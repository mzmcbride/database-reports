#!/usr/bin/python

# Copyright 2010 bjweeks, MZMcBride

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import codecs
import ConfigParser
import datetime
import MySQLdb, MySQLdb.cursors
import os
import re
import wikitools

config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/.dbreps.ini')])

debug = False

skipped_pages = []
skipped_file = codecs.open('/home/mzmcbride/scripts/predadurr/skipped_pages.txt', 'r', 'utf-8')
for i in skipped_file.read().strip('\n').split('\n'):
    skipped_pages.append(i)
skipped_file.close()

excluded_titles = [
'^USS_',
'_[Ff]amily$',
'_[Mm]odel$',
'^FBI_',
'^The_',
'_School$',
'_Station$',
'_Band$',
'_Canada$',
'_Church$',
'_Tigers$',
'^List(s)?_of',
'^Numbers_in',
'^\d',
'\d$',
'_of_',
'_and_',
'_\&_',
'\(band\)',
'_FC$',
'_\([Ff]ilm\)$',
'_transmission$',
'_\(miniseries\)$',
'_College$',
'album\)$',
'song\)$',
'[Dd]isambiguation\)$',
'_Awards?$',
'_[Ss]chool',
'_team$',
'_[Hh]ighway',
'_[Dd]iscography$',
'_election$',
'_bibliography',
'^Official_',
'^National_',
'^Los_Premios_',
'^LaserWriter',
'^IEEE_',
'^HMS_',
'\(gene\)$',
'_[Rr]anking',
'_Index$',
'_Inc\.$',
'_Incorporated$',
'^United_',
'^Women',
'^Official',
'^Governor_General\'s_Award'
]

jobs = [
'Athletes',
'Accountants',
'Actors',
'Actresses',
'Administrators',
'Aerospace engineers',
'Air traffic controllers',
'Ambassadors',
'Anesthetists',
'Anchormen',
'Animators',
'Animal trainers',
'Archaeologists',
'Architects',
'Art dealers',
'Artists',
'Astronauts',
'Astronomers',
'Athletic trainers',
'Attorneys',
'Authors',
'Auditors',
'Babysitters',
'Bakers',
'Bank tellers',
'Bankers',
'Barbers',
'Baristas',
'Barristers',
'Bartenders',
'Bassoonists',
'Batmen',
'Beauty therapists',
'Beekeepers',
'Bellhops',
'Blacksmiths',
'Boilermakers',
'Bookkeepers',
'Booksellers',
'Brewers',
'Builders',
'Butchers',
'Butlers',
'Brain surgeons',
'Cab drivers',
'Calligraphers',
'Cameramen',
'Car designers',
'Cardiologists',
'Carpenters',
'Cartoonists',
'Cartographers',
'Cashiers',
'Cellists',
'Chaplains',
'Chess players',
'Chief compliance officers',
'Chief executive officers',
'Chief information officers',
'Chief financial officers',
'Chief technology officers',
'Chief privacy officers',
'Chauffeurs',
'Cheesemakers',
'Chefs',
'Chemists',
'Chief of polices',
'Chimney sweeps',
'Cinematographers',
'Civil servants',
'Civil engineers',
'Clarinetists',
'Cleaners',
'Clerks',
'Clockmakers',
'Clowns',
'Coachs',
'Coachmen',
'Coast guards',
'Cobblers',
'Columnists',
'Comedians',
'Company secretaries',
'Compasssmiths',
'Composers',
'Computer programmers',
'Conductors',
'Construction engineers',
'Construction workers',
'Consuls',
'Consultants',
'Contractors',
'Cooks',
'Coroners',
'Corrections officers',
'Cosmonauts',
'Costume designers',
'Couriers',
'Cryptographers',
'Cryptozoologists',
'Curriers',
'customer service advisors',
'Customer service representatives',
'Customs officers',
'Dancers',
'Dentists',
'Deputies',
'Dermatologists',
'Detectives',
'Dictators',
'Disc jockeys',
'Underwater divers',
'Divers',
'Doctors',
'Dog walkers',
'Doormen',
'Dressmakers',
'Croupiers',
'Dealers',
'Dummies',
'Electricians',
'Entertainers',
'Escorts',
'Engineers',
'Falconers',
'Farmers',
'Farriers',
'Fashion designers',
'Film directors',
'Film producers',
'Financial advisers',
'Fire marshals',
'Fire Safety Officers',
'Firefighters',
'First Mates',
'Fishmongers',
'Fishermen',
'Machinists',
'Fitters',
'Flavorists',
'Fletchers',
'Flight attendants',
'Flight instructors',
'Florists',
'Flautists',
'Food critics',
'Footballers',
'Foresters',
'Fortune tellers',
'Funeral directors',
'Gamekeepers',
'Game designers',
'Game wardens',
'Gardeners',
'Gemcutters',
'Genealogists',
'Generals',
'Geologists',
'Gigolos',
'Goldsmiths',
'Government agents',
'Governors',
'Graphic designers',
'Gravediggers',
'Greengrocers',
'Grocers',
'Guides',
'Guitarists',
'Gunsmiths',
'Hairdressers',
'Hairstylists',
'Handymen',
'Harbourmasters',
'Harpists',
'Hatters',
'Historians',
'Homeopaths',
'Hotel managers',
'Housekeepers',
'Housewifes',
'Limners',
'Illuminators',
'Illusionists',
'Illustrators',
'Image consultants',
'Importers',
'Industrial engineers',
'Industrialists',
'Information Technologists',
'Inkers',
'Innkeepers',
'Teachers',
'Instructors',
'Interior designers',
'Interpreters',
'Interrogators',
'Inventors',
'Investigators',
'Investment bankers',
'Investment brokers',
'Ironmongers',
'Ironmasters',
'Ironworkers',
'Jailers',
'Janitors',
'Jewellers',
'Journalists',
'Jurists',
'Judges',
'Jockeys',
'Jogglers',
'Karate masters',
'Kinesiologists',
'Kickboxers',
'Kings',
'kindergarten teachers',
'Loan officers',
'Laborers',
'Landlords',
'Landladies',
'Laundresses',
'Lavendars',
'Law enforcement agents',
'Lawyers',
'Leadworkers',
'Leatherers',
'Leather workers',
'Lecturers',
'Level designers',
'Mappers',
'Librarianships',
'Librettists',
'Lifeguards',
'Lighthouse keepers',
'Lighting technicians',
'Linemen',
'Linguisticss',
'Linguists',
'Loan officers',
'Lobbyists',
'Locksmiths',
'Logisticians',
'Lumberjacks',
'Lyricists',
'Magistrates',
'Magnates',
'Maids',
'Postmen',
'Mailman or Mail carriers',
'Make-up artists',
'Management consultants',
'Managers',
'Manicurists',
'Manufacturers',
'Marine biologists',
'Market gardeners',
'Martial artists',
'Masonries',
'Masons',
'Master of business administrators',
'Massage therapists',
'masseuses',
'masseurs',
'Matadors',
'Mathematicians',
'Mechanics',
'Mechanical Engineers',
'Mechanicians',
'Mediators',
'Medics',
'Medical billers',
'Medical Laboratory Scientists',
'Medical Transcriptionists',
'Mesmerists',
'Bicycle messengers',
'Messengers',
'Mid-wifes',
'Milkmen',
'Milkmaids',
'Millers',
'Miners',
'Missionaries',
'Models',
'Modellers',
'Moneychangers',
'Moneylenders',
'Monks',
'Mortgage brokers',
'Mountaineers',
'Muralists',
'Music educators',
'Musicians',
'Navigators',
'Negotiators',
'Netmakers',
'Neurologists',
'Newscasters',
'Night auditors',
'Nightwatchmens',
'Notary publics',
'Notaries',
'Novelists',
'Numerologists',
'Numismatists',
'Nuns',
'Nursemaids',
'Nurses',
'Nutritionists',
'Oboists',
'Obstetricians',
'Occupational therapists',
'Odontologists',
'Oncologists',
'Ontologists',
'Operators',
'Ophthalmologists',
'Opticians',
'Optometrists',
'Oracles',
'Ordinary Seamen',
'Organizers',
'Orthodontists',
'Ornithologists',
'Hostlers',
'Ostlers',
'Otorhinolaryngologists',
'Optometrists',
'Ocularists',
'Painters',
'Paleontologists',
'Paralegals',
'Paramedics',
'Park rangers',
'Parole Officers',
'Pastors',
'Patent attorneys',
'Patent examiners',
'Pathologists',
'Pawnbrokers',
'Peddlers',
'Pediatricians',
'Pedologists',
'Percussionists',
'Perfumers',
'Personal Trainers',
'Pharmacists',
'Philanthropists',
'Philologists',
'Philosophers',
'Photographers',
'Physical Therapists',
'Physicians',
'Physician Assistants',
'Physicists',
'Physiognomists',
'Physiotherapists',
'Pianists',
'Piano tuners',
'Pilots',
'Aviators',
'Pirates',
'Plumbers',
'Podiatrists',
'Poets',
'Police inspectors',
'Politicians',
'Porters',
'Presenters',
'Presidents',
'Press officers',
'Priests',
'Princesss',
'Principals',
'Printers',
'Prison officers',
'Private detectives',
'Probation Officers',
'Proctologists',
'Product designers',
'Professors',
'Professional dominants',
'Programmers',
'Project Managers',
'Proofreaders',
'Prostitutes',
'Psychiatrists',
'Psychodramatists',
'Psychologists',
'Public Relations Officers',
'Public speakers',
'Publishers',
'Porn stars',
'Queen consorts',
'Queen regnants',
'Quilters',
'Rabbis',
'Radiologists',
'Radiographers',
'Real estate brokers',
'Real estate investors',
'Real estate developers',
'Receptionists',
'Record producers',
'Referees',
'Refuse collectors',
'Registrars',
'Registered Nurses',
'Reporters',
'Researchers',
'Respiratory Therapists',
'Restaurateurs',
'Retailers',
'Rubbish Collectors',
'Sexologists',
'Sex Slaves',
'Sailmakers',
'Sailors',
'Salesmens',
'Sanitation workers',
'Sauciers',
'Saxophonists',
'Sawyers',
'Scientists',
'School superintendents',
'Reconnaissances',
'Scouts',
'Screenwriters',
'Scribes',
'Scriveners',
'Seamstresss',
'Second Mates',
'Secret service agents',
'Secretary generals',
'Security guards',
'Senators',
'Search engine optimizers',
'Sextons',
'Sheepshearers',
'Sheriffs',
'Sheriff officers',
'Shoemakers',
'Shoeshiners',
'Shop assistants',
'Singers',
'Skydivers',
'Sleepers',
'Sleuths',
'Social workers',
'Socialites',
'Software engineers',
'Soil scientists',
'Soldiers',
'Solicitors',
'Sommeliers',
'Sonographers',
'Sound Engineers',
'Special agents',
'Speech therapists',
'Sportsmen',
'Spies',
'Statisticians',
'Street artists',
'Street musicians',
'Stevedores',
'Street sweepers',
'Street vendors',
'Structural engineers',
'Stunt doubles',
'Stunt performers',
'Surgeons',
'Supervisors',
'Surveyors',
'Swimmers',
'Switchboard operators',
'System administrators',
'Systems analysts',
'Students',
'Tailors',
'Tanners',
'Tapestrymakers',
'Tapicers',
'Tapesters',
'Tax collectors',
'Tax lawyers',
'Taxidermists',
'Taxicab drivers',
'Taxonomists',
'Tea ladies',
'Teachers',
'Technicians',
'Technologists',
'Technical writers',
'Telegraphists',
'Telegraphers',
'Telephone operators',
'Tennis players',
'Terminators',
'Test developers',
'Test pilots',
'Thatchers',
'Theatre directors',
'Therapists',
'Thimblers',
'Tilers',
'Toolmakers',
'Tour Guides',
'Trademark attorneys',
'Merchants',
'Traders',
'Tradesmen',
'Trainers',
'Transit planners',
'Translators',
'Transport Planners',
'Treasurers',
'Truck drivers',
'Turners',
'Tutors',
'Tylers',
'Typists',
'Undertakers',
'Ufologists',
'Undercover agents',
'Underwriters',
'Upholsterers',
'Urban planners',
'Urologists',
'Ushers',
'Underwear models',
'Valets',
'Sextons',
'Vergers',
'Veterinarians',
'Vibraphonists',
'Vicars',
'Video editors',
'Video game developers',
'Vintners',
'Violinists',
'Violists',
'Voice Actors',
'Waiting staff',
'Watchmakers',
'Weaponsmiths',
'weather forecasters',
'Weathermen',
'Weavers',
'Web designers',
'Web developers',
'Wedding planners',
'Welders',
'Wet nurses',
'Winemakers',
'Wood cutters',
'Woodcarvers',
'Wranglers',
'Writers',
'Xylophonists',
'X-ray Operators',
'Yodelers',
'Yinder Hos',
'zen masters',
'zoo veternarians',
'Zookeepers',
'Zoologists',
]

excluded_categories = [
'_clubs',
'-century',
'_phrases',
'_organizations_',
'_pseudonyms',
'_bc_(deaths',
'births)',
'political_parties',
'companies_',
'_species',
'_software',
'communes_of_',
'_(dis)?establishments',
'television_series',
'_cathedrals_',
'_lists',
'needing_coordinates',
'organizations_based_in',
'roller_coasters_in',
'_singles',
'_albums',
'(artist',
'geography)_stubs',
'year_of_death',
'living_people',
'[\ds]_births',
'[\ds]_deaths',
'(rock',
'musical)_groups',
'record_labels',
'fictional',
'disambiguation',
'_films',
'Geography_of',
'Districts_of',
'_songs',
'_books',
'_novels',
'_films',
'mythological',
'Style_guides',
'Fluid_mechanics',
'Quantum_mechanics',
'Computer_printers',
'Buildings_and_monuments',
'Game_manufacturers',
'Guitar_amplifier_manufacturers',
'Bus_manufacturers',
'Car_manufacturers',
'Marine_engine_manufacturers',
'video_game_companies',
'Case_law_reporters',
'BASIC_interpreters',
'Coast_guards',
'Statistical_mechanics',
'Business_models',
'Greek_mythology'
]

excluded_templates = [
'infobox_single',
'infobox_book',
'infobox_television',
'infobox_stadium',
'infobox_company',
'infobox_motorsport_venue',
'infobox_album',
'infobox_tv_channel',
'infobox_film',
'infobox_television_film',
'infobox_software',
'infobox_television_season',
'infobox_scotus_case',
'infobox_golf_tournament',
'infobox_website',
'infobox_vg',
'infobox_university',
'infobox_podcast',
'infobox_bus_transit',
'infobox_shopping_mall',
'infobox_dotcom_company',
'infobox_painting',
'infobox_football_club',
's-rail-start',
'infobox_music_genre',
'infobox_programming_language',
'infobox_company',
'coord'
]

excluded_titles_re = re.compile(r'(%s)' % '|'.join(str(i) for i in excluded_titles))
jobs_re = re.compile(r'(%s)' % '|'.join(r'\b' + str(i) + r'$' for i in jobs), re.I|re.U)
excluded_categories_re = re.compile(r'(%s)' % '|'.join(str(i) for i in excluded_categories), re.I|re.U)
excluded_templates_re = re.compile(r'(%s)' % '|'.join(str(i) for i in excluded_templates), re.I|re.U)
capital_letters_re = re.compile(r'[A-Z]')

report_title = config.get('dbreps', 'rootpage') + 'Potential biographies of living people (4)'

report_template = u'''
Articles that potentially need to be in [[:Category:Living people]] \
(limited to the first 2000 entries). List generated mostly using magic; \
data as of <onlyinclude>%s</onlyinclude>.

{| class="wikitable sortable plainlinks" style="width:100%%; margin:auto;"
|- style="white-space:nowrap;"
! No.
! Biography
|-
%s
|}
'''

wiki = wikitools.Wiki(config.get('dbreps', 'apiurl'))
wiki.login(config.get('dbreps', 'username'), config.get('dbreps', 'password'))

conn = MySQLdb.connect(host=config.get('dbreps', 'host'),
                       db=config.get('dbreps', 'dbname'),
                       read_default_file='~/.my.cnf',
                       cursorclass=MySQLdb.cursors.SSCursor)
cursor = conn.cursor()
cursor.execute('SET SESSION group_concat_max_len = 1000000;')

def has_multiple_capital_letters(page_title):
    if len(capital_letters_re.findall(page_title)) > 1:
        return True
    return False

def has_excluded_categories(categories):
    if excluded_categories_re.search(categories):
        return True
    return False

def has_valid_job(categories):
    for category in categories.split('|'):
        category = category.replace('_', ' ')
        if jobs_re.search(category):
            if debug:
                print category
            return True
    return False

i = 1
total_count = 1
offset = 0
if debug:
    output_limit = 3
else:
    output_limit = 2000
page_titles = set()
output = []
while True:
    if total_count > output_limit:
        break
    cursor.execute('''
    /* potenshblps4.py SLOW_OK */
    SELECT
      page_title,
      GROUP_CONCAT(DISTINCT c1.cl_to SEPARATOR '|'),
      GROUP_CONCAT(DISTINCT tl_title SEPARATOR '|')
    FROM page
    LEFT JOIN templatelinks
    ON tl_from = page_id
    JOIN categorylinks AS c1
    ON c1.cl_from = page_id
    LEFT JOIN categorylinks AS c2
    ON c2.cl_from = page_id
    AND c2.cl_to = 'Living_people'
    WHERE page_namespace = 0
    AND page_is_redirect = 0
    AND c2.cl_to IS NULL
    GROUP BY page_id
    LIMIT 200000 OFFSET %s;
    ''' , offset)
    while True:
        row = cursor.fetchone()
        if i > output_limit:
            break
        if total_count > output_limit:
            break
        if not row:
            break
        page_title = u'%s' % unicode(row[0], 'utf-8')
        page_titles.add(page_title)
        if page_title in skipped_pages:
            continue
        if row[1] is not None:
            cl_to = u'%s' % unicode(row[1], 'utf-8')
        else:
            cl_to = 'NULL'
        if row[2] is not None:
            tl_title = u'%s' % unicode(row[2], 'utf-8')
        else:
            tl_title = ''
        if (not has_excluded_categories(cl_to) and
            not excluded_titles_re.search(page_title) and
            page_title.find('_') != -1 and
            has_valid_job(cl_to) and
            has_multiple_capital_letters(page_title) and
            not excluded_templates_re.search(tl_title)):
            table_row = u'''| %d
| [[%s]]
|-''' % (i, page_title)
            output.append(table_row)
            i += 1
            total_count += 1
    offset += 200000
    if debug:
        print offset

cursor.close()
cursor = conn.cursor()

cursor.execute('''SELECT
                    UNIX_TIMESTAMP() - UNIX_TIMESTAMP(rc_timestamp)
                  FROM recentchanges
                  ORDER BY rc_timestamp DESC
                  LIMIT 1;''')
rep_lag = cursor.fetchone()[0]
current_of = (datetime.datetime.utcnow() - datetime.timedelta(seconds=rep_lag)).strftime('%H:%M, %d %B %Y (UTC)')

report = wikitools.Page(wiki, report_title)
report_text = report_template % (current_of, '\n'.join(output))
report_text = report_text.encode('utf-8')
if debug:
    print report_text
else:
    report.edit(report_text, summary=config.get('dbreps', 'editsumm'), bot=1)

cursor.close()
conn.close()
