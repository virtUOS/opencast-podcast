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


def post(path, **kwargs):
    server = config('opencast', 'server')
    user = config('opencast', 'user')
    password = config('opencast', 'password')
    auth = HTTPBasicAuth(user, password)

    r = requests.post(f'{server}{path}', auth=auth, **kwargs)
    r.raise_for_status()


def create_series(podcast):
    series = {
            'identifier': podcast.podcast_id,
            'publisher': podcast.author,
            'title': podcast.title
            }
    post('/series/', data=series)


def create_episode(episode):
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
