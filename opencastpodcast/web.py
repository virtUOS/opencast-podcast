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
import uuid
import yaml

from datetime import datetime
from flask import Flask, request, redirect, render_template, session, \
                  url_for, send_from_directory
from functools import wraps

from opencastpodcast.config import config
from opencastpodcast.db import with_session, Podcast, Episode
from opencastpodcast.utils import random_string
from opencastpodcast.opencast import create_series, create_episode
from opencastpodcast.itunes import itunes_categories
from opencastpodcast.feed import update_feed


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
    return render_template('index.html',
                           podcasts=podcasts,
                           itunes_categories=itunes_categories)


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
    podcast.language = request.form.get('language')
    podcast.category = request.form.get('category')
    podcast.explicit = request.form.get('explicit')
    podcast.image = filename

    create_series(podcast)

    db.add(podcast)
    db.commit()

    # Create initial RSS feed
    update_feed(identifier)

    # Back to home
    return redirect(url_for('home'))


@app.route('/p/<identifier>')
@with_session
def podcast(db, identifier):
    base_url = config('server', 'base_url').rstrip('/')
    podcast = db.query(Podcast).where(Podcast.podcast_id == identifier).one()
    return render_template('podcast.html', base_url=base_url, podcast=podcast)


@app.route('/p/<identifier>', methods=['POST'])
@with_session
def episode_add(db, identifier):
    podcast = db.query(Podcast).where(Podcast.podcast_id == identifier).one()
    episode = Episode()
    episode.episode_id = str(uuid.uuid4())
    episode.podcast_id = identifier

    # check if the post request has a valid media file
    if 'media' not in request.files or not request.files['media'].filename:
        return 'Media file is missing', 400
    media = request.files['media']
    ext = media.filename.lower().split('.')[-1]
    if ext not in ('mp3', 'm4a'):
        return 'Invalid media type', 400
    filename = f'{identifier}-{episode.episode_id}.{ext}'
    upload_tmp_dir = config('directories', 'upload_tmp') or 'upload_tmp'
    media_tmp_path = os.path.join(upload_tmp_dir, filename)
    media.save(media_tmp_path)
    episode.media = filename

    # check if the post request has a valid image
    if 'image' in request.files and request.files['image'].filename:
        image = request.files['image']
        ext = image.filename.lower().split('.')[-1]
        if ext not in ('jpg', 'png', 'jpeg'):
            return 'Invalid image type', 400
        filename = f'{identifier}-{episode.episode_id}.{ext}'
        upload_dir = config('directories', 'upload') or 'upload'
        image.save(os.path.join(upload_dir, filename))
        episode.image = filename

    else:
        # use the podcast's cover image if none was provided
        episode.image = podcast.image

    episode.title = request.form.get('title')
    episode.description = request.form.get('description')
    episode.author = request.form.get('author')
    episode.published = datetime.now()

    create_episode(episode)
    logger.info('Deleting temporary file %s', episode.media)
    os.remove(media_tmp_path)

    db.add(episode)
    db.commit()

    # Back to podcast page
    return redirect(url_for('podcast', identifier=identifier))


@app.route('/i/<image>')
@with_session
def image(db, image):
    upload_dir = os.path.abspath(config('directories', 'upload') or 'upload')
    if '/' in image:
        return 'No such image', 404
    return send_from_directory(upload_dir, image)


@app.route('/r/<identifier>.xml')
@with_session
def rss(db, identifier):
    feed_dir = os.path.abspath(config('directories', 'feeds') or 'feeds')
    if '/' in identifier:
        return 'No such feed', 404
    logger.debug('Delivering feed for %s', identifier)
    return send_from_directory(feed_dir, f'{identifier}.xml')


init()
