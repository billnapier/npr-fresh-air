#!/usr/bin/python

# Module use to setup appengine tests.  Parses arguments and sets up
# the path to ensure everything can be found

import sys
import unittest

appengine_sdk_path = sys.argv[1]
code_path = sys.argv[2]


# muck with the path
sys.path.insert(0, appengine_sdk_path)
sys.path.insert(0, appengine_sdk_path + '/lib/webob')
sys.path.insert(0, appengine_sdk_path + '/lib/yaml/lib')

sys.path.insert(0, code_path)

def main(name):
    unittest.TestProgram(argv=[name])
