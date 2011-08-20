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

"""Data storage model classes."""

from google.appengine.ext import db
from google.appengine.ext.db import polymodel

### 3 different model types, all in the same entity group.  Since we
### see the FullStory first, we'll make that the parent of the entity
### group.  StoryPreview contains all the parsed data that may be
### needed to render a preview of the story.  This will probably
### include all the metadata, the title, and abstract, etc.
###
### Story contains all the parsed metadata and is a bit more
### heavyweight than StoryPreview.  FullStory just contains the
### unparsed XML.
###
### The idea here is that we always want to keep the unparsed XML
### around at all times so we can possibly re-parse the data later as
### the XML parser gets improved (fixes bugs, parses more data, etc.),
### but that's the only time that datastore object is used, so it's a
### waste to fetch it for pages that won't render it.  In the same
### vein, we may be rendering a lot of story previews on a single
### page, so we make them as small as possible so we can get them
### quickly.

class StoryBase(polymodel.PolyModel):
    """Base class for all story data objects."""
    last_modified_date = db.DateTimeProperty(auto_now=True)
    date_added = db.DateTimeProperty(auto_now_add=True)
    
    # This may be a dupe of the key, but easier to get at
    id = db.StringProperty()

class FullStory(StoryBase):
    """The unmparsed XML."""
    xml = db.TextProperty()

# The class hierarcy here is kinda odd.  A typical hierarch would look
# like this:
#   StoryBase -> StoryPreview -> Story
# Due to PolyModel's implementation, this makes it impossible to query
# for just StoryPreviews, which defeats the purpose.

class ParsedStoryBase(StoryBase):
    xml_parser_version = db.IntegerProperty()

    title = db.StringProperty()

    # We handle dates by parsing the full date, an then breaking out
    # the year, and the year/month for indexing.
    story_date = db.DateTimeProperty()
    story_year = db.IntegerProperty()
    story_yearmonth = db.IntegerProperty()
    
    publish_date = db.DateTimeProperty()
    publish_year = db.IntegerProperty()
    publish_yearmonth = db.IntegerProperty()

    thumbnail_large = db.StringProperty()
    thumbnail_medium = db.StringProperty()
    thumbnail_small = db.StringProperty()

    @property
    def has_thumbnail(self):
        return self.preferred_thumbnail != None

    @property
    def preferred_thumbnail(self):
        if self.thumbnail_large != None:
            return self.thumbnail_large
        if self.thumbnail_medium != None:
            return self.thumbnail_medium
        if self.thumbnail_small != None:
            return self.thumbnail_small
        return None

    teaser = db.TextProperty()
    short_teaser = db.TextProperty()

    @property
    def has_teaser(self):
        return self.short_teaser != None or self.teaser != None

    @property
    def preferred_teaser(self):
        if self.short_teaser != None:
            return self.short_teaser
        if self.teaser != None:
            return self.teaser        
        return ''

    topics = db.StringListProperty()

    @property
    def all_topics(self):
        ret = set(self.topics)
        ret.add(self.primary_topic)
        return list(ret)
    
    primary_topic = db.StringProperty()

    @property
    def has_column(self):
        return self.column != None
    
    column = db.StringProperty()

    @property
    def has_collection(self):
        return self.collection != None
    
    collection = db.StringProperty()

    story_url = db.LinkProperty()
    
    
class StoryPreview(ParsedStoryBase):
    # This should never add any additional properties
    pass

class Story(ParsedStoryBase):
    text = db.TextProperty()
    text_with_html = db.TextProperty()


