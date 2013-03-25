# Public domain; MZMcBride, Tim Landscheidt; 2013

"""
Report class for ticker symbols in article leads
"""

import datetime
import re

import wikitools

import reports

class report(reports.report):
    def get_template_redirects(self, template_title):
        template_redirects = set()
        params = { 'action': 'query',
                   'list': 'backlinks',
                   'bltitle': 'Template:%s' % template_title,
                   'blnamespace': 10,
                   'blfilterredir': 'redirects',
                   'format': 'json'
                 }
        request = wikitools.APIRequest(self.wiki, params)
        response = request.query(querycontinue=True)
        backlinks = response['query']['backlinks']
        for backlink in backlinks:
            template_redirects.add(backlink[u'title'].split(':', 1)[1])
        return template_redirects

    def get_title(self):
        return 'Ticker symbols in article leads'

    def get_preamble(self, conn):
        return u'''Ticker symbols in article leads (limited to the first 1000 entries); \
data as of <onlyinclude>%s</onlyinclude>.

Related pages:
* [[WP:TICKER]]
* [[WP:RFC/TICKER]]

Proposed edit summary: <tt><nowiki>rm ticker symbol from article lead \
as it appears in the infobox, per [[WP:TICKER]] and [[WP:RFC/TICKER]]\
</nowiki></tt>''' % datetime.datetime.utcnow().strftime('%H:%M, %d %B %Y (UTC)')

    def get_table_columns(self):
        return ['Article', 'Total instances']

    def get_table_rows(self, conn):
        templates_in_cat = set()
        params = { 'action': 'query',
                   'list': 'categorymembers',
                   'cmtitle': 'Category:Ticker symbol templates',
                   'cmnamespace': 10,
                   'cmlimit': 'max',
                   'format': 'json'
                 }
        request = wikitools.APIRequest(self.wiki, params)
        response = request.query(querycontinue=True)
        members = response['query']['categorymembers']
        for member in members:
            templates_in_cat.add(member[u'title'].split(':', 1)[1])

        template_variations = templates_in_cat
        for template in templates_in_cat:
            template_redirects = self.get_template_redirects(template)
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
            request = wikitools.APIRequest(self.wiki, params)
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
        ticker_templates_re = re.compile(r"\{\{(%s)\|" %
                                         '|'.join(template_variations), re.I)
        ticker_templates_in_lead_re = re.compile(r"'''.+\{\{(%s)\|" %
                                                 '|'.join(template_variations), re.I)
        for title,text in page_texts.iteritems():
            if i > 1000:
                break
            instances = len(ticker_templates_re.findall(text))
            if ticker_templates_in_lead_re.search(text):
                yield [u'{{dbr link|1=%s}}' % title, str(instances)]
                i += 1
