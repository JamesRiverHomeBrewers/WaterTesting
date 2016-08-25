import os
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

class BaseConfig(object):
    DEBUG = False
    TESTING = False
    FREEZER_REMOVE_EXTRA_FILES = True

    FREEZER_DESTINATION = os.path.join(ROOT_DIR, 'html')
    FREEZER_RELATIVE_URLS = True

class ProductionConfig(BaseConfig):
    GOOGLE_API_KEY = os.path.join(ROOT_DIR, 'client_id.json')
    GOOGLE_SHEET_ID = '1Z1XF9nabneWBDbFwaovI_n9YcazeNQq4hon1wsIxrus'
    GOOGLE_SHEET_TAB = 'Data'


class DevelopmentConfig(BaseConfig):
    DATA_FILE = os.path.join(ROOT_DIR, 'data.csv')
    DEBUG = True
    TESTING = True


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True
