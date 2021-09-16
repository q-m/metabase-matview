import re
import requests
from datetime import datetime

MAGIC_HEADER = '-- converted to materialized view using metabase_matview'

class Metabase:
    def __init__(self, url, email=None, password=None, session_id=None, schema='metabase_matview'):
        self.url = url.rstrip('/')
        self.email = email
        self.password = password
        self.session_id = session_id
        self.schema = schema

    def login(self):
        res = requests.post(self.url + '/api/session', json={
            'username': self.email,
            'password': self.password,
        })
        if not res.ok:
            raise Exception(res)

        self.session_id = res.json()['id']

    def check_session(self):
        if self.session_id:
            res = requests.get(self.url + '/api/user/current', headers=self._headers())
            if res.ok:
                return
            if res.status_code != 401:
                raise Exception(res)

        return self.login()

    def get(self, endpoint, raw=False, login=True, **kwargs):
        if not self.session_id:
            self.login()
        res = requests.get(self.url + endpoint, **kwargs, headers=self._headers())
        if res.status_code == 401 and login:
            self.login()
            return self.get(endpoint, **kwargs, raw=raw, login=False)
        elif raw:
            return res
        elif res.ok:
            return res.json()
        else:
            return False

    def post(self, endpoint, raw=False, login=True, **kwargs):
        if not self.session_id:
            self.login()
        res = requests.post(self.url + endpoint, **kwargs, headers=self._headers())
        if res.status_code == 401 and login:
            self.login()
            return self.post(endpoint, **kwargs, raw=raw, login=False)
        elif raw:
            return res
        elif res.ok:
            return res.json()
        else:
            return False

    def put(self, endpoint, raw=False, login=True, **kwargs):
        if not self.session_id:
            self.login()
        res = requests.put(self.url + endpoint, **kwargs, headers=self._headers())
        if res.status_code == 401 and login:
            self.login()
            return self.put(endpoint, **kwargs, raw=raw, login=False)
        elif raw:
            return res
        elif res.ok:
            return res.json()
        else:
            return False

    def get_card(self, id):
        res = self.get('/api/card/%d' % id)
        return MetabaseCard(self, res)

    def get_native_query(self, query):
        res = self.post('/api/dataset/native', json=query)
        return res['query']

    def get_databases(self):
        res = self.get('/api/database')
        return [MetabaseDatabase(self, db) for db in res['data']]

    def _headers(self):
        return {
            'X-Metabase-Session': self.session_id,
        }

class MetabaseCard:
    def __init__(self, metabase, data):
        self.metabase = metabase
        self.data = data

    @property
    def id(self):
        return self.data['id']

    @property
    def name(self):
        return self.data['name']

    @property
    def database_id(self):
        return self.data['database_id']

    @property
    def updated_at(self):
        return datetime.strptime(self.data['updated_at'], '%Y-%m-%dT%H:%M:%S.%fZ')

    @property
    def query_type(self):
        return self.data['query_type']

    @property
    def dataset_query(self):
        return self.data['dataset_query']

    @property
    def view_name(self):
        return '"%s"."question_%i"' % (self.metabase.schema, self.id)

    @property
    def is_materialized(self):
        if self.query_type == 'native':
            query = self.data['dataset_query']['native']['query']
            return query.startswith(MAGIC_HEADER)
        else:
            # only native queries can be materialized
            return False

    def get_native_query(self):
        return self.metabase.get_native_query(self.data['dataset_query'])

    def materialize(self) -> bool:
        if self.is_materialized:
            return False
        elif self.query_type == 'native':
            query = self.data['dataset_query']['native']['query']
            query = '\n'.join([
                '%s - only edit the ORIGINAL QUERY please' % MAGIC_HEADER,
                'WITH original_query AS (\n-- ORIGINAL QUERY - EDIT BELOW\n\n%s\n\n-- END OF ORIGINAL QUERY - EDIT ABOVE\n)' % query,
                'SELECT * FROM %s' % self.view_name
            ])
            self.data['dataset_query']['native']['query'] = query
            return True
        else:
            raise Exception('Only native queries supported')

    def unmaterialize(self) -> bool:
        if not self.is_materialized:
            return False
        elif self.query_type == 'native':
            query = self.data['dataset_query']['native']['query']
            query = re.sub(r'\A.*^--\s*ORIGINAL QUERY - EDIT BELOW\s*(.*)\s*^--\s*END OF ORIGINAL QUERY.*\Z', '\\1', query, flags=re.MULTILINE|re.DOTALL).strip()
            self.data['dataset_query']['native']['query'] = query
            return True
        else:
            raise Exception('Only native queries supported')

    def save(self):
        self.metabase.put('/api/card/%d' % self.id, json=self.data)

class MetabaseDatabase:
    def __init__(self, metabase, data):
        self.metabase = metabase
        self.data = data

    @property
    def id(self):
        return self.data['id']

    @property
    def name(self):
        return self.data['name']

    @property
    def engine(self):
        return self.data['engine']

    @property
    def features(self):
        return self.data['features']