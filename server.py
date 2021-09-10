#!/usr/bin/env python3
import os
from flask import Flask, jsonify, request, render_template

from database import schema, init_db, Card
from metabase import Metabase

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = init_db(app)

WEB_PATH = os.getenv('WEB_PATH', '/')
METABASE_URL = os.getenv('METABASE_URL')
METABASE_DATABASE_ID = int(os.getenv('METABASE_DATABASE_ID', -1))

_mb = None # Metabase instance when configured from the environment

def mb():
    """Return a Metabase instance"""
    global _mb
    if _mb: return _mb

    # try to get from session (assuming same domain as Metabase to share cookie)
    session_id = request.cookies.get('metabase.SESSION')
    if session_id:
        return Metabase(METABASE_URL, session_id=session_id, schema=schema)

    # then try session from environment
    session_id = os.getenv('METABASE_SESSION_ID')
    if session_id:
        _mb = Metabase(METABASE_URL, session_id=session_id, schema=schema)
        return _mb

    # then try login from environment
    email = os.getenv('METABASE_EMAIL')
    password = os.getenv('METABASE_PASSWORD')
    if email and password:
        _mb = Metabase(METABASE_URL, email=email, password=password, schema=schema)
        return _mb

    raise Exception("Missing Metabase session/login info.")

@app.route('/')
def main():
    return render_template('index.html', metabase_url=METABASE_URL, web_path=WEB_PATH)

@app.route('/api/1/cards')
def api_1_cards():
    return jsonify([c.as_json() for c in Card.query.all()])

@app.route('/api/1/card/<int:id>')
def api_1_card(id):
    return jsonify(Card.query.get(id).as_json())

@app.route('/api/1/card/<int:id>', methods=['POST'])
def api_1_card_create(id):
    mb_card = mb().get_card(id)
    if mb_card.database_id != METABASE_DATABASE_ID:
        raise Exception("Can only work with questions using database %d" % METABASE_DATABASE_ID)
    db_card = Card(id=id, name=mb_card.name)

    db.session.add(db_card)
    db_card.create_view(mb_card.query_orig)
    mb_card.update_query(mb_card.query_materialized)
    db.session.commit()

    db_card.refresh_view()
    db.session.commit()

    return jsonify(db_card.as_json())

@app.route('/api/1/card/<int:id>', methods=['DELETE'])
def api_1_card_destroy(id):
    db_card = Card.query.get(id)
    mb_card = mb().get_card(id)

    mb_card.update_query(mb_card.query_orig)
    db_card.destroy_view()
    db.session.delete(db_card)

    db.session.commit()
    return jsonify({}) # TODO proper status

@app.route('/api/1/card/<int:id>/refresh', methods=['POST'])
def api_1_card_refresh(id):
    mb_card = mb().get_card(id)
    db_card = Card.query.get(id)

    if mb_card.updated_at > db_card.card_refreshed_at:
        db_card.update_view(mb_card.query_orig)
    db_card.refresh_view()

    db.session.commit()
    return jsonify(db_card.as_json()) # TODO proper status


if __name__ == '__main__':
    app.run()
