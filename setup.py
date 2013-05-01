from distutils.core import setup

setup(
        name='StormBase',
        version='0.1.0',
        author='Steven Joseph',
        author_email='steven@stevenjoseph.in',
        packages=['stormbase',
                  'stormbase.util',
                  'stormbase.database',
                  'stormbase.database.couchdb',
                  'stormbase.asyncouch',
                  'stormbase.auth',
                  'stormbase.test'],
        #scripts=['bin/stowe-towels.py','bin/wash-towels.py'],
        url='http://pypi.python.org/pypi/StormBase/',
        license='LICENSE.txt',
        description='Useful tornado-related stuff.',
        long_description=open('README.txt').read(),
        install_requires=[
            "tornado",
            "corduroy",
            ],
        )
