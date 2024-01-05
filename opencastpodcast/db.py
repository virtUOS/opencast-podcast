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
import enum

from functools import wraps
from datetime import datetime
from sqlalchemy import create_engine, func, Column, Date, DateTime, String, \
        Enum, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from opencastpodcast.config import config

# Logger
logger = logging.getLogger(__name__)

# Database uri as described in
# https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls
database = config('database') or 'sqlite:///opencast-podcast.db'

# Global session variable. Set on initialization.
__session__ = None

# Base Class of all ORM objects.
Base = declarative_base()


class Podcast(Base):
    """ORM object for podcasts.
    """
    __tablename__ = 'podcast'
    podcast_id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(String)
    author = Column(String)
    image = Column(String)

    # Episode relationship
    episodes = relationship('Episode')


class Episode(Base):
    """ORM object for podcast episodes.
    """
    __tablename__ = 'episode'
    episode_id = Column(String, primary_key=True)
    podcast_id = Column(String, ForeignKey('podcast.podcast_id'))
    title = Column(String)
    description = Column(Text)
    image = Column(String)
    duration = Column(Integer)
    media = Column(String)
    media_url = Column(String)
    media_size = Column(Integer)
    media_duration = Column(Integer)


def with_session(f):
    """Wrapper for f to make a SQLAlchemy session present within the function

    :param f: Function to call
    :type f: Function
    :raises e: Possible exception of f
    :return: Result of f
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get new session
        session = get_session()
        try:
            # Call f with the session and all the other arguments
            result = f(session, *args, **kwargs)
        except Exception as e:
            # Rollback session, something bad happend.
            session.rollback()
            session.close()
            raise e
        # Close session and return the result of f
        session.close()
        return result
    return decorated


def get_session():
    """Get a new session.

    Lazy load the database connection and create the tables.

    Returns:
        sqlalchemy.orm.session.Session -- SQLAlchemy Session object
    """
    global __session__
    # Create database connection, tables and Sessionmaker if neccessary.
    if not __session__:
        Engine = create_engine(
            database, echo=logger.getEffectiveLevel() == logging.DEBUG)
        __session__ = sessionmaker(bind=Engine)
        Base.metadata.create_all(Engine)

    # Return new session object
    return __session__()
