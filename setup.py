from distutils.core import setup

setup(name='dbreps',
      version='0.1-alpha',
      requires=['oursql',
                'wikitools'],
      packages=['reports',
                'reports.general',
                'reports.tests'],
      scripts=['dbreps'],
      )
