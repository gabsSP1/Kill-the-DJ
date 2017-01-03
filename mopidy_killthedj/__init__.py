from __future__ import unicode_literals

import os
import logging
from request_handlers import *
from mopidy import config, ext

root = os.path.dirname(os.path.abspath(__file__))

__version__ = '0.1.0'

# TODO: If you need to log, use loggers named after the current Python module
logger = logging.getLogger(__name__)


def ktd_api(config, core):
    return [
        (r'/', IndexHandler, {'version': __version__, 'core': core}),
        (r"/docs/(.*)", tornado.web.StaticFileHandler,
            {"path": root + "/API_documentation/", "default_filename": "index.html"}),

        ('r/session', SessionHandler, {'core': core}),
        ('r/session/users', UsersHandler, {'core': core}),

        (r'/tracks', TrackHandler, {'core': core}),
        (r'/searches', SearchHandler, {'core': core}),

        (r'/tracklist/tracks', TracklistHandler, {'core': core}),
        (r'/tracklist/votes', VoteHandler, {'core': core}),
    ]


class Extension(ext.Extension):
    dist_name = 'Mopidy-KillTheDJ'
    ext_name = 'killthedj'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        return schema

    def setup(self, registry):
        registry.add('http:app', {
            'name': self.ext_name,
            'factory': ktd_api,
        })



