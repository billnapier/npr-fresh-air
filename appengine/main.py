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

from datetime import date
from datetime import datetime
import logging
import os
from urlparse import urlparse
from urlparse import urlunparse
import urllib

from google.appengine.dist import use_library
use_library('django', '1.2')
    
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import bindex
import closure
import config
import model
import queries

_MONTHS = map(lambda x: datetime(year=1990, month=x, day=1).strftime("%B"),
              range(1, 13))

def _build_page_title(subtitle):
    return 'Fresh Air - %s' % subtitle

def _get_default_template_params(req, overrides):
    if config.JS_COMPILED.get():
        js_compiled='_compiled'
    else:
        js_compiled=''
    
    parsed_url = urlparse(req.url)
    home_url = urlunparse([parsed_url.scheme,
                           parsed_url.netloc,
                           '', '', '', ''])
    overrides.update(dict(canonical_url=req.url,
                          js_compiled=js_compiled,
                          home_url=home_url))
    return overrides

class FilterWrapper(object):
    def __init__(self, name, arg_name, req):
        self.name = name
        query_params = {}
        for arg in req.arguments():
            value = req.get(arg, None)
            if value != None:
                query_params[arg] = value

        # Overwrite any old value with the new one
        query_params[arg_name] = name           

        # Re-build the URL
        q = urllib.urlencode(query_params)
        parsed_url = urlparse(req.url)
        self.url = urlunparse([parsed_url.scheme,
                               parsed_url.netloc,
                               '', '', q, ''])        
        

class MainPage(webapp.RequestHandler):
    def get(self):
        columns = [FilterWrapper(i, 'column', self.request) for i
                   in bindex.list_values('column').list()]
        collections = [FilterWrapper(i, 'collection', self.request) for i
                       in bindex.list_values('collection').list()]
        topics = [FilterWrapper(i, 'topic', self.request) for i
                  in bindex.list_values('topics').list()]
        years = [FilterWrapper(i, 'year', self.request) for i
                 in bindex.list_values('publish_year').list()]
        
        path = os.path.join(os.path.dirname(__file__),
                            'templates', 'main.html')

        if len(self.request.arguments()) == 0:
            # Stories are recent stories
            stories = queries.get_recent_stories(config.RECENT_STORIES_COUNT.get())
        else:
            # parse arguments
            topic = self.request.get('topic', None)
            year = self.request.get('year', None)            
            collection = self.request.get('collection', None)
            month = self.request.get('month', None)

            stories = queries.get_stories_with_filter(topic=topic,
                                                      year=year,
                                                      collection=collection,
                                                      month=month)

        months = [FilterWrapper(i, 'month', self.request) for i in _MONTHS]
        
        self.response.out.write(template.render(path,
                                                _get_default_template_params(self.request,
                                                                             dict(page_title='Fresh Air',
                                                                                  stories=stories,
                                                                                  columns=columns,
                                                                                  collections=collections,
                                                                                  topics=topics,
                                                                                  years=years,
                                                                                  months=months,
                                                                                  ))))
        
class StoryPage(webapp.RequestHandler):
    def get(self):
        id = self.request.get('id', None)
        if id is None:
            logging.error('Got request missing parameters: %s' % id)
            self.error(404)
            return

        story = queries.get_story_by_id(id)

        if not config.HAVE_STORY_PAGE.get():
            self.redirect(story.story_url, True)
            return
        
        page_title = _build_page_title(story.title)
        path = os.path.join(os.path.dirname(__file__),
                            'templates', 'story.html')        
        self.response.out.write(template.render(path,
                                                _get_default_template_params(self.request,
                                                                             dict(story=story,
                                                                                  page_title=page_title))))
    
application = webapp.WSGIApplication([('/', MainPage),
                                      ('/story', StoryPage),
                                      ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
