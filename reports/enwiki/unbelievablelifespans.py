# Public domain; MZMcBride, Tim Landscheidt; 2012, 2013

"""
Report class for unbelievable life spans
"""

import datetime

import reports

class report(reports.report):
    def get_title(self):
        return 'Unbelievable life spans'

    def get_preamble_template(self):
        return 'Unbelievable life spans; data as of <onlyinclude>%s</onlyinclude>.'

    def get_table_columns(self):
        return ['Page', 'Birth year', 'Death year', 'Life span']

    def get_table_rows(self, conn):
        currentyear = int(datetime.datetime.utcnow().strftime('%Y'))

        cursor = conn.cursor()
        for birthyear in range(1, currentyear + 1):
            cursor.execute('''
            SELECT page_namespace, ns_name, page_title, deathyear
            FROM (SELECT
                page_namespace,
                CONVERT(ns_name USING utf8) AS ns_name,
                CONVERT(page_title USING utf8) AS page_title,
                CAST(SUBSTRING_INDEX(cl3.cl_to, '_', 1) AS UNSIGNED) AS deathyear
              FROM categorylinks AS cl1
              LEFT JOIN categorylinks AS cl2
              ON cl1.cl_from = cl2.cl_from
              AND cl2.cl_to IN ('Longevity_traditions', 'Longevity_claims')
              JOIN categorylinks AS cl3
              ON cl1.cl_from = cl3.cl_from
              AND cl3.cl_to REGEXP '^[0-9]+_deaths$'
              JOIN page
              ON page_id = cl1.cl_from
              JOIN toolserver.namespace
              ON page_namespace = ns_id AND dbname = CONCAT(?, '_p')
              WHERE cl1.cl_to = CONCAT(?, '_births')
              AND cl2.cl_from IS NULL) AS BornAndDeads
            WHERE ? > deathyear
            OR deathyear - ? > 122;
            ''', (self.site, birthyear, birthyear, birthyear))
            for page_namespace, ns_name, page_title, deathyear in cursor:
                if page_namespace in (6, 14):
                    full_page_title = u'[[:'+ns_name+u':'+page_title+u']]'
                elif page_namespace == 0:
                    full_page_title = u'[['+page_title+u']]'
                else:
                    full_page_title = u'[['+ns_name+u':'+page_title+u']]'
                yield [full_page_title, str(birthyear), str(deathyear), str(deathyear - birthyear)]

        cursor.close()
