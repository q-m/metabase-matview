import os
from datetime import datetime, timezone
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy

schema = os.getenv('METABASE_MATVIEW_SCHEMA', 'metabase_matview')

db = SQLAlchemy(metadata=MetaData(schema=schema))

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    starred = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    card_refreshed_at = db.Column(db.DateTime)
    view_refreshed_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Card id=%i>' % self.id

    @property
    def view_name(self):
        return '"%s"."question_%i"' % (self.metadata.schema, self.id)

    def as_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'starred': self.starred,
            'created_at': self.created_at,
            'card_refreshed_at': self.card_refreshed_at,
            'view_refreshed_at': self.view_refreshed_at
        }

    def create_view(self, sql: str):
        db.session.execute('CREATE MATERIALIZED VIEW %s AS %s WITH NO DATA' % (self.view_name, sql))
        self.card_refreshed_at = datetime.now(timezone.utc)

    def update_view(self, sql: str):
        # TODO recreate dependents too ... (!)
        self.destroy_view()
        self.create_view(sql)
        self.card_refreshed_at = datetime.now(timezone.utc)

    def destroy_view(self):
        db.session.execute('DROP MATERIALIZED VIEW %s' % self.view_name)

    def refresh_view(self):
        db.session.execute('REFRESH MATERIALIZED VIEW %s' % self.view_name)
        self.view_refreshed_at = datetime.now(timezone.utc)

def init_db(app):
    db.app = app
    db.init_app(app)
    db.session.execute('CREATE SCHEMA IF NOT EXISTS %s' % schema)
    db.session.commit()
    db.create_all()
    return db

