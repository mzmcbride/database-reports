from distutils.core import setup
import glob

setup(name='dbreps',
      version='0.1-alpha',
      requires=['oursql',
                'wikitools'],
      packages=['reports',
                'reports.enwiki',
                'reports.general',
                'reports.tests'],
      scripts=['dbreps'] + [file for dir in ['commonswiki', 'enwiki', 'general', 'plwiki', 'wikidatawiki'] for file in glob.glob(dir + '/*.py')]
      )
