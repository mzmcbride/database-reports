#! /usr/bin/env python
# Public domain; MZMcBride; 2011

import datetime
import MySQLdb
import wikitools
import settings

report_title = settings.rootpage + 'Largely duplicative file names'

report_template = u'''\
Largely duplicative file names; data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:80%%;"
|- style="white-space:nowrap;"
! No.
! Normalized name
! Count
! Real names
|-
%s
|}
'''

wiki = wikitools.Wiki(settings.apiurl)
wiki.login(settings.username, settings.password)

# This should be changed sometime to dynamically generate the input.
# Input file currently created by running:
# $ sql enwiki_p < ~/queries/ns/ns_6.sql > /mnt/user-store/mzmcbride/enwiki_p-ns-6.txt
input_file = open('/mnt/user-store/mzmcbride/%s-ns-6.txt' % settings.dbname, 'r')
input_database = settings.dbname+'_file_names'

conn = MySQLdb.connect(host='sql-s1',
                       db='u_mzmcbride_p',
                       read_default_file='~/.my.cnf')

cursor = conn.cursor()
cursor.execute('''
/* dupefilenames.py SLOW_OK */
CREATE TABLE %s (
  orig_name varbinary(255) NOT NULL default '',
  norm_name varbinary(255) NOT NULL default ''
);

CREATE INDEX norm_name ON %s (norm_name);
''' % (input_database, input_database))
cursor.close()
conn.commit()

cursor = conn.cursor()
i = 1
for line in input_file.xreadlines():
    orig_line = line.strip('\n')
    norm_line = unicode(orig_line, 'utf-8').lower().encode('utf-8')
    if orig_line != 'page_title':
        cursor.execute('''
                       /* dupefilenames.py */
                       INSERT INTO %s SET
                       orig_name = "%s",
                       norm_name = "%s"
                       ''' % (input_database,
                              MySQLdb.escape_string(orig_line),
                              MySQLdb.escape_string(norm_line)))
    i += 1
cursor.close()
conn.commit()

output = []
i = 1
cursor = conn.cursor()
cursor.execute('''
/* dupefilenames.py SLOW_OK */
SELECT
  norm_name,
  GROUP_CONCAT(orig_name SEPARATOR '|'),
  COUNT(*)
FROM %s
GROUP BY norm_name
HAVING COUNT(*) > 2
LIMIT 1000;
''' % input_database)
for row in cursor.fetchall():
    norm_name = u'%s' % unicode(row[0], 'utf-8')
    orig_names = []
    for name in row[1].split('|'):
        name = u'[[:File:%s|%s]]' % (unicode(name, 'utf-8'), unicode(name, 'utf-8'))
        orig_names.append(name)
    orig_name = ', '.join(orig_names)
    count = row[2]
    table_row = u'''\
| %d
| %s
| %s
| %s
|-''' % (i, norm_name, count, orig_name)
    output.append(table_row)
    i += 1

cursor.execute('''
               SELECT
                 UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp)
               FROM enwiki_p.recentchanges
               ORDER BY rc_timestamp DESC
               LIMIT 1;
               ''')
rep_lag = cursor.fetchone()[0]
time_diff = datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)
current_of = time_diff.strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
report.edit(report_text, summary=settings.editsumm, bot=1)

cursor.close()
conn.commit()

cursor = conn.cursor()
cursor.execute('''
/* dupefilenames.py SLOW_OK */
DROP TABLE %s;
''' % input_database)
cursor.close()
conn.commit()

conn.close()
