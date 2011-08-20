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

import logging
import urllib
import urlparse
import xml.etree.ElementTree as et

from google.appengine.ext import db
from google.appengine.ext.db import Query
from google.appengine.ext.db import Key
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import memcache
from google.appengine.api import taskqueue

import bindex
import config
import model
import story_parser

_BINDEXED_FIELDS = [
    'story_year',
    'story_yearmonth',    
    'publish_year',
    'publish_yearmonth',
    'primary_topic',
    'column',
    'collection',
    'topics'
    ]

def _parse_bool(input):
    return input.lower() == 'true'

def _parse_int(input):
    return int(input)

def _fetch_xml(offset, count, force=False):
    taskqueue.add(url='/backend/fetch_xml',
                  queue_name='fetch-queue',
                  countdown=config.AUTO_FETCH_DELAY_SEC.get(),
                  params=dict(force=force,
                              offset=offset,
                              count=count))

def _parse_stories(ids):
    # Schedule a task to parse all these id's.  For now, just put all
    # of them (at most 20) into a single task.  This should help keep
    # the queue size down.
    
    # Encode the ids into something that can be passed via url
    id_param = ','.join(ids)
    
    taskqueue.add(url='/backend/parse_xml',
                  queue_name='parse-queue',
                  # We put a delay here because otherwise this queue
                  # seems to eat all the CPU.  Hoping this will fix
                  # it.
                  countdown=config.AUTO_FETCH_DELAY_SEC.get(),                  
                  params=dict(ids=id_param,
                              task=True))

class FetchAll(webapp.RequestHandler):
    def get(self):
        force_refresh = _parse_bool(self.request.get('force', 'False'))

        # Schedule the first task.  The NPR API always starts with 1
        _fetch_xml(offset=1,
                   count=config.NUM_STORIES_TO_FETCH.get(),
                   force=force_refresh)

        # Return success
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('OK')


def _build_api_url(path, query_map):
    query = urllib.urlencode(query_map)
    return urlparse.urlunparse(['http', config.NPR_API_HOSTNAME.get(), path, '', query, ''])

def _retrieve_url(url):
    try:
        f = urllib.urlopen(url)
        res = f.read()
        f.close()
        return res
    except:
        return None

class NoMoreStories(Exception):
    pass

def _query_stories_for_show(show_id, api_key, start_num, num_results=20):
    url = _build_api_url('query', dict(startNum=start_num,
                                      numResults=num_results,
                                      id=show_id,
                                      apiKey=api_key))
    logging.info('Getting API results from URL %s'  % url)
    
    data = _retrieve_url(url)
    if data == None:
        logging.error('error trying to fetch: %s' % url)
        return []
    
    try:
        doc = et.fromstring(data)
    except:
        logging.error('Unable to parse data for request')
        return []

    # The API will return message 401 when we're done.
    messages = doc.findall('message')
    for message in messages:
        if message.attrib['id'] == '401':
            raise NoMoreStories()
    
    # Return all the stories as et nodes
    return doc.findall('list/story')

class FetchXml(webapp.RequestHandler):
    def get(self):
        self._handle()
        
    def post(self):
        self._handle()

    def _handle(self):
        force_refresh = _parse_bool(self.request.get('force', 'False'))
        offset = _parse_int(self.request.get('offset'))
        count = _parse_int(self.request.get('count'))

        logging.info('FetchXml: %d/%d' % (offset, count))

        try:
            stories = _query_stories_for_show(config.FRESH_AIR_ID.get(),
                                              config.NPR_API_KEY.get(),
                                              start_num=offset,
                                              num_results=count)
        except NoMoreStories:
            logging.warning('API returned error indicating at end of stories.')

            # Return success
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('OK')
            return

        full_stories = []
        done = False
        story_stored = False
        for story in stories:
            # Create a FullStory object and commit it
            id = story.attrib['id']

            if not force_refresh:
                # See if we already have this id
                q = Query(model.FullStory, keys_only=True)
                q.filter('id ==', id)
                
                if q.get() is None:
                    # New id
                    logging.info('Putting storyid %s into datastore' % id)
                
                    full_stories.append(model.FullStory(key_name=id,
                                                        id=id,
                                                        xml=et.tostring(story)))

                    # And signal that something was stored
                    story_stored = True                                    
            else:
                # Force refresh, always put
                logging.info('Putting storyid %s into datastore' % id)
                
                full_stories.append(model.FullStory(key_name=id,
                                                    id=id,
                                                    xml=et.tostring(story)))
                # And signal that something was stored
                story_stored = True                


        # store them all in bulk
        if len(full_stories) != 0:
            db.put(full_stories)

            if config.AUTO_PARSE_XML.get():
                _parse_stories([story.attrib['id'] for story in stories])        

        if story_stored:
            # this means we stored something, so keep going
            new_offset = offset + count
            logging.info('Keep going! %s/%d' % (new_offset, count))

            _fetch_xml(offset=new_offset,
                       count=config.NUM_STORIES_TO_FETCH.get(),
                       force=force_refresh)
        else:
            # We're at the end, let's flush the cache
            memcache.flush_all()

        # Return success
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('OK')        

def _parse_id_param(ids):
    if ids is None:
        return []
    return ids.split(',')

class ParseXml(webapp.RequestHandler):
    def get(self):
        self._handle()
    def post(self):
        self._handle()

    def _handle(self):
        ids = _parse_id_param(self.request.get('ids'))

        if len(ids) == 0:
            logging.error('Got no ids, stopping')
            # Return success
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('OK')            
            return

        # Bulk get all stories
        stories = model.FullStory.get_by_key_name(ids)

        for (id, full_story) in zip(ids, stories):
            if full_story is None:
                logging.info('Story %s could not be found' % id)
                continue
                
            logging.info('Going to parse id %s' % id)

            (parsed_story, preview) = story_parser.parse_full_story(full_story.xml,
                                                                    full_story)

            # Need to store these together in the same transaction
            db.run_in_transaction(lambda x,y: db.put([x, y]),
                                  parsed_story, preview)

            # Also bindex some useful fields
            bindex.index(parsed_story, _BINDEXED_FIELDS)
            bindex.index(preview, _BINDEXED_FIELDS)            
        
        # Return success
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('OK')

class ReparseXml(webapp.RequestHandler):
    def get(self):
        self._handle()
    def post(self):
        self._handle()

    def _handle(self):
        in_task = _parse_bool(self.request.get('task', 'False'))
        cursor = self.request.get('cursor', None)

        if not in_task:
            logging.info('Request to reparse found, posting a task.')
            
            # Post a new task to ourselves
            taskqueue.add(url='/backend/reparse_xml',
                          queue_name='parse-queue',
                          params=dict(task=True))

            # Return success
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('OK')
            return

        logging.info('Reparsing in task, cursor is %s' % cursor)
                    
        # Pull all the stories
        q = Query(model.FullStory, keys_only=True)

        if cursor is not None:
            q.with_cursor(cursor)

        # Only fetch a limited number of stories here. We'll handle
        # the rest in a later task.
        task_size = config.REPARSE_TASK_SIZE.get()
        stories = q.fetch(task_size)
        cursor = q.cursor()

        # do to PolyModel, we get duplicate id's here. Use set to kill
        # them
        ids = list(set([story.name() for story in stories]))

        if len(ids) == 0:
            # Bail
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('OK')

            # and flush the cache
            memcache.flush_all()            
            return

        logging.info('Handling stories %s' % ids)            

        # And have them all parsed (in another task as well)
        _parse_stories(ids)

        # New task to parse the rest
        taskqueue.add(url='/backend/reparse_xml',
                      queue_name='parse-queue',
                      params=dict(task=True,
                                  cursor=cursor))        
        
        # Return success
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('OK')    
            

application = webapp.WSGIApplication([('/backend/fetch_all', FetchAll),
                                      ('/backend/fetch_xml', FetchXml),
                                      ('/backend/reparse_xml', ReparseXml),                                      
                                      ('/backend/parse_xml', ParseXml)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
