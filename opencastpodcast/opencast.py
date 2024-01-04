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

import requests
import logging
import os

from requests.auth import HTTPBasicAuth

from opencastpodcast.config import config

# Public ACL
acl = '{"acl": {"ace": [' \
        '{"allow": true,"role": "ROLE_ANONYMOUS","action": "read"}]}}'

# Logger
logger = logging.getLogger(__name__)


def ensure_list(elem):
    if type(elem) is list:
        return elem
    return [elem]


def auth():
    user = config('opencast', 'user')
    password = config('opencast', 'password')
    return HTTPBasicAuth(user, password)


def post(path, **kwargs):
    server = config('opencast', 'server')
    r = requests.post(f'{server}{path}', auth=auth(), **kwargs)
    r.raise_for_status()


def get(path, **kwargs):
    server = config('opencast', 'server')
    r = requests.get(f'{server}{path}', auth=auth(), **kwargs)
    r.raise_for_status()
    return r.json()


def create_series(podcast):
    logger.info(f'Creating series {podcast.podcast_id}')
    series = {
            'identifier': podcast.podcast_id,
            'publisher': podcast.author,
            'title': podcast.title
            }
    post('/series/', data=series)


def create_episode(episode):
    logger.info(f'Ingesting episode {episode.episode_id}')
    workflow = config('opencast', 'workflow')
    upload_dir = os.path.abspath(config('directories', 'upload') or 'upload')
    image = os.path.join(upload_dir, episode.image)
    upload_tmp_dir = config('directories', 'upload_tmp') or 'upload_tmp'
    media = os.path.join(upload_tmp_dir, episode.media)

    # Build request
    fields = [('acl', (None, acl))]
    fields.append(('identifier', (None, episode.episode_id)))
    fields.append(('title', (None, episode.title)))
    fields.append(('publisher', (None, episode.author)))
    fields.append(('isPartOf', (None, episode.podcast_id)))
    fields.append(('flavor', (None, 'presenter/source')))
    fields.append(('BODY', open(image, 'rb')))
    fields.append(('flavor', (None, 'presenter/source')))
    fields.append(('BODY', open(media, 'rb')))

    # Ingest media
    post(f'/ingest/addMediaPackage/{workflow}', files=fields)


def get_episode_url(episode_id):
    episode = get('/search/episode.json', params={'id': episode_id})
    episode = episode.get('search-results').get('result')
    if not episode:
        return None
    mediapackage = episode.get('mediapackage')
    tracks = ensure_list(mediapackage.get('media').get('track'))
    for track in tracks:
        if track.get('type') == 'presenter/audio':
            return track.get('url')

