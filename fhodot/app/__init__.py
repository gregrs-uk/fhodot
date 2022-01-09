"""Flask API which frontend uses to fetch data from database"""

from logging import debug
from os import environ

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from fhodot.config import REDIS_URL
from fhodot.database import Session


# static files served by Flask in development but Apache in production
if "FLASK_ENV" in environ and environ["FLASK_ENV"] == "development":
    app = Flask(__name__, static_folder="ui/dist", static_url_path="")
else:
    app = Flask(__name__, static_folder=None)

limiter = Limiter(app,
                  key_func=get_remote_address,
                  default_limits=["10 per second", "60 per minute"],
                  storage_uri=REDIS_URL)

# see https://flask.palletsprojects.com/en/1.1.x/patterns/packages/
import fhodot.app.routes # pylint: disable=wrong-import-position,cyclic-import

@app.teardown_request
def remove_session(exception=None): # pylint: disable=unused-argument
    """Remove database session at end of request"""
    Session.remove()
