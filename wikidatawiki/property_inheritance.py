#!/usr/bin/env python
"""
Copyright (C) 2013 Legoktm

Licensed as CC-Zero. See https://creativecommons.org/publicdomain/zero/1.0 for more details.

Finds items which have one property (like country),
but don't have another (like continent).

"""

import os
import ConfigParser
import wikitools
import oursql
import datetime

query = """
SELECT
  page_title
FROM pagelinks
JOIN page
ON page_id=pl_from
WHERE pl_namespace=120
AND page_namespace=0
AND pl_title=?
AND page_title NOT IN (
  SELECT
    page_title
  FROM pagelinks
  JOIN page
  ON page_id=pl_from
  WHERE pl_namespace=120
  AND pl_title=?
  AND page_namespace=0
)
LIMIT 100;
"""

label_query = """
SELECT
term_text
FROM wb_terms
WHERE term_entity_id=?
AND term_entity_type="property"
AND term_language="en"
AND term_type="label"
"""
base = 'Wikidata:Database reports/Property inheritance'

header = "A list of pages which have [[Property:{0}|{0}]], \
but not [[Property:{1}|{1}]]. Limited to the first 100 results. \
Data as of <onlyinclude>{2}</onlyinclude>.\n"


config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

wiki = wikitools.Wiki('http://www.wikidata.org/w/api.php')
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))



def get_label(db, pid):
    cursor=db.cursor()
    id = int(pid.replace('P',''))
    cursor.execute(label_query, (id,))
    answer = cursor.fetchone()[0]
    return answer

def replag(db):
    cursor=db.cursor()
    cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
    rep_lag = cursor.fetchone()[0]
    return (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

def mk_report(db, first, second):
    cursor = db.cursor()
    # print 'running query'
    cursor.execute(query, (first, second))
    text = ''
    for qid in cursor:
        text+= '*[[{0}]]\n'.format(qid[0])
    # print 'done'
    return text

def run(db, first, second):
    title = base + '/{0} not in {1}'.format(first, second)
    page = wikitools.Page(wiki, title)
    text = mk_report(db, first, second)
    text = header.format(first, second, replag(db)) + text
    page.edit(text, summary='Bot: Updating database report',bot=1)
    return '\n*[[{0}|Pages with "{1}" but not "{2}"]]'.format(title, get_label(db, first), get_label(db, second))

def main():
    page = wikitools.Page(wiki, base)
    db = oursql.connect(db='wikidatawiki_p',
                        host="sql-s5",
                        read_default_file=os.path.expanduser("~/.my.cnf"),
                        charset=None,
                        use_unicode=False
    )
    text = 'This report spans multiple subpages. It was last run at <onlyinclude>~~~~~</onlyinclude>.'
    text += run(db, 'P17','P30') #country w/o continent
    text += run(db, 'P21', 'P107') #sex w/o entity type
    page.edit(text, summary='Bot: Updating database report',bot=1)

if __name__ == "__main__":
    main()
