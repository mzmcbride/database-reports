# Public domain; MZMcBride, Tim Landscheidt; 2011, 2013

"""
Report class for articles containing invalid template parameters
"""

import re

import wikitools

import reports

class report(reports.report):
    def get_target_templates_list(self):
        return ['Infobox_officeholder']

    def get_template_parameters_from_template(self, template):
        template_parameters = set()
        template_text = wikitools.Page(self.wiki, 'Template:'+template).getWikiText().decode('utf-8')
        legal_chars = r'[ %!"$&\'()*,\-.0-9:;?@A-Z^_`a-z~\x80-\xFF]'
        legal_chars_spaceless = r'[%!"$&\'()*,\-.0-9:;?@A-Z^_`a-z~\x80-\xFF]'
        dynamic_parameter_re = re.compile(r'('+
                                          legal_chars_spaceless + '+' +
                                          r')\{\{#if:\{\{\{(' +
                                          legal_chars + '+' +
                                          r')\|\}\}\}\|(' +
                                          legal_chars + '*' +
                                          r')\|(' +
                                          legal_chars + '*' +
                                          r')\}\}(' +
                                          legal_chars + '*' +
                                          r')')
        for match in dynamic_parameter_re.finditer(template_text):
            parameter_name_1 = match.group(1)+match.group(3)+match.group(5)
            parameter_name_2 = match.group(1)+match.group(4)+match.group(5)
            template_parameters.add(parameter_name_1)
            template_parameters.add(parameter_name_2)
        parameter_re = re.compile(r'\{\{\{(' + legal_chars + r'+)(\||\})', re.I|re.MULTILINE)
        for match in parameter_re.finditer(template_text):
            template_parameters.add(match.group(1).strip())
        return template_parameters

    def get_articles_list(self, cursor, template):
        articles_list = []
        cursor.execute('''
                       /* bullshitparams.py SLOW_OK */
                       SELECT
                         CONVERT(page_title USING utf8)
                       FROM page
                       JOIN templatelinks
                       ON tl_from = page_id
                       LEFT JOIN %s.bullshit_reviewed_page_titles
                       USING (page_id)
                       WHERE tl_namespace = 10
                       AND tl_title = ?
                       AND page_namespace = 0
                       AND page_is_redirect = 0
                       AND bullshit_reviewed_page_titles.page_id IS NULL;
                       ''' % self.userdb, (template, ))
        for (page_title, ) in cursor:
            articles_list.append(page_title)

        return articles_list

    def grab_template(self, article_text, template_redirects):
        template_re = re.compile(r'\{\{\s*%s\s*(.*?)\}\}' % template_redirects, re.I|re.MULTILINE|re.DOTALL)
        if not template_re.search(article_text):
            return False
        string_start_position = template_re.search(article_text).start()
        start_brace_strings = ['{{', '{{{']
        end_brace_strings = ['}}', '}}}']
        brace_strings = start_brace_strings + end_brace_strings
        shit_re = re.compile(r'(%s)' % '|'.join(re.escape(brace_string) for brace_string in brace_strings))
        start_matches = 0
        end_matches = 0
        for match in shit_re.finditer(article_text[string_start_position:]):
            if match.group(0) in start_brace_strings:
                start_matches += 1
            elif match.group(0) in end_brace_strings:
                string_end_position = match.end()
                end_matches += 1
            if start_matches == end_matches:
                template_content = article_text[string_start_position:string_end_position+string_start_position]
                return template_content
        return False

    def get_template_parameters_from_article(self, article, templates, template_redirects):
        legal_chars = r'[ %!"$&\'()*,\-.0-9:;?@A-Z^_`a-z~\x80-\xFF]'
        article_parameters = set()
        inner_template_re = re.compile(r'\{\{[^}]+\}\}', re.I|re.MULTILINE)
        parameter_re = re.compile(r'\|\s*(' + legal_chars + r'+)\s*=', re.I|re.MULTILINE)
        article_text = wikitools.Page(self.wiki, article).getWikiText().decode('utf-8')
        for template in templates:
            template_content = self.grab_template(article_text, template_redirects)
            if not template_content:
                continue
            for match in inner_template_re.finditer(template_content[2:]):
                template_redirects = legal_chars + '+'
                inner_template = self.grab_template(template_content[2:], template_redirects)
                if inner_template:
                    template_content = re.sub(re.escape(inner_template), '', template_content)
            break
        if template_content:
            for match in parameter_re.finditer(template_content):
                article_parameter = match.group(1).strip()
                article_parameters.add(article_parameter)
        return article_parameters

    def get_template_redirects(self, cursor, template):
        template_redirects = [template.replace('_', r'[\s_]*')]
        cursor.execute('''
                       /* bullshitparams.py SLOW_OK */
                       SELECT
                         CONVERT(page_title USING utf8)
                       FROM redirect
                       JOIN page
                       ON rd_from = page_id
                       WHERE page_namespace = 10
                       AND rd_title = ?
                       AND rd_namespace = 10;
                       ''' , (template, ))
        for (template_redirect, ) in cursor:
            template_redirects.append(template_redirect.replace('_', r'[\s_]*'))
        template_redirects_list = r'(%s)' % '|'.join(template_redirects)
        return template_redirects_list

    def needs_user_db(self):
        return True

    def get_title(self):
        return 'Articles containing invalid template parameters'

    def get_preamble_template(self):
        return u'''Articles containing invalid template parameters (limited to approximately \
the first 1000 entries); data as of <onlyinclude>%s</onlyinclude>.'''

    def get_table_columns(self):
        return ['Page', 'Parameter']

    def get_table_rows(self, conn):
        cursor = conn.cursor()

        target_templates = self.get_target_templates_list()

        count = 1
        for template in target_templates:
            if count > 1000:
                break
            articles_list = self.get_articles_list(cursor, template)
            template_parameters = self.get_template_parameters_from_template(template)
            template_redirects = self.get_template_redirects(cursor, template)
            for article in articles_list:
                if count > 1000:
                    break
                article_parameters = self.get_template_parameters_from_article(article,
                                                                               target_templates,
                                                                               template_redirects)
                bullshit_parameters_count = 0
                for i in article_parameters-template_parameters:
                    yield [u'{{dbr link|1='+article.replace('_', ' ')+u'}}', i]
                    count += 1
                    bullshit_parameters_count += 1
                if bullshit_parameters_count == 0:
                    cursor.execute(u'REPLACE INTO %s.bullshit_reviewed_page_titles (page_id) SELECT page_id FROM page WHERE page_namespace = 0 AND page_title = CONVERT(? USING utf8);' % self.userdb, (article, ))

        cursor.close()
