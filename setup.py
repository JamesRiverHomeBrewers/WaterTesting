try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'JRHB Water Testing',
    'author': 'Chris Giacofei',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'c.giacofei@gmail.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['jrhbtesting'],
    'scripts': [],
    'name': 'watertest'
}

setup(**config)
