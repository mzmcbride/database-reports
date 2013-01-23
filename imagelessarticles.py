#! /usr/bin/env python
# Public domain; MZMcBride; 2013

import datetime
import re

import wikitools

import settings

report_title = settings.rootpage + 'Articles without images'
report_template = u'''\
Articles without images (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl); wiki.setMaxlag(-1)
wiki.login(settings.username, settings.password)

i = 1
output = []
params = { 'action': 'query',
           'generator': 'random',
           'grnnamespace': 0,
           'grnlimit': 'max',
           'prop': 'revisions',
           'rvprop': 'content',
           'format': 'json'
         }
while True:
    if i > 1000:
        break
    request = wikitools.APIRequest(wiki, params)
    response = request.query(querycontinue=False)
    pages = response['query']['pages']
    for page_id, page_data in pages.iteritems():
        if i > 1000:
            break
        page_title = page_data['title']
        page_text = page_data['revisions'][0]['*']
        if not re.search(r'(\[\[(file:|image:)|\.jpg|\.png|\.gif)', page_text, re.I):
            table_row = u"""\
|-
| %d
| {{dbr link|1=%s}}""" % (i, page_title)
            output.append(table_row)
            i += 1

current_of = datetime.datetime.utcnow().strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=settings.editsumm, bot=1)
