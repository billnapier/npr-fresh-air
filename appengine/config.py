#!/usr/bin/python
#
# Copyright (C) 2011 by Bill Napier (napier@pobox.com)
#
# Licensed under the Apache License, Version 2.0 (the "License"); you
# may not use this file except in compliance with the License.  You
# may obtain a copy of the License at:
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""Config objects to control the web app."""

from google.appengine.ext import db

class _TextConfig(db.Model):
    """Data store object to contain the config."""
    last_modified_date = db.DateTimeProperty(auto_now=True)
    date_added = db.DateTimeProperty(auto_now_add=True)    
    value = db.StringProperty()

# TODO(napier): need some way to set things

class _StringConfig(object):
    def __init__(self, name, default_value=''):
        self.value = _TextConfig.get_or_insert(name, value=default_value)

    def get(self):
        return self.value.value

class _IntConfig(object):
    def __init__(self, name, default_value=0):
        self.value = _TextConfig.get_or_insert(name, value=str(default_value))

    def get(self):
        return int(self.value.value)

class _BoolConfig(object):
    def __init__(self, name, default_value=False):
        self.value = _TextConfig.get_or_insert(name, value=str(default_value))

    def get(self):
        return self.value.value == 'True'


# The API Key to pass to NPR api server
NPR_API_KEY = _StringConfig('npr_api_key', '')

# The API node to list shows
NPR_SHOW_LIST_ID = _StringConfig('npr_show_list_id', '3004')

# The hostname for the NPR api server
NPR_API_HOSTNAME = _StringConfig('npr_api_hostname', 'api.npr.org')

# The show ID for 'Fresh Air'
FRESH_AIR_ID = _StringConfig('fresh_air_id', '13')

# The number of stories to try and fetch in each task execution. Note
# that the API maxes out at 20 stories.
NUM_STORIES_TO_FETCH = _IntConfig('num_stories_to_fetch', 20)

# Whether the tasks to parse the XML should be schedule immediately on
# completion of fetch.
AUTO_PARSE_XML = _BoolConfig('auto_parse_xml', True)

# True indicates that a fetch_xml request should try and keep fetching
# stories to backfill the stories datastore.  Should be kept in True
# for production, but useful to set to False for debugging.
AUTO_FETCH_STORIES = _BoolConfig('auto_fetch_stories', True)

# How long to wait after a fetch until the next one begins (in
# seconds)
AUTO_FETCH_DELAY_SEC = _IntConfig('auto_fetch_delay_sec', 30)

RECENT_STORIES_COUNT = _IntConfig('recent_stories_count', 10)

# The number of stories to get from the datastore to hand to each
# parse task.
REPARSE_TASK_SIZE = _IntConfig('reparse_task_size', 30)

# If we should serve the compiled JS files or not.  Defaults to False
# for easier debuggi.
JS_COMPILED = _BoolConfig('js_compiled', False)

# True to have a story page, false to just redirect to the NPR page.
HAVE_STORY_PAGE = _BoolConfig('have_story_page', False)
