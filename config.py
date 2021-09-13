import os

def get_database_urls():
    database_urls = {}

    for key in os.environ.keys():
        if not key.startswith('DATABASE_URL_'): continue
        try:
            id = int(key[13:])
            database_urls[id] = os.getenv(key)
        except ValueError:
            pass

    return database_urls

WEB_PATH = os.getenv('WEB_PATH', '/')
SCHEMA = os.getenv('METABASE_MATVIEW_SCHEMA', 'metabase_matview')
METABASE_URL = os.getenv('METABASE_URL')
DATABASE_URLS = get_database_urls()
