// Copyright (C) 2011 by Bill Napier (napier@pobox.com)
//
// Licensed under the Apache License, Version 2.0 (the "License"); you
// may not use this file except in compliance with the License.  You
// may obtain a copy of the License at:
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
// implied.  See the License for the specific language governing
// permissions and limitations under the License.

goog.provide('billnapier.nprfreshair.main');

goog.require('goog.ui.AnimatedZippy');
goog.require('goog.ui.Zippy');
goog.require('goog.ui.ZippyEvent');

function define_zippy(name) {
  return new goog.ui.Zippy(name + '_filter', name + '_content');
}

// Every page has it's main function
function main() {
  var year_zip = define_zippy('year');
  var month_zip = define_zippy('month');
  var topic_zip = define_zippy('topic');
  var collection_zip = define_zippy('collection');
}
