#!/usr/bin/env python
"""

Copyright (C) 2013 Legoktm


Licensed as CC-Zero. See https://creativecommons.org/publicdomain/zero/1.0 for more details.
"""
import datetime
import oursql
import os
import wikitools
import ConfigParser

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

wiki = wikitools.Wiki('http://www.wikidata.org/w/api.php')
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))


get_namespaces = """
/* SLOW_OK */
SELECT
wiki.dbname,
namespacename.ns_name
FROM toolserver.wiki AS wiki
JOIN toolserver.namespacename as namespacename
ON wiki.dbname = namespacename.dbname
WHERE wiki.family = "wikipedia"
AND wiki.is_multilang =0
AND namespacename.ns_id=2
"""



query = """
SELECT
 ips_item_id,
 ips_site_page
FROM wb_items_per_site
WHERE ips_site_id="{lang}wiki"
AND ips_site_page LIKE "{ns}:%"
AND NOT ips_site_page LIKE "%Emijrp%"
AND NOT ips_site_page LIKE "%UBX%"
AND NOT ips_site_page LIKE "%Vorlage%"
AND NOT ips_site_page LIKE "%Userbox%"
AND NOT ips_site_page LIKE "%Box%"
AND NOT ips_site_page LIKE "%Userboksy%"
limit 100;
"""

template = """
A list of pages with links to userspace. Last updated at <onlyinclude>{0}</onlyinclude>.

{{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! Item
! Link
"""

table_row = """|-
| [[Q{0}]]
| [[:{1}:{2}]]
"""

def main():
    db_ts = oursql.connect(
        host="sql-toolserver",
        read_default_file=os.path.expanduser("~/.my.cnf"),
        charset=None,
        use_unicode=False
    )
    cursor = db_ts.cursor()
    cursor.execute(get_namespaces)
    rows = cursor.fetchall()
    db_ts.close()
    db = oursql.connect(db='wikidatawiki_p',
        host="sql-s5",
        read_default_file=os.path.expanduser("~/.my.cnf"),
        charset=None,
        use_unicode=False
    )
    text = ''
    for row in rows:
    #    print row
        text+= get_report(db, *row)
    text = template.format(replag(db)) + text + '\n|}'
    page = wikitools.Page(wiki, 'Wikidata:Database reports/User pages')
    page.edit(text, summary='Bot: Updating database report',bot=1)


def get_lang(dbname):
    return dbname.replace('wiki_p','')

def get_report(db, dbname, ns):
    text = ''
    cursor = db.cursor()
    cursor.execute(query.format(lang=get_lang(dbname), ns=ns))
    for row in cursor:
        # print row

        text += table_row.format(row[0], get_lang(dbname).replace('_','-'), row[1])
    return text

def replag(db):
    cursor=db.cursor()
    cursor.execute('SELECT UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp) FROM recentchanges ORDER BY rc_timestamp DESC LIMIT 1;')
    rep_lag = cursor.fetchone()[0]
    return (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')


if __name__ == "__main__":
    main()
