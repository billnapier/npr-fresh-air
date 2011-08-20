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

import unittest

import test_setup

from google.appengine.ext import testbed

class FakeRequest(object):
    def __init__(self, params={}):
        self.params = {
            'Content-Type': 'text/html'
            }
        self.params.update(params)
        
    def get(self, param, default=None):
        if param in self.params:
            return self.params[param]
        return default

class FakeResponseOut(object):
    def write(self, out):
              pass

class FakeResponse(object):
    def __init__(self):
        self.headers = {}
        self.out = FakeResponseOut()

class TestBackend(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.setup_env(app_id='npr-fresh-air')
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()                
        self.testbed.init_taskqueue_stub(_all_queues_valid=True)

    def testIncremenalTest(self):
        import backend

        req = FakeRequest(dict(force='False'))
        resp = FakeResponse()
        
        fetch_all = backend.FetchAll()
        fetch_all.initialize(req, resp)
        fetch_all.get()

        taskqueue_stub = self.testbed.get_stub('taskqueue')
        queues = taskqueue_stub.GetQueues()

        # Ensure that there is a task queued
        fetch_queue = taskqueue_stub.GetTasks('fetch-queue')
        self.assertEquals(1, len(fetch_queue))

if __name__ == '__main__':
    test_setup.main('backend')
