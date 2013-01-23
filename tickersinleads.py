#! /usr/bin/env python
# Public domain; MZMcBride; 2012

import datetime
import re

import wikitools

import settings

report_title = settings.rootpage + 'Ticker symbols in article leads'
report_template = u'''\
Ticker symbols in article leads (mostly); data as of \
<onlyinclude>%s</onlyinclude>.

Proposed edit summary: <tt><nowiki>rm ticker symbol from article lead \
as it appears in the infobox, per [[WP:TICKER]] and [[WP:RFC/TICKER]]\
</nowiki></tt>

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl); wiki.setMaxlag(-1)
wiki.login(settings.username, settings.password)

page_texts = {}
params = { 'action': 'query',
           'generator': 'embeddedin',
           'geititle': 'Template:NASDAQ',
           'geinamespace': 0,
           'geilimit': 'max',
           'prop': 'revisions',
           'rvprop': 'content',
           'format': 'json'
         }
request = wikitools.APIRequest(wiki, params)
response = request.query(querycontinue=True)
pages = response['query']['pages']
for page_id, page_data in pages.iteritems():
    page_title = page_data['title']
    page_text = page_data['revisions'][0]['*']
    page_texts[page_title] = page_text

i = 1
output = []
for k,v in page_texts.iteritems():
    ticker_templates = len(re.findall(r'\{\{nasdaq\|', v, re.I))
    if ticker_templates > 1:
        table_row = u"""\
|-
| %d
| {{dbr link|1=%s}}""" % (i, k)
        output.append(table_row)
        i += 1

current_of = datetime.datetime.utcnow().strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=settings.editsumm, bot=1)
