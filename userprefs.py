#!/usr/bin/python
# Public domain; MZMcBride; 2011

import ConfigParser
import datetime
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'User preferences'

report_template = u'''\
User preferences statistics; data as of <onlyinclude>%s</onlyinclude>.

== Gender ==
{| class="wikitable sortable plainlinks" style="width:80%%;"
|- style="white-space:nowrap;"
! Gender
! Users
|-
%s
|}

== Language ==
{| class="wikitable sortable plainlinks" style="width:80%%;"
|- style="white-space:nowrap;"
! Language code
! Language name
! Users
|-
%s
|}

== Skin ==
{| class="wikitable sortable plainlinks" style="width:80%%;"
|- style="white-space:nowrap;"
! Skin
! Users
|-
%s
|}

== Gadgets ==
{| class="wikitable sortable plainlinks" style="width:80%%;"
|- style="white-space:nowrap;"
! Gadget
! Users
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'),
                       db=config.get('dbreps', 'dbname'),
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()

gender_output = []
cursor.execute('''
/* userprefs.py SLOW_OK */
SELECT
  up_value,
  COUNT(*)
FROM user_properties_anonym
WHERE up_property = 'gender'
GROUP BY up_value;
''')
for row in cursor.fetchall():
    up_value = '{{MediaWiki:gender-%s}}' % row[0]
    count = row[1]
    table_row = u'''\
| %s
| %s
|-''' % (up_value, count)
    gender_output.append(table_row)

language_output = []
cursor.execute('''
/* userprefs.py SLOW_OK */
SELECT
  up_value,
  COUNT(*)
FROM user_properties_anonym
WHERE up_property = 'language'
GROUP BY up_value;
''')
for row in cursor.fetchall():
    lang_code = row[0]
    lang_name = '{{#language:%s}}' % row[0]
    count = row[1]
    table_row = u'''\
| %s
| %s
| %s
|-''' % (lang_code, lang_name, count)
    language_output.append(table_row)

skin_output = []
cursor.execute('''
/* userprefs.py SLOW_OK */
SELECT
  up_value,
  COUNT(*)
FROM user_properties_anonym
WHERE up_property = 'skin'
GROUP BY up_value;
''')
for row in cursor.fetchall():
    up_value = '{{MediaWiki:skinname-%s}}' % row[0]
    count = row[1]
    table_row = u'''\
| %s
| %s
|-''' % (up_value, count)
    skin_output.append(table_row)

gadgets_output = []
cursor.execute('''
/* userprefs.py SLOW_OK */
SELECT
  up_property,
  COUNT(*)
FROM user_properties_anonym
WHERE up_property LIKE 'gadget-%'
AND up_value = 1
GROUP BY up_property;
''')
for row in cursor.fetchall():
    up_property = '[[MediaWiki:%s|%s]]' % (row[0], row[0].split('gadget-', 1)[1])
    count = row[1]
    table_row = u'''\
| %s
| %s
|-''' % (up_property, count)
    gadgets_output.append(table_row)

cursor.execute('''
               SELECT
                 UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp)
               FROM recentchanges
               ORDER BY rc_timestamp DESC
               LIMIT 1;
               ''')
rep_lag = cursor.fetchone()[0]
time_diff = datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)
current_of = time_diff.strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of,
                                 '\n'.join(gender_output),
                                 '\n'.join(language_output),
                                 '\n'.join(skin_output),
                                 '\n'.join(gadgets_output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
