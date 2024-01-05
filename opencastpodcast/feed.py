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
import os

from feedgen.feed import FeedGenerator

from opencastpodcast.config import config
from opencastpodcast.db import get_session, Podcast, Episode
from opencastpodcast.opencast import get_episode_url


# Logger
logger = logging.getLogger(__name__)

def update_feed(podcast_id):
    logger.info('Generating feed for %s', podcast_id)
    db = get_session()
    podcast = db.query(Podcast).where(Podcast.podcast_id == podcast_id).one()
    base_url = config('server', 'base_url').rstrip('/')

    fg = FeedGenerator()
    fg.load_extension('podcast')
    fg.id(f'{base_url}/p/{podcast_id}')
    fg.title(podcast.title)
    fg.description(podcast.description)
    #fg.author( {'name':'John Doe','email':'john@example.de'} )
    fg.author(name=podcast.author)
    fg.link(href=base_url, rel='alternate' )
    fg.logo(f'{base_url}/i/{podcast_id}')
    fg.link(href=f'{base_url}/rss/{podcast_id}.xml', rel='self' )
    fg.language('en')
    fg.podcast.itunes_category('Technology', 'Podcasting')

    for episode in podcast.episodes:
        if not episode.media_url:
            continue
        fe = fg.add_entry()
        fe.id(f'{base_url}/p/{podcast_id}/{episode.episode_id}')
        fe.title(episode.title)
        fe.description(episode.description)
        fe.enclosure(episode.media_url, 0, 'audio/mpeg')

    db.close()

    print(fg.rss_str(pretty=True).decode())
    feed_dir = config('directories', 'feeds') or 'feeds'
    feed_path = os.path.join(feed_dir, f'{podcast_id}.xml')
    logger.info('Writing feed to %s', feed_path)
    fg.rss_file(feed_path)
