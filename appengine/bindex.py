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
from google.appengine.ext import db

class _BIndex(db.Expando):
    refs = db.ListProperty(db.Key)
    count = db.IntegerProperty()

def _is_not_property_empty(obj, prop):
    obj_properties = obj.properties()
    return prop in obj_properties and not obj_properties[prop].empty(obj.__getattribute__(prop))

def _calc_key_name(key, value):
    return '='.join(map(str, [key, value]))    

def index(obj, properties):
    key = obj.key()

    entries = []
    for prop in properties:
        if _is_not_property_empty(obj, prop):
            obj_properties = obj.properties()

            attrs = [obj.__getattribute__(prop)]

            # Special case for handling string lists.
            if isinstance(obj_properties[prop], db.StringListProperty):
                attrs = obj.__getattribute__(prop)

            for attr in attrs:
                key_name = _calc_key_name(prop, attr)
                # Look up the _BIndex entry using prop as the key
                entry = _BIndex.get_by_key_name(key_name)
                if entry == None:
                    # Create a new entry
                    entry =_BIndex(key_name=key_name)
                
                    # Add  an expando key for this property
                    entry.__setattr__(prop, attr)

                # Link to this document (if not already linked).
                if key not in entry.refs:
                    entry.refs.append(key)

                # Update the count
                entry.count = len(entry.refs)

                # Put this in the list of things we'll store at the end.
                entries.append(entry)

    # Bulk store the new _BIndex values
    db.put(entries)


# TODO(napier): would be nice to have a DSL here to specify more
# complex queries.  Like 'foo = bar AND baz = quux'.

class _BIndexQuery(object):
    def __init__(self, iterator):
        self.items = list(iterator)
    
    def count(self):
        return sum([i.count for i in self.items])

    def run(self):
        for i in self.items:
            for r in i.refs:
                yield r

def query(field, value, operator='='):
    mc_key = ':'.join(map(str, ['bindex_query', field, value, operator]))
    results = memcache.get(mc_key)
    if results != None:
        return _BIndexQuery(results)
        
    # Shortcut for '=' operator
    if '=' == operator:
        # Shortcut
        item = _BIndex.get_by_key_name(_calc_key_name(field, value))
        if item == None:
            return _BIndexQuery([])
        else:
            memcache.set(mc_key, [item])
            return _BIndexQuery([item])


    q = _BIndex.all()
    q.filter(' '.join([field, operator]), value)
    # Uhh, this will someday cause a problem (though probably not in
    # this app).  Once the size of the results exceeds the size of the
    # memcahce entry size things are going to start breaking.
    results = q.fetch(1000)
    memcache.set(mc_key, results)    
    return _BIndexQuery(results)


class _BIndexListValueReturn(object):
    def __init__(self, prop, items):
        self.prop = prop
        self.items = list(items)

    def list(self):
        return [i.__getattribute__(self.prop) for i in self.items]

    def counts(self):
        res = {}
        for i in self.items:
            res[i.__getattribute__(self.prop)] = i.count
        return res

def list_values(property):
    q = _BIndex.all()
    q.filter('%s !=' % property, 'NULL')
    return _BIndexListValueReturn(property, q.run())


