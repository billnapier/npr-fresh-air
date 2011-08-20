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

from google.appengine.api import memcache

from datetime import datetime

import model

def get_recent_stories(count):
    mc_key = 'recent_stories:' + str(count)
    results = memcache.get(mc_key)
    if results != None:
        return results
    
    # TODO(napier): memcache
    q = model.StoryPreview.all()
    q.order('-publish_date')

    # TODO(napier): figure out how to change to run instead and then
    # truncate the iterable (should be async)
    results = q.fetch(limit=count)
    memcache.set(mc_key, results)
    return results

def get_story_by_id(id):
    mc_key = 'story_by_id:' + str(id)
    results = memcache.get(mc_key)
    if results != None:
        return results
    
    q = model.Story.all()
    q.filter('id =', id)
    # Only one, so use get
    results = q.get()
    memcache.set(mc_key, results)
    return results    

_MONTHS = map(lambda x: datetime(year=1990, month=x, day=1).strftime("%B"),
              range(1, 13))

def _month_to_monum(month):
    for x in range(0, 12):
        if _MONTHS[x] == month:
            return x + 1
    return 0

def get_stories_with_filter(topic=None,
                            year=None,
                            month=None,
                            collection=None,
                            count=10):

    mc_key = ':'.join([x for x in ['stories_with_filter', topic, year,
                           month, collection, str(count)] if x != None])
    results = memcache.get(mc_key)
    if results != None:
        return results
    
    q = model.Story.all()
    q.order('-publish_date')
    if topic != None:
        # Need to figure out how to handle primary topic
        q.filter('topics =', topic)
    if collection != None:
        q.filter('collection =', collection)

    if year != None and month == None:
        q.filter('publish_year =', int(year))
    if year != None and month != None:
        yearmo = (int(year) * 100) + _month_to_monum(month)
        q.filter('publish_yearmonth =', yearmo)        
    results = q.fetch(count)
    memcache.set(mc_key, results)
    return results 
