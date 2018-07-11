import base64
import kubernetes
import psycopg2

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pykubeop import KubernetesOperator, CRDBase


DB_CREDENTIALS_SECRET = 'postgres-database-credentials'


class PostgresDatabase(CRDBase):
    GROUP = "postgres.example.com"
    VERSION = "v1alpha1"
    PLURAL = "postgresdatabases"
    SINGULAR = "postgresdatabase"
    KIND = "PostgresDatabase"

    def _decode_secret_data(self, data):
        return dict(
            [
                (key: base64.b64decode(val).decode('utf-8'))
                for key, val in data.items()
            ]
        )

    def _get_credentials_from_secret(self):
        # Connect to the V1 API re-using the CRD clients version of api_client
        api_client = self.crd_client.api_client
        v1 = kubernetes.client.CoreV1Api(api_client)

        # Fetch the Database Credentials from a Secret
        secret = v1.read_namespaced_secret(DB_CREDENTIALS_SECRET, self.metadata['namespace'])
        return s = self._decode_secret_data(secret.data)

    def _get_db_connection(self):
        credentials = self._get_credentials_from_secret()
        con = psycopg2.connect(
            host=credentials['dbHost'],
            user=credentials['dbUser'],
            password=credentials['dbPassword']
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return con

    def ensure_created(self):
        con = self._get_db_connection()
        cur = con.cursor()

        try:
            cur.execute('CREATE DATABASE {};'.format(self.spec['dbName']))
            self.status = {'state': 'created'}
        except Exception as e:
            self.status = {'state': 'error', 'error': str(e)}

    def ensure_modified(self):
        # modified logic goes here
        pass

    def ensure_deleted(self):
        con = self._get_db_connection()
        cur = con.cursor()
        cur.execute('DROP DATABASE {};'.format(self.spec['dbName'])


if __name__ == "__main__":
    KubernetesOperator(PostgresDatabase).run()
