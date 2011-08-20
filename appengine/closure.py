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

from django.utils import simplejson as json
from google.appengine.ext import webapp

import closure_html

class ClosureHandler(webapp.RequestHandler):
    def __init__(self, title, filename, funcname):
        self.title = title
        self.filename = filename
        self.funcname = funcname

    def _replace_data(self, input, data):
        input = input.replace('{{page_title}}', self.title)
        input = input.replace('{{funcname}}', self.funcname)
        input = input.replace('{{filename}}', self.filename)
        input = input.replace('{{data}}', data)
        return input

    def get_data(self):
        """Called during render to get data to show."""
        return {'a': 1, 'b': 2}
        
    def get(self):
        data = self.get_data()
        if data == None:
            data = ''
        else:
            data = json.dumps(data)

        self.response.out.write(self._replace_data(closure_html.TEMPLATE, data))

