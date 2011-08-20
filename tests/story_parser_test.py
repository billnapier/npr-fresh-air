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

import datetime
import sys
import unittest

import xml.etree.ElementTree as et

import test_setup

from google.appengine.ext import testbed

import model
import story_parser

class TestSequenceFunctions(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env(app_id='npr-fresh-air')
        self.testbed.activate()        
        self.testbed.init_datastore_v3_stub()        
    
    def test_parse_datetime(self):
        when = 'Thu, 23 Jun 2011 11:02:04 -0400'
        dt = story_parser._parse_into_datetime(when)
        self.assertEquals(2011, dt.year)
        self.assertEquals(6, dt.month)
        self.assertEquals(23, dt.day)
        self.assertEquals(11, dt.hour)
        self.assertEquals(2, dt.minute)
        self.assertEquals(4, dt.second)

        utc = dt.utctimetuple()
        self.assertEquals(15, utc.tm_hour)

    def test_datetime_into_year(self):
        when = datetime.datetime(2011, 4, 4, 13, 27, 30)
        self.assertEqual(2011,
                         story_parser._parse_datetime_into_year(when))

    def test_datetime_into_yearmonth(self):
        when = datetime.datetime(2011, 4, 4, 13, 27, 30)
        self.assertEqual(201104,
                         story_parser._parse_datetime_into_yearmonth(when))

    def test_parse_story(self):
        fp = open('tests/story.xml')
        story_xml = fp.read()
        fp.close()
        parent = model.FullStory(key_name='0', id='0', xml='')
        (preview, parsed_story) = story_parser.parse_full_story(story_xml, parent)

        self.assertEquals('http://media.npr.org/assets/img/2011/06/23/badteaching_sq.jpg?t=1308930266&s=13',
                          preview.thumbnail_medium)
        self.assertEquals('http://media.npr.org/assets/img/2011/06/23/badteaching_sq.jpg?t=1308930266&s=13',
                          parsed_story.thumbnail_medium)
        self.assertEquals('http://media.npr.org/assets/img/2011/06/23/badteaching_sq.jpg?t=1308930266&s=11',
                          preview.thumbnail_large)
        self.assertEquals('http://media.npr.org/assets/img/2011/06/23/badteaching_sq.jpg?t=1308930266&s=11',
                          parsed_story.thumbnail_large)        

        self.assertEquals('http://media.npr.org/assets/img/2011/06/23/badteaching_sq.jpg?t=1308930266&s=11',
                          preview.preferred_thumbnail)
        self.assertEquals('http://media.npr.org/assets/img/2011/06/23/badteaching_sq.jpg?t=1308930266&s=11',
                          parsed_story.preferred_thumbnail)

        self.assertEquals('Critic David Edelstein says that the film\'s moral turpitude is also the source of its charm.',
                          preview.short_teaser)
        self.assertEquals('Critic David Edelstein says that the film\'s moral turpitude is also the source of its charm.',
                          parsed_story.short_teaser)        
        

        self.assertEquals(('How bad is this teacher? Director Jake Kasdan stuffs ineptness '
                          'and inappropriateness into the lesson plan in equal measure. But '
                          'critic David Edelstein says that the film\'s moral turpitude is '
                          'also the source of its charm.'),
                          preview.teaser)
        self.assertEquals(('How bad is this teacher? Director Jake Kasdan stuffs ineptness '
                          'and inappropriateness into the lesson plan in equal measure. But '
                          'critic David Edelstein says that the film\'s moral turpitude is '
                          'also the source of its charm.'),
                          parsed_story.teaser)

        self.assertEquals('Fresh Air Reviews', preview.collection)
        self.assertEquals('Fresh Air Reviews', parsed_story.collection)

        self.assertEquals('Movie Reviews', preview.column)
        self.assertEquals('Movie Reviews', parsed_story.column)

        self.assertEquals('Movies', preview.primary_topic)
        self.assertEquals('Movies', parsed_story.primary_topic)

        expected_results = ['Movies', 'Arts & Life']
        for topic in preview.topics:
            self.assertTrue(topic in expected_results)
        for topic in parsed_story.topics:
            self.assertTrue(topic in expected_results)

        self.assertEquals('http://www.npr.org/2011/06/24/137378586/class-is-dismissed-bad-teacher-is-crude-but-fun?ft=3&f=13',
                          preview.story_url)
        self.assertEquals('http://www.npr.org/2011/06/24/137378586/class-is-dismissed-bad-teacher-is-crude-but-fun?ft=3&f=13',
                          parsed_story.story_url)
        
                        

if __name__ == '__main__':
    test_setup.main('story_parser')

