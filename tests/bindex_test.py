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

import sys
import unittest

import test_setup

from google.appengine.ext import db
from google.appengine.ext import testbed

import bindex

def _get_first(iter):
    for i in iter:
        return i
    return None

class TestObject(db.Model):
    s = db.StringProperty()
    i = db.IntegerProperty()
    str_list = db.StringListProperty()

_PROPERTIES = ['s','i', 'str_list']

class TestBindex(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env(app_id='npr-fresh-air')
        self.testbed.activate()        
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        obj1 = TestObject(key_name='key_name1', s='string',
                          i=7, str_list=['baz'])
        db.put(obj1)

        obj2 = TestObject(key_name='key_name2', s='string',
                          str_list=['quux'])
        db.put(obj2)

        obj3 = TestObject(key_name='key_name3', s='no',
                          str_list=['foo', 'bar', 'baz'])

        # Index obj
        bindex.index(obj1, _PROPERTIES)
        # Even though i doesn't exist in obj2, this should not fail.
        bindex.index(obj2, _PROPERTIES)
        # And #3
        bindex.index(obj3, _PROPERTIES)
        # Re-index obj (this should be a noop)
        bindex.index(obj1, _PROPERTIES)

    def testQeury_stringList(self):
        res = bindex.query('str_list', 'foo').run()
        obj = _get_first(res)
        self.assertEquals('key_name3', obj.name())

        res = bindex.query('str_list', 'bar').run()
        for r in res:
            self.assertTrue(r.name() in ['key_name1', 'key_name3'])        


    def testListValues(self):
        res = bindex.list_values('s')
        values = res.list()
        expected_values = ['string', 'no']
        self.assertEquals(len(expected_values), len(values))

        for v in values:
            self.assertTrue(v in expected_values)

        self.assertEquals(2, res.counts()['string'])
        self.assertEquals(1, res.counts()['no'])        

    def testIndex(self):
        i = bindex._BIndex.all().filter('i =', 7).get()
        self.assertEquals(1, len(i.refs))

    def testStringListIndex(self):
        res = list(bindex._BIndex.all().filter('str_list !=', 'NULL').run())
        self.assertEquals(4, len(res))
        
    def testQuery(self):
        res = bindex.query('s', 'string').run()
        for r in res:
            self.assertTrue(r.name() in ['key_name1', 'key_name2'])

        res = bindex.query('i', 7).run()
        obj = _get_first(res)
        self.assertEquals('key_name1', obj.name())

    def testQuery_notFound(self):
        res = bindex.query('s', 'not_here').run()
        for r in res:
            self.fail('should be empty')

        res = bindex.query('i', 'wrongtype').run()
        for r in res:
            self.fail('should be empty')

        res = bindex.query('i', 0).run()
        for r in res:
            self.fail('should be empty')

        res = bindex.query('no_field', 'not_here').run()
        for r in res:
            self.fail('should be empty')

    def testQuery_comparison(self):
        q = bindex.query('i', 1, operator='>')
        self.assertEquals(1, q.count()) 
        obj = _get_first(q.run())
        self.assertEquals('key_name1', obj.name())

        # And test the opposite
        q = bindex.query('i', 10, operator='>')
        self.assertEquals(0, q.count())
        for r in q.run():
            self.fail('should be empty')
                        

if __name__ == '__main__':
    test_setup.main('bindex')
