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

import logging
import time

from opencastpodcast.config import config
from opencastpodcast.db import get_session, Podcast, Episode
from opencastpodcast.opencast import get_episode_url


# Logger
logger = logging.getLogger(__name__)

def run():
    while True:
        session = get_session()
        episodes = session.query(Episode).where(Episode.media_url == None).all()
        for episode in episodes:
            logger.info('Episode %s: Checking publication', episode.episode_id)
            track = get_episode_url(episode.episode_id)
            if track:
                logger.info('Found %s', track['url'])
                episode.media_url = track.get('url')
                episode.media_size = track.get('size')
                episode.media_duration = track.get('duration')
                session.commit()
        session.close()
        time.sleep(10)
