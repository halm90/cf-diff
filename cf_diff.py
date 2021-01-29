"""
cf-diff tool main

Note(s):
    1. Requires Python 3
"""
from sortedcontainers import SortedDict

from logger import Logger
from parameters import SysParams
from cc_fetcher import CCFetcher
from statsdb import StatsDB


def get_counts(foundation, cc_obj, db_obj):
    """
    Fetch the app count from the Cloud Controller and from the
    database, and reply with these counts and the difference.
    """
    cf_count = cc_obj.app_count(foundation)
    if not cf_count:
        Logger().logger.debug("No count for foundation %s", foundation)

    query_sql = "SELECT COUNT(DISTINCT GUID) FROM applications"
    db_count = db_obj.query(query_sql).fetchall()[0][0]
    return cf_count, db_count


def main():
    """
    Wrap up main functionality
    """
    foundation = SysParams()['FOUNDATION']
    cc_fetcher = CCFetcher()
    db_obj = StatsDB()
    cf_count, db_count = get_counts(foundation, cc_fetcher, db_obj)
    Logger().logger.info("[Foundation %s] CloudController: %s, Database: %s",
                         foundation, cf_count, db_count)


if __name__ == "__main__":
    Logger().logger.debug("Main starting")
    main()
