"""
Unit tests for the cf-diff tool cf_diff module
"""
from mock import patch, MagicMock
from testfixtures import LogCapture
import logging
import os
import unittest

import cf_diff
import statsdb

#pylint: disable=protected-access, invalid-name

class TestCFDiff(unittest.TestCase):
    """
    Test basic operation of the main module.
    """
    _test_env = {'OAUTH_CLIENT_ID': 'id',
                 'OAUTH_CLIENT_SECRET': 'shhh',
                 'OAUTH_URL': 'a/b/c/d',
                 'FOUNDATION': 'foundation',
                 'CC_URL': 'e/f/g/h'}
    def setUp(self):
        """
        Test setups: patch out functions across all tests.
        """
        patch.dict(os.environ, self._test_env).start()

    def tearDown(self):
        """
        Test teardowns: clean up test-wide patches.
        """
        patch.stopall()

    def testMain(self):
        """
        """
        with patch("cc_fetcher.CCFetcher.__init__", return_value=None) as mock_fetcher, \
             patch("statsdb.StatsDB.__init__", return_value=None) as mock_stats, \
             patch("cf_diff.get_counts", return_value=(1, 2)) as mock_counts, \
             LogCapture(level=logging.INFO) as log_info:
            cf_diff.main()
        mock_counts.assert_called_once()
        log_info.check(('logger', 'INFO',
                        '[Foundation foundation] CloudController: 1, Database: 2'))

    def testGetCounts(self):
        """
        """
        db_value = 4242
        class fakeFetch():
            @staticmethod
            def fetchall():
                return ((db_value,),)
        with patch("cc_fetcher.CCFetcher") as mock_fetcher, \
             patch.object(statsdb, "StatsDB") as mock_stats, \
             LogCapture(level=logging.INFO) as log_info:

            mock_fetcher.app_count = MagicMock(return_value=42)
            mock_fetchall = MagicMock(return_value=((4242,),))
            mock_stats.query.return_value = fakeFetch()
            cf, db = cf_diff.get_counts('FoundationName',
                                        mock_fetcher, mock_stats)

        sql = 'SELECT COUNT(DISTINCT GUID) FROM applications'
        mock_stats.query.assert_called_once_with(sql)
        self.assertEqual(db, db_value)
