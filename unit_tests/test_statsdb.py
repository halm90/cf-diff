"""
Unit tests for the cf-diff tool statsdb module
"""
import logging
import os
import pytest
import unittest

from mock import call, patch, MagicMock
from testfixtures import LogCapture

import statsdb

#pylint: disable=protected-access, invalid-name


class TestStatsDB(unittest.TestCase):
    """
    Test basic operation of the StatsDB class.
    """
    _env_dict = {'CC_URL': 'a/b/{foundation}/d',
                 'FOUNDATION': 'foundation',
                 'LOG_LEVEL': 'DEBUG',
                 'OAUTH_CLIENT_ID': 'client_id',
                 'OAUTH_CLIENT_SECRET': 'shhhh',
                 'OAUTH_URL': 'e/f/{foundation}/g',
                 'MYSQL_USER': 'mysqlUser',
                 'MYSQL_PASSWORD': 'mysqlPassword',
                 'MYSQL_HOST': 'mysqlHost',
                 'MYSQL_CF_DATABASE': 'mysqlDB',
                }
    def setUp(self):
        """
        Test setups: patch out functions across all tests.
        """
        patch.dict(os.environ, self._env_dict).start()

    def tearDown(self):
        """
        Test teardowns: clean up test-wide patches.
        """
        patch.stopall()

    def testMakeIndices(self):
        """
        test the _make_table_indices function
        """
        index_list = [('someName', 'someTable', 'someColumn'),
                      ('anotherName', 'anotherTable', 'anotherColumn')]
        with patch("statsdb.StatsDB.__init__", return_value=None), \
             patch("statsdb.StatsDB.query") as mock_query:
            stats_obj = statsdb.StatsDB()
            stats_obj.logger = MagicMock()
            stats_obj._make_table_indices(index_list)

        queries = [call("CREATE OR REPLACE INDEX {} ON {}({})".format(n,t,c))
                   for n, t, c in index_list]
        mock_query.assert_has_calls(queries)

    def testConnect(self):
        """
        test the _connect function
        """
        with patch("statsdb.StatsDB.__init__", return_value=None), \
             patch("mysql.connector.connect") as mock_connect:
            stats_obj = statsdb.StatsDB()
            stats_obj.logger = MagicMock()
            stats_obj._conn = MagicMock()
            stats_obj._user = "a User"
            stats_obj._password = "a password"
            stats_obj._host = "a host"
            stats_obj._database = "a database"
            stats_obj._buffered = False
            stats_obj._autocommit = False

            stats_obj._connect()

        mock_connect.assert_called_once_with(user=stats_obj._user,
                                             password=stats_obj._password,
                                             host=stats_obj._host,
                                             database=stats_obj._database)
        stats_obj._conn.cursor.assert_called_once_with(buffered=stats_obj._buffered)

    def testConnectClose(self):
        """
        test the _connect function
        """
        class Err(Exception):
            """
            Some dummy exception
            """

        with patch("statsdb.StatsDB.__init__", return_value=None), \
             pytest.raises(Err), \
             patch("mysql.connector.connect", side_effect=Err) as mock_connect:
            stats_obj = statsdb.StatsDB()
            stats_obj.logger = MagicMock()
            stats_obj._conn = MagicMock()
            stats_obj._user = "a User"
            stats_obj._password = "a password"
            stats_obj._host = "a host"
            stats_obj._database = "a database"
            stats_obj._buffered = False
            stats_obj._autocommit = False

            stats_obj._connect()

        mock_connect.assert_called_once_with(user=stats_obj._user,
                                             password=stats_obj._password,
                                             host=stats_obj._host,
                                             database=stats_obj._database)
        self.assertEqual(stats_obj._conn, None)

    def testConnectQuery(self):
        """
        test the query function
        """
        test_sql = "SELECT foo FROM bar"
        with patch("statsdb.StatsDB.__init__", return_value=None), \
             patch("mysql.connector.connect") as mock_connect:
            stats_obj = statsdb.StatsDB()
            stats_obj.logger = MagicMock()
            stats_obj._conn = MagicMock()
            stats_obj._connect = MagicMock()
            mock_cursor = MagicMock()
            stats_obj._cursor = mock_cursor

            stats_obj.query(test_sql)

        mock_cursor.execute.assert_called_once_with(test_sql)
        stats_obj._conn.close.assert_called_once

    def testConnectQueryDict(self):
        """
        test the query_dict function
        """
        test_sql = "SELECT foo FROM bar"
        col = ["col1", "col2", "col3", "col4"]
        with patch("statsdb.StatsDB.__init__", return_value=None), \
             patch("statsdb.StatsDB.row_to_dict") as mock_rtd, \
             patch("statsdb.StatsDB.query", return_value=[("some_row")]) as mock_query:

            stats_obj = statsdb.StatsDB()
            stats_obj.logger = MagicMock()
            rtn = stats_obj.query_dict(test_sql, col)

        mock_query.assert_called_once_with(test_sql)
        mock_rtd.asset_called_once_with("some_row", col)

    def testSelect(self):
        """
        test the query_dict function
        """
        tname = "table_name"
        drtn = "dict_return"
        class DummyTable():
            name = tname

        fields = ["field1", "field2"]
        where = "somewhere"

        with patch("statsdb.StatsDB.__init__", return_value=None), \
             patch("statsdb.StatsDB.query_dict",
                   return_value=drtn) as mock_dict:

            stats_obj = statsdb.StatsDB()
            stats_obj.logger = MagicMock()
            rtn = stats_obj.select(DummyTable(), fields, where)

        sql = "SELECT {} FROM {} WHERE {}".format(','.join(fields), tname, where)
        mock_dict.assert_called_once_with(sql, fields)
        self.assertEqual(rtn, drtn)

    def testSelect(self):
        """
        test the query_dict function
        """
        tname = "table_name"
        qrtn = "query_return"
        class DummyTable():
            name = tname

        fields = ["field1", "field2"]
        where = "somewhere"

        with patch("statsdb.StatsDB.__init__", return_value=None), \
             patch("statsdb.StatsDB.query",
                   return_value=qrtn) as mock_query:

            stats_obj = statsdb.StatsDB()
            stats_obj.logger = MagicMock()
            rtn = stats_obj.select(DummyTable(), fields, where, as_dict=False)

        sql = "SELECT {} FROM {} WHERE {}".format(','.join(fields), tname, where)
        mock_query.assert_called_once_with(sql)
        self.assertEqual(rtn, qrtn)


class TestStatsStatic(unittest.TestCase):
    """
    Test StatsDB static function(s)
    """
    def testRowToDict(self):
        """
        Test row-to-dict (normal operation)
        """
        col = ["key1", "key2", "key3", "key4"]
        row = ["val1", "val2", "val3", "val4"]
        rtn = statsdb.StatsDB.row_to_dict(row, col)
        desired = {"key1": "val1",
                   "key2": "val2",
                   "key3": "val3",
                   "key4": "val4"}
        self.assertEqual(rtn, desired)

    def testRowToDictErr(self):
        """
        Test row-to-dict (error case)
        """
        col = ["key1", "key2", "key3", "key4"]
        row = ["val1", "val2", "val3"]
        rtn = statsdb.StatsDB.row_to_dict(row, col)
        self.assertEqual(rtn, {})
