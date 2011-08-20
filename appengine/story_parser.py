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

import time
from datetime import datetime
from datetime import tzinfo
from datetime import timedelta
import xml.etree.ElementTree as et

import model

_XML_PARSER_VERSION = 1

ZERO = timedelta(0)
class FixedOffset(tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset, name):
        self.__offset = timedelta(minutes=offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return ZERO

# who would have thought this would have been so much work
def _parse_into_datetime(input):
    # Pull out GMT offset
    gmt_offset = input[-5:]
    gmt_sign = gmt_offset[0]
    gmt_offset = gmt_offset[1:]
    gmt_offset_minute = int(gmt_offset[-2:])
    gmt_offset_hour = int(gmt_offset[:-2])

    # Make GMT sign into a +1 or -1
    gmt_sign = int(gmt_sign + '1')

    # Adjust input
    input = input[:-5].rstrip().lstrip()

    tz = FixedOffset(((gmt_offset_hour * 60) + gmt_offset_minute) * gmt_sign,
                     name=gmt_offset)

    dt = datetime.strptime(input, '%a, %d %b %Y %H:%M:%S')

    return datetime(year=dt.year,
                    month=dt.month,
                    day=dt.day,
                    hour=dt.hour,
                    minute=dt.minute,
                    second=dt.second,
                    tzinfo=tz)    

def _parse_datetime_into_year(dt):
    return dt.year

def _parse_datetime_into_yearmonth(dt):
    # This code will break in appox 8000 years. I think we'll be OK
    return (dt.year * 100) + dt.month

def parse_full_story(full_story_xml, full_story):
    story = et.fromstring(full_story_xml)
    id = story.attrib['id']    
    title = story.find('title').text
    
    story_date = _parse_into_datetime(story.find('storyDate').text)
    story_year = _parse_datetime_into_year(story_date)
    story_yearmonth = _parse_datetime_into_yearmonth(story_date)
    
    pub_date = _parse_into_datetime(story.find('pubDate').text)
    pub_year = _parse_datetime_into_year(pub_date)
    pub_yearmonth = _parse_datetime_into_yearmonth(pub_date)

    thumbnail_large = story.find('thumbnail/large')
    if thumbnail_large is not None:
        thumbnail_large = thumbnail_large.text
    thumbnail_medium = story.find('thumbnail/medium')
    if thumbnail_medium is not None:
        thumbnail_medium = thumbnail_medium.text    
    thumbnail_small = story.find('thuombnail/small')
    if thumbnail_small is not None:
        thumbnail_small = thumbnail_small.text

    teaser = story.find('teaser').text
    short_teaser = story.find('miniTeaser').text

    story_url = ''
    for link in story.findall('link'):
        if link.attrib['type'] == 'html':
            story_url = link.text
            

    # Parse parents into topics and stuff
    collection = None
    topics = set([])
    primary_topic = None
    column = None
    
    for parent in story.findall('parent'):
        type = parent.attrib['type']
        value = parent.find('title').text
        if 'topic' == type:
            topics.add(value)
        if 'column' == type:
            column = value
        if 'collection' == type:
            collection = value
        if 'primaryTopic' == type:
            primary_topic = value

    preview = model.StoryPreview(key_name=id,
                                 parent=full_story,
                                 id=id,
                                 title=title,
                                 story_date=story_date,
                                 story_year=story_year,
                                 story_yearmonth=story_yearmonth,
                                 publish_date=pub_date,
                                 publish_year=pub_year,
                                 publish_yearmonth=pub_yearmonth,
                                 thumbnail_large = thumbnail_large,
                                 thumbnail_medium = thumbnail_medium,
                                 thumbnail_small = thumbnail_small,
                                 teaser=teaser,
                                 short_teaser=short_teaser,
                                 collection=collection,
                                 column=column,
                                 primary_topic=primary_topic,
                                 topics=list(topics),
                                 story_url=story_url,
                                 xml_parser_version=_XML_PARSER_VERSION)
    parsed_story = model.Story(key_name=id,
                               parent=preview,                               
                               id=id,
                               title=title,
                               story_date=story_date,
                               story_year=story_year,
                               story_yearmonth=story_yearmonth,
                               publish_date=pub_date,
                               publish_year=pub_year,
                               publish_yearmonth=pub_yearmonth,
                               thumbnail_large = thumbnail_large,
                               thumbnail_medium = thumbnail_medium,
                               thumbnail_small = thumbnail_small,
                               teaser=teaser,
                               short_teaser=short_teaser,
                               collection=collection,
                               column=column,
                               primary_topic=primary_topic,
                               topics=list(topics),
                               story_url=story_url,                               
                               # TODO(napier): fill these out
                               text='',
                               text_with_html='',
                               xml_parser_version=_XML_PARSER_VERSION)

    return (preview, parsed_story)
