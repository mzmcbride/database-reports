"""
report: Base class for all reports
"""

import locale
import os
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
        timestamp = cursor.fetchone() [0]
        if self.site == 'plwiki':
            old_TZ = os.environ.get('TZ')
            locale.setlocale(locale.LC_ALL, 'pl_PL.utf8')
            os.environ['TZ'] = ':Europe/Warsaw'
            current_of = time.strftime('%d %B %Y, %H:%M', time.localtime(timestamp))
            locale.setlocale(locale.LC_ALL, 'C')
            if old_TZ == None:
                del os.environ['TZ']
            else:
                os.environ['TZ'] = old_TZ
        else:
            current_of = time.strftime('%H:%M, %d %B %Y (UTC)', time.gmtime(timestamp))
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

    def get_footer(self):
        """Get footer."""
        return None

    def get_all_categories_beneath(self, cursor, cat):
        queried_cats = {}

        def process_category(cat):
            queried_cats [cat] = True
            cursor.execute('''
                           SELECT
                             CONVERT(page_title USING utf8)
                           FROM page
                           JOIN categorylinks
                           ON cl_from = page_id
                           WHERE cl_to = CONVERT(? USING utf8)
                           AND page_namespace = 14;
                           ''', (cat, ))
            results = cursor.fetchall()
            for subcatrow in results:
                if not subcatrow[0] in queried_cats:
                    process_category (subcatrow[0])

        process_category(cat)

        return queried_cats.keys()
