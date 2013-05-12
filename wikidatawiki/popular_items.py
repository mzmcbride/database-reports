#!/usr/bin/python
"""
Copyright (C) 2013 Legoktm

Licensed as CC-Zero. See https://creativecommons.org/publicdomain/zero/1.0 for more details.
"""
import os
import oursql
import wikitools
import ConfigParser
import datetime
query = """
/* SLOW_OK */
SELECT
 pl_title,
 COUNT(*)
FROM pagelinks
JOIN page
ON pl_from=page_id
WHERE pl_namespace=0
AND page_namespace=0
GROUP BY pl_title
ORDER BY COUNT(*) DESC
LIMIT 200;
"""

label_query = """
SELECT
 term_text
FROM wb_terms
WHERE term_entity_id=?
AND term_entity_type="item"
AND term_language="en"
AND term_type="label"
"""

template = """
A list of the most linked to items. Data as of <onlyinclude>{0}</onlyinclude>.

{{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! Property
! Usage
"""
table_row = """|-
| [[{0}|{{{{label|{0}}}}}]]
| {2}
"""

footer = '|}\n\n[[Category:Properties]]'

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

wiki = wikitools.Wiki('http://www.wikidata.org/w/api.php')
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

def mk_report(db):
    cursor = db.cursor()
    # print 'running query'
    cursor.execute(query)
    text = ''
    for qid, count in cursor:
        text+= table_row.format(qid, count)
    # print 'done'
    return text

def replag(db):
    cursor=db.cursor()
    cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
    rep_lag = cursor.fetchone()[0]
    return (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')


def main():
    page=wikitools.Page(wiki, 'Wikidata:Database reports/Popular items')
    db = oursql.connect(db='wikidatawiki_p',
        host="sql-s5",
        read_default_file=os.path.expanduser("~/.my.cnf"),
        charset=None,
        use_unicode=False
    )
    report = mk_report(db)
    repl = replag(db)
    text = template.format(repl) + report + footer
    #print '----'
    #print text
    page.edit(text, summary='Bot: Updating database report',bot=1)

if __name__ == "__main__":
    main()
