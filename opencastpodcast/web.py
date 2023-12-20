# Opencast Podcast Studio
# Copyright 2023 Osnabrück University
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import glob
import logging
import os
import yaml

from dateutil.parser import parse
from flask import Flask, request, redirect, render_template, session, jsonify
from functools import wraps

from opencastpodcast.config import config
from opencastpodcast.db import with_session, Podcast
from opencastpodcast.utils import random_string, organizational_unit


# Logger
logger = logging.getLogger(__name__)

flask_config = {}
if config('ui', 'directories', 'template'):
    flask_config['template_folder'] = config('ui', 'directories', 'template')
if config('ui', 'directories', 'static'):
    flask_config['static_folder'] = config('ui', 'directories', 'static')
app = Flask(__name__, **flask_config)
app.secret_key = config('secret_key') or random_string(64)

__error = {}
__i18n = {}
__languages = []


def init():
    '''Load internationalization and try to register the authentication system.
    '''
    # load internationalization data
    files = glob.glob(os.path.dirname(__file__) + '/i18n/error-*.yml')
    globals()['__languages'] = {os.path.basename(f)[6:-4] for f in files}
    logger.info('Detected available languages: %s', __languages)

    for lang in __languages:
        # load error messages
        i18n_file = os.path.dirname(__file__) + f'/i18n/error-{lang}.yml'
        with open(i18n_file, 'r') as f:
            globals()['__error'][lang] = yaml.safe_load(f)

        # load internationalization file
        i18n_file = os.path.dirname(__file__) + f'/i18n/i18n-{lang}.yml'
        with open(i18n_file, 'r') as f:
            globals()['__i18n'][lang] = yaml.safe_load(f)


@app.route('/', methods=['GET'])
@with_session
def home(db):
    podcasts = db.query(Podcast)
    return render_template('index.html', podcasts=podcasts)


init()
