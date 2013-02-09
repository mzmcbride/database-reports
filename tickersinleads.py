#! /usr/bin/env python
# Public domain; MZMcBride; 2013

import ConfigParser
import datetime
import os
import re
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'Ticker symbols in article leads'
report_template = u'''\
Ticker symbols in article leads (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

Related pages:
* [[WP:TICKER]]
* [[WP:RFC/TICKER]]

Proposed edit summary: <tt><nowiki>rm ticker symbol from article lead \
as it appears in the infobox, per [[WP:TICKER]] and [[WP:RFC/TICKER]]\
</nowiki></tt>

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Article
! Total instances
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl')); wiki.setMaxlag(-1)
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

templates_in_cat = set()
params = { 'action': 'query',
           'list': 'categorymembers',
           'cmtitle': 'Category:Ticker symbol templates',
           'cmnamespace': 10,
           'cmlimit': 'max',
           'format': 'json'
         }
request = wikitools.APIRequest(wiki, params)
response = request.query(querycontinue=True)
members = response['query']['categorymembers']
for member in members:
    templates_in_cat.add(member[u'title'].split(':', 1)[1])

def get_template_redirects(template_title):
    template_redirects = set()
    params = { 'action': 'query',
               'list': 'backlinks',
               'bltitle': 'Template:%s' % template_title,
               'blnamespace': 10,
               'blfilterredir': 'redirects',
               'format': 'json'
             }
    request = wikitools.APIRequest(wiki, params)
    response = request.query(querycontinue=True)
    backlinks = response['query']['backlinks']
    for backlink in backlinks:
        template_redirects.add(backlink[u'title'].split(':', 1)[1])
    return template_redirects

template_variations = templates_in_cat
for template in templates_in_cat:
    template_redirects = get_template_redirects(template)
    template_variations = template_variations.union(template_redirects)

page_texts = {}
for template in templates_in_cat:
    params = { 'action': 'query',
               'generator': 'embeddedin',
               'geititle': 'Template:%s' % template,
               'geinamespace': 0,
               'geilimit': 'max',
               'prop': 'revisions',
               'rvprop': 'content',
               'rvsection': 0,
               'format': 'json'
             }
    request = wikitools.APIRequest(wiki, params)
    response = request.query(querycontinue=True)
    try:
        pages = response['query']['pages']
    except KeyError:
        # This means no transclusions
        continue
    for page_id, page_data in pages.iteritems():
        page_title = page_data['title']
        page_text = page_data['revisions'][0]['*']
        page_texts[page_title] = page_text

i = 1
output = []
limit = 1000
ticker_templates_re = re.compile(r"\{\{(%s)\|" %
                                 '|'.join(template_variations), re.I)
ticker_templates_in_lead_re = re.compile(r"'''.+\{\{(%s)\|" %
                                         '|'.join(template_variations), re.I)
for title,text in page_texts.iteritems():
    if i > 1000:
        break
    instances = len(ticker_templates_re.findall(text))
    if ticker_templates_in_lead_re.search(text):
        table_row = u"""\
|-
| %d
| {{dbr link|1=%s}}
| %d""" % (i, title, instances)
        output.append(table_row)
        i += 1

current_of = datetime.datetime.utcnow().strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)
