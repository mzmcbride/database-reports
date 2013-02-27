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
 ips_item_id,
 COUNT(*)
FROM wb_items_per_site
WHERE NOT EXISTS (
    SELECT
     *
    FROM wb_items_per_site AS data
    WHERE data.ips_item_id=wb_items_per_site.ips_item_id
    AND data.ips_site_id = ?
)
GROUP BY ips_item_id
ORDER BY COUNT(*) DESC
LIMIT 100;"""

template = """
A list of items with no link to {site}. Data as of <onlyinclude>{0}</onlyinclude>.

{{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! Item
! Sitelinks
"""
table_row = """|-
| [[Q{0}]]
| {1}
"""

footer = '|}'

report_template = """
This report is split over multiple subpages. It was last run at <onlyinclude>~~~~~</onlyinclude>.
"""

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

wiki = wikitools.Wiki('http://www.wikidata.org/w/api.php')
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))


def get_input():
    page = wikitools.Page(wiki, 'Wikidata:Database reports/Missing links/Input')
    text = page.getWikiText()
    for line in text.splitlines():
        if not line.startswith(('#','<')) and line.endswith('wiki'):
            yield line.strip()


def mk_report(db, site):
    cursor = db.cursor()
    # print 'running query on '+site
    cursor.execute(query,(site,))
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
    page=wikitools.Page(wiki, 'Wikidata:Database reports/Missing links')
    db = oursql.connect(db='wikidatawiki_p',
        host="wikidatawiki-p.rrdb.toolserver.org",
        read_default_file=os.path.expanduser("~/.my.cnf"),
        charset=None,
        use_unicode=False
    )
    sites = get_input()
    report_text=report_template
    for site in sites:
        report = mk_report(db, site)
        repl = replag(db)
        text = template.format(repl,site=site) + report + footer
        rep_page=wikitools.Page(wiki, 'Wikidata:Database reports/Missing links/'+site)
        rep_page.edit(text, summary='Bot: Updating database report',bot=1)
        report_text += '\n*[[Wikidata:Database reports/Missing links/{0}|{0}]]'.format(site)
    #print '----'
    #print text
    page.edit(report_text, summary='Bot: Updating database report',bot=1)

if __name__ == "__main__":
    main()
