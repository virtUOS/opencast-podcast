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
import re
import yaml

from dateutil.parser import parse
from flask import Flask, request, redirect, render_template, session, \
                  jsonify, url_for, send_from_directory
from functools import wraps

from opencastpodcast.config import config
from opencastpodcast.db import with_session, Podcast
from opencastpodcast.utils import random_string, organizational_unit


# Logger
logger = logging.getLogger(__name__)

flask_config = {}
if config('directories', 'template'):
    flask_config['template_folder'] = config('directories', 'template')
if config('directories', 'static'):
    flask_config['static_folder'] = config('directories', 'static')
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

@app.route('/', methods=['POST'])
@with_session
def podcast_add(db):
    identifier = request.form.get('id')
    if not re.match('^[a-z0-9-]{2,32}$', identifier):
        return 'Invalid identifier', 400

    # check if the post request has a valid image
    if 'image' not in request.files or not request.files['image'].filename:
        return 'Image is missing', 400
    image = request.files['image']
    ext = image.filename.lower().split('.')[-1]
    if ext not in ('jpg', 'png', 'jpeg'):
        return 'Invalid image type', 400
    filename = f'{identifier}.{ext}'
    upload_dir = config('directories', 'upload') or 'upload'
    image.save(os.path.join(upload_dir, filename))

    # create podcast
    podcast = Podcast()
    podcast.podcast_id = identifier
    podcast.title = request.form.get('title')
    podcast.description = request.form.get('description')
    podcast.author = request.form.get('author')
    podcast.image = filename
    db.add(podcast)
    db.commit()

    # Back to home
    return redirect(url_for('home'))

@app.route('/p/<identifier>')
@with_session
def podcast(db):
    podcast = db.query(Podcast).where(Podcast.podcast_id == identifier).one()
    return render_template('podcast.html', podcasts=podcasts)

@app.route('/img/<identifier>')
@with_session
def send_report(db, identifier):
    podcast = db.query(Podcast).where(Podcast.podcast_id == identifier).one()
    upload_dir = os.path.abspath(config('directories', 'upload') or 'upload')
    return send_from_directory(upload_dir, podcast.image)

init()
