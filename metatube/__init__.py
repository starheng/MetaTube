import engineio
from flask import Flask, json
from flask.logging import default_handler
from flask_sqlalchemy import SQLAlchemy
from flask_jsglue import JSGlue
from flask_migrate import Migrate
from flask_socketio import SocketIO
from config import Config

import logging
db = SQLAlchemy()
migrate = Migrate()
jsglue = JSGlue()
socketio = SocketIO()

logformat = logging.Formatter(fmt='[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d]: %(message)s', datefmt='%d-%m-%Y %H:%M')

console = logging.StreamHandler()
console.setFormatter(fmt=logformat)

logger = logging.Logger('default')
logger.addHandler(console)

from metatube.settings import bp as bp_settings
from metatube.overview import bp as bp_overview
from metatube.init import init as init_db

def create_app(config_class=Config):
    app = Flask(__name__, static_url_path='/static')
    app.config.from_object(config_class)
    app.config.update(
        FLASK_DEBUG=False,
        FLASK_ENV='production'
    )
    
    app.logger.removeHandler(default_handler)
    app.logger.addHandler(logger)
    console.setLevel(int(app.config["LOG_LEVEL"]))
    is_sqlite = app.config["SQLALCHEMY_DATABASE_URI"].startswith('sqlite:///')
    socket_log = logger if bool(app.config["SOCKET_LOG"]) is True else False
    buffer_size = int(app.config["BUFFER_SIZE"])
    db.init_app(app)

    migrate.init_app(app, db, compare_type=True, render_as_batch=is_sqlite)
    jsglue.init_app(app)
    socketio.init_app(app, async_mode='gevent', json=json, engineio_logger=socket_log, logger=socket_log, max_http_buffer_size=buffer_size) # Allow maximum 10MB to be sent through web sockets
    app.register_blueprint(bp_overview)
    app.register_blueprint(bp_settings)
    init_db(app)
    return app

import metatube.database, metatube.routes