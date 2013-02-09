#!/usr/bin/python
# Public domain; MZMcBride; 2011

import ConfigParser
import datetime
import MySQLdb
import os
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

report_title = config.get('dbreps', 'rootpage') + 'WikiLove usage'

report_template = u'''\
[[mw:Extension:WikiLove|WikiLove]] usage statistics; \
data as of <onlyinclude>%s</onlyinclude>.

== Message types ==
{| class="wikitable sortable plainlinks"
|- style="white-space:nowrap;"
! No.
! Type
! Uses
|-
%s
|}

== Senders ==
{| class="wikitable sortable plainlinks"
|- style="white-space:nowrap;"
! No.
! User
! Uses
|-
%s
|}

== Custom images ==
{| class="wikitable sortable plainlinks"
|- style="white-space:nowrap;"
! No.
! Image
! Uses
|-
%s
|}

== Uses per day ==
{| class="wikitable sortable plainlinks"
|- style="white-space:nowrap;"
! Day
! Uses
|-
%s
|- class="sortbottom"
! Total
! style="text-align:left;" | %s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'),
                       db=config.get('dbreps', 'dbname'),
                       read_default_file='~/.my.cnf')
cursor = conn.cursor()

types = []
i = 1
cursor.execute('''
/* wikilovestats.py SLOW_OK */
SELECT
  wll_type,
  COUNT(wll_type)
FROM wikilove_log
GROUP BY wll_type
ORDER BY COUNT(wll_type) DESC;
''')
for row in cursor.fetchall():
    wll_type = unicode(row[0], 'utf-8')
    count = row[1]
    table_row = u'''\
| %d
| %s
| %s
|-''' % (i, wll_type, count)
    types.append(table_row)
    i += 1

senders = []
i = 1
cursor.execute('''
/* wikilovestats.py SLOW_OK */
SELECT
  user_name,
  COUNT(wll_sender)
FROM wikilove_log
JOIN user
ON user_id = wll_sender
GROUP BY wll_sender
HAVING COUNT(wll_sender) > 2
ORDER BY COUNT(wll_sender) DESC
LIMIT 20;
''')
for row in cursor.fetchall():
    user_name = u'[[User:%s|%s]]' % (unicode(row[0], 'utf-8'), unicode(row[0], 'utf-8'))
    count = row[1]
    table_row = u'''\
| %d
| %s
| %s
|-''' % (i, user_name, count)
    senders.append(table_row)
    i += 1

custom_images = []
i = 1
cursor.execute('''
/* wikilovestats.py SLOW_OK */
SELECT
  wlil_image,
  COUNT(wlil_image)
FROM wikilove_image_log
GROUP BY wlil_image
HAVING COUNT(wlil_image) > 3
ORDER BY COUNT(wlil_image) DESC
LIMIT 20;
''')
for row in cursor.fetchall():
    wlil_image = u'[[:%s|%s]]' % (unicode(row[0], 'utf-8'), unicode(row[0], 'utf-8').strip('File:'))
    count = row[1]
    table_row = u'''\
| %d
| %s
| %s
|-''' % (i, wlil_image, count)
    custom_images.append(table_row)
    i += 1

days = []
total = 0
cursor.execute('''
/* wikilovestats.py SLOW_OK */
SELECT
  DATE(CONCAT(YEAR(wll_timestamp),"-",MONTH(wll_timestamp),"-",DAY(wll_timestamp))) AS day,
  COUNT(wll_timestamp) AS uses
FROM wikilove_log
GROUP BY day
ORDER BY day ASC;
''')
for row in cursor.fetchall():
    day = row[0]
    uses = row[1]
    total += int(uses)
    table_row = u'''\
| %s
| %s
|-''' % (day, uses)
    days.append(table_row)

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
                                 '\n'.join(types),
                                 '\n'.join(senders),
                                 '\n'.join(custom_images),
                                 '\n'.join(days),
                                 total)
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
