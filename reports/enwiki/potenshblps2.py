# Public domain; bjweeks, MZMcBride, Tim Landscheidt; 2012, 2013

"""
Report class for potential biographies of living people (2)
"""

import datetime

import reports

class report(reports.report):
    def get_title(self):
        return 'Potential biographies of living people (2)'

    def get_preamble_template(self):
        return u'''Articles that are in a "XXXX births" category (greater than 1899) that are \
not in [[:Category:Living people]], [[:Category:Possibly living people]], \
or a "XXXX deaths" category (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Biography', 'Birth year']

    def get_table_rows(self, conn):
        excluded_categories = []

        current_year = int(datetime.datetime.utcnow().strftime('%Y'))

        cursor = conn.cursor()
        for year in range(current_year, 1899, -1):
            cursor.execute('''
            /* potenshblps2.py SLOW_OK */
            SELECT
              CONVERT(page_title USING utf8)
            FROM page
            JOIN categorylinks AS c1
            ON c1.cl_from = page_id
            AND c1.cl_to = CONCAT(?, '_births')
            LEFT JOIN categorylinks AS c2
            ON c2.cl_from = page_id
            AND (c2.cl_to IN ('Living_people',
                              'Possibly_living_people',
                              'Disappeared_people',
                              'Missing_people',
                              'Year_of_death_unknown',
                              'Date_of_death_unknown',
                              'Year_of_death_missing',
                              'Date_of_death_missing',
                              '20th-century_deaths',
                              '21st-century_deaths',
                              '1900s_deaths',
                              '2000s_deaths',
                              'People_declared_dead_in_absentia')
                 OR c2.cl_to REGEXP '^[0-9]{4}_deaths$'
                 OR c2.cl_to REGEXP '^[0-9]{3}0s_deaths$')
            WHERE page_namespace = 0
            AND page_is_redirect = 0
            AND c2.cl_from IS NULL
            ORDER BY 1;
            ''', (year, ))
            for (page_title, ) in cursor:
                yield [u'[[%s]]' % page_title, str(year)]

        cursor.close()
