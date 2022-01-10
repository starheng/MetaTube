import os
from os.path import join, dirname
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = join(dirname(__file__), '.flaskenv')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class Config(object):
    ''' All environment variables are stored here ''' 
    SECRET_KEY = str(os.urandom(24))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'metatube/app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMPLATES_AUTO_RELOAD = True
    FLASK_DEBUG = False
    FLASK_ENV = 'production'
    BASE_DIR = basedir
    LOGGER = os.environ.get('LOG', False)
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 10)
    SOCKET_LOG = os.environ.get('SOCKET_LOG', False)
    PORT = os.environ.get('PORT', 5000)
    FFMPEG =  os.environ.get('FFMPEG', "")
    DOWNLOADS = os.environ.get('DOWNLOADS', os.path.join(basedir, 'downloads'))
    BUFFER_SIZE = os.environ.get('BUFFER_SIZE', 10000000)
    URL_SUBPATH = os.environ.get('URL_SUBPATH', '/')