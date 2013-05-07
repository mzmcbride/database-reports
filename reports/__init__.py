"""
report: Base class for all reports
"""

import time

class report:
    """Base class for all reports"""
    def __init__(self, wiki, site, dumpdate, userdb):
        """Initialize report object."""
        self.wiki = wiki
        self.site = site
        self.dumpdate = dumpdate
        self.userdb = userdb

    def needs_commons_db(self):
        """Return whether the report needs the commons database."""
        return False

    def needs_user_db(self):
        """Return whether the report needs the user database."""
        return False

    def rows_per_page(self):
        """Return number of rows per page or None if single-page report."""
        return None

    def get_title(self):
        """Get title."""
        raise NotImplementedError("Please implement this method")

    def get_preamble(self, conn):
        """Get preamble."""
        cursor = conn.cursor()
        cursor.execute('SELECT UNIX_TIMESTAMP(MAX(rc_timestamp)) FROM recentchanges;')
        current_of = time.strftime('%H:%M, %d %B %Y (UTC)', time.gmtime(cursor.fetchone() [0]))
        cursor.close()

        return self.get_preamble_template() % current_of

    def get_preamble_template(self):
        """Get preamble template."""
        raise NotImplementedError("Please implement this method")

    def get_table_columns(self):
        """Get a list of table columns."""
        raise NotImplementedError("Please implement this method")

    def get_table_rows(self, conn):
        """Get a table row as a list."""
        raise NotImplementedError("Please implement this method")
