"""
cf_diff DB objects

Note(s):
    1. Requires Python 3
"""
import json
import os
import mysql.connector

from logger import Logger
from parameters import SysParams


class StatsDB(object):
    """
    Generic PCF database object.
    """
    # table index tuple: index name, table name, column name
    _table_indices = []
    def __init__(self):
        """
        """
        mysql_env = {'user': ('username', 'MYSQL_USER'),
                     'password': ('password', 'MYSQL_PASSWORD'),
                     'host': ('hostname', 'MYSQL_HOST'),
                     'database': ('name', 'MYSQL_CF_DATABASE')}

        self.logger = Logger().logger
        self.params = SysParams()
        self.logger.debug("Initializing StatsDB")

        missing = []
        msql_creds = {}
        vcap = os.environ.get('VCAP_SERVICES')
        if vcap:
            # If the VCAP environment variable is set then fetch
            # mysql credentials from there
            vcap_creds = json.loads(vcap)['p-mysql'][0]['credentials']
            for kw_key, (vc_key, _) in mysql_env.items():
                try:
                    msql_creds[kw_key] = vcap_creds[vc_key]
                except KeyError:
                    missing.append(vc_key)
        else:
            for param, (_, env_key) in mysql_env.items():
                try:
                    msql_creds[param] = msql_creds.get(param) or os.environ[env_key]
                except KeyError:
                    missing.append(env_key)

        if missing:
            self.logger.error("Missing parameter(s): %s", ', '.join(missing))
            exit(1)

        self._user = msql_creds['user']
        self._password = msql_creds['password']
        self._host = msql_creds['host']
        self._database = msql_creds['database']
        self._autocommit = msql_creds.get('autocommit', False)
        self._buffered = msql_creds.get('buffered', True)
        self._conn = None
        self._connect()
        self._cursor = None
        self._make_table_indices(self._table_indices)

        super().__init__()

    def end(self):
        """
        Terminate the DB connection
        """
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        """
        Context manager enter/constructor
        """
        self.logger.debug("DB object context enter")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """
        Context manager exit/destructor
        """
        self.logger.debug("DB object context exit")
        self.end()

    def _make_table_indices(self, index_list):
        """
        Create table indices.

        :param index_list: list of index tuples (index_name, table_name, column)
        """
        self.logger.debug('Creating %d table indices', len(index_list))
        index_sql = 'CREATE OR REPLACE INDEX {} ON {}({})'
        for (index_name, table_name, column) in index_list:
            sql = index_sql.format(index_name, table_name, column)
            self.logger.debug('Index: %s', sql)
            self.query(sql)

    def _connect(self):
        """
        Create the connection to the database server

        """
        self.logger.debug("Make DB connection")
        if self._conn:
            self._conn.close()
        try:
            self._conn = mysql.connector.connect(user=self._user,
                                                 password=self._password,
                                                 host=self._host,
                                                 database=self._database)
            self._cursor = self._conn.cursor(buffered=self._buffered)
            self._conn.autocommit = self._autocommit
        except:
            msg = "Failed to create MySQL connection"
            self.logger.error(msg)
            self.logger.debug("%s (user: %s, pwd: %s, host: %s, db: %s)",
                              msg, self._user, self._password, self._host,
                              self._database)
            self._conn = None
            raise

    @staticmethod
    def row_to_dict(row, column_list):
        """
        Convert a query result row (tuple) into a dict.

        :param row: cursor row
        :param column_list: column name mapping
        :return: dict
        """
        Logger().logger.debug("Convert query row to dict")

        if len(row) != len(column_list):
            Logger().logger.warning("WARNING: query row %d items, %d expected",
                                    len(row), len(column_list))
            rtn = {}
        else:
            rtn = dict(zip(column_list, row))
        Logger().logger.debug("row_to_dict returning dict length %d", len(rtn))
        return rtn

    def query(self, sql):
        """
        Set the cursor and run the query.

        If the connection is closed (timed out) then reconnect and try again.

        :param sql: the SQL query string
        :return: cursor object resulting from query
        """
        self.logger.debug("Run SQL query: %s", sql)
        self._connect()
        try:
            self.logger.debug("Execute SQL")
            self._cursor.execute(sql)
        except:
            self.logger.warning("mySQL query failed: %s", sql)
            raise
        self._conn.close()
        return self._cursor

    def query_dict(self, sql, column_list):
        """
        Execute an SQL query, then return a list of dicts where each list
        entry is a row returned from the query, converted to a dict.  In
        order to convert rows to dicts a column list must be provided.

        :param sql: the SQL query string
        :param column_list: list of columns used to map the row->dictionary
        :return: list of dicts
        """
        self.logger.debug("Run SQL query, return dict: %s", sql)
        rtn = [self.row_to_dict(row, column_list) for row in self.query(sql)]
        return rtn

    def select(self, table, fields=None, where=None, as_dict=True):
        """
        Wrap up a simple generic select.

        :param table: table object to query
        :param fields: list of fields to query for ("select X")
        :param where: match conditions ("where ...")
        :param as_dict: return dict if true else return cursor

        :return: dict or cursor result from query
        """
        fields = [fields] if (fields and isinstance(fields, str)) else fields
        where = [where] if (where and isinstance(where, str)) else where
        columns = fields if (fields and fields != '*') else table.columns

        itemspec = '{}'.format(','.join(fields)) if fields else '*'
        self.logger.debug("%s table query for items: <%s>",
                          table.name, itemspec)
        sql = "SELECT {} FROM {}".format(itemspec, table.name)

        if where:
            self.logger.debug("%s table query for match: <%s>",
                              table.name, where)
            sql += " WHERE {}".format(' AND '.join(where))

        if as_dict:
            retn = self.query_dict(sql, columns)
        else:
            retn = self.query(sql)
        return retn
