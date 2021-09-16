#!/usr/bin/env python3
import os
from flask import Flask, jsonify, request, render_template

from database import init_db, Card
from metabase import Metabase
from config import SCHEMA, WEB_PATH, METABASE_URL, DATABASE_URLS

app = Flask(__name__, static_url_path=WEB_PATH+'static')

# TODO move part of mb() to config
_mb = None  # Metabase instance when configured from the environment


def mb():
    """Return a Metabase instance"""
    global _mb
    if _mb:
        return _mb

    # try to get from session (assuming same domain as Metabase to share cookie)
    session_id = request.cookies.get('metabase.SESSION')
    if session_id:
        return Metabase(METABASE_URL, session_id=session_id, schema=SCHEMA)

    # then try session from environment
    session_id = os.getenv('METABASE_SESSION_ID')
    if session_id:
        _mb = Metabase(METABASE_URL, session_id=session_id, schema=SCHEMA)
        return _mb

    # then try login from environment
    email = os.getenv('METABASE_EMAIL')
    password = os.getenv('METABASE_PASSWORD')
    if email and password:
        _mb = Metabase(METABASE_URL, email=email,
                       password=password, schema=SCHEMA)
        return _mb

    raise Exception("Missing Metabase session/login info.")


def get_db(database_id):
    database_url = DATABASE_URLS.get(database_id)
    if not database_url:
        raise Exception("Database not configured for use in this app.")
    return init_db(app, database_id, database_url)


def check_session():
    """Raises an exception when there is no valid Metabase session"""
    mb().check_session()


@app.route(WEB_PATH)
def main():
    return render_template('index.html', metabase_url=METABASE_URL, web_path=WEB_PATH)


@app.route(WEB_PATH+'api/1/databases')
def api_1_databases():
    check_session()
    mb_dbs = mb().get_databases()
    mb_dbs = [db for db in mb_dbs if db.id in DATABASE_URLS.keys()]
    mb_dbs = [{'id': db.id, 'name': db.name, 'engine': db.engine}
              for db in mb_dbs]
    return jsonify(mb_dbs)

@app.route(WEB_PATH+'api/1/database/<int:db_id>/cards')
def api_1_cards(db_id):
    check_session()
    db = get_db(db_id)
    return jsonify([c.as_json() for c in Card.query.all()])


@app.route(WEB_PATH+'api/1/database/<int:db_id>/card/<int:card_id>')
def api_1_card(db_id, card_id):
    check_session()
    db = get_db(db_id)
    return jsonify(Card.query.get(card_id).as_json())


@app.route(WEB_PATH+'api/1/card/<int:card_id>', methods=['POST'])
def api_1_card_create(card_id):
    check_session()
    mb_card = mb().get_card(card_id)
    db = get_db(mb_card.database_id)
    db_card = Card(id=card_id, name=mb_card.name)

    db.session.add(db_card)
    mb_card.unmaterialize()  # in case the query was materialized but not in the database
    db_card.create_view(mb_card.get_native_query())
    mb_card.materialize()
    mb_card.save()
    db.session.commit()

    db_card.refresh_view()
    db.session.commit()

    return jsonify(db_card.as_json())


@app.route(WEB_PATH+'api/1/card/<int:card_id>', methods=['DELETE'])
def api_1_card_destroy(card_id):
    check_session()
    mb_card = mb().get_card(card_id)
    db = get_db(mb_card.database_id)
    db_card = Card.query.get(card_id)

    db_card.destroy_view()
    mb_card.unmaterialize()
    mb_card.save()
    db.session.delete(db_card)

    db.session.commit()
    return jsonify({})  # TODO proper status


@app.route(WEB_PATH+'api/1/card/<int:card_id>/refresh', methods=['POST'])
def api_1_card_refresh(card_id):
    check_session()
    mb_card = mb().get_card(card_id)
    db = get_db(mb_card.database_id)
    db_card = Card.query.get(card_id)

    if mb_card.updated_at > db_card.card_refreshed_at:
        mb_card.unmaterialize()
        db_card.update_view(mb_card.get_native_query())
    db_card.refresh_view()

    db.session.commit()
    return jsonify(db_card.as_json())


if __name__ == '__main__':
    app.run()
