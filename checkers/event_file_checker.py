###############################################################################
# (c) Copyright 2022 CERN for the benefit of the LHCb Collaboration           #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
import sys

'''checker for syntax of Phoenix event file format'''

class PhoenixFormatError(Exception):
    '''Main exception thrown in case of bad format'''
    def __init__(self, msg):
        self.message = msg

def genericCheck(j, d, objName, objType):
    '''
    generic checker of the structure of a json object j

    d is a dictionnary describing what to check.
    Each entry is a potential key of the j object associated to
    a pair of values : (isOpt, checker)
    where isOpt is a boolean saying whether this entry is optional
    or not and checker is a function which will be called to check
    the syntax of the entry's value

    objName and objType are strings describing object j for logging
    '''
    # j should be an object
    if not isinstance(j, dict):
        raise PhoenixFormatError(
            "Expected %s to be dictionaries. Not the case for %s" % (objType, objName))
    # go through the entries to check
    for key in d:
        isOpt, checker = d[key]
        # check presence of mandatory entries
        if not isOpt and key not in j:
            raise PhoenixFormatError("Expected a '%s' attribute in %s" % (key, objName))
        if key in j:
            checker(j[key], objName + ", attribute '" + key + "'")

def genericTypeCheck(j, objName, typ):
    '''Checks that the object has the given type'''
    if not isinstance(j, typ):
        raise PhoenixFormatError(
            'Expected the %s to be of type "%s", found %s' % (objName, typ.__name__, type(j).__name__))

def noCheck(j, name):
    ''' no checking anything !'''
    return
    
def floatCheck(j, name):
    '''Checks that the object is a float'''
    if not isinstance(j, float) and not isinstance(j, int):
        raise PhoenixFormatError(
            'Expected the %s to be of type float or int, found %s' % (name, type(j).__name__))

def colorAttributeCheck(j, name):
    '''Checks that the object is a color. Actually only checking it's a string for the moment'''
    genericTypeCheck(j, name, str)

def floatListCheck(j, name, nitems=-1):
    '''Checks that the object is a float list and that the number of items is the number expected if nitems >= 0'''
    # check we have a list
    genericTypeCheck(j, name, list)
    # check number of items if needed
    if nitems >= 0 and len(j) != nitems:
        raise PhoenixFormatError("Expected %d entries in %s, got %d" % (nitems, name, len(j)))
    # check all items are floats
    n = 0
    for item in j:
        floatCheck(item, name + ", item %d" % n)
        n += 1

def hitTypeCheck(j, name):
    '''check that the object is a valid hit Type, so one of Point, Line or Box'''
    if j not in ('Point', 'Box', 'Line'):
        raise PhoenixFormatError(
            'Invalid hit type "%s" in %s. Valid values are Point, Line and Box' % (j, name))    
    
def posAttributeCheck(positions, name):
    '''Check that the object is a valid pos attibute, so a list of floats triplets'''
    # pos attribute should be a list
    genericTypeCheck(positions, name, list)
    # each item should be a triplet of floats
    n = 0
    for pos in positions:
        floatListCheck(pos, name + ", item %d" % n, 3)
        n += 1
        
def tracksCheck(data_name, data):
    '''Check that the object is a valid Tracks entry'''
    entries = {
        'pos' : (False, posAttributeCheck),
        'color' : (True, colorAttributeCheck),
        'dparams' : (True, lambda j, n : floatListCheck(j, n, 5)),
        'd0' : (True, floatCheck),
        'z0' : (True, floatCheck),
        'phi' : (True, floatCheck),
        'eta' : (True, floatCheck),
    }
    genericTypeCheck(data, data_name, list)
    n = 1
    for track in data:
        # check entries of the Track
        genericCheck(track, entries, '%s, track %d' % (data_name, n), 'Track')
        n += 1

def jetsCheck(data_name, data):
    '''Check that the object is a valid Jets entry'''
    entries = {
        'eta' : (False, floatCheck),
        'phi' : (False, floatCheck),
        'theta' : (True, floatCheck),
        'energy' : (True, floatCheck),
        'et' : (True, floatCheck),
        'coneR' : (True, floatCheck),
        'color' : (True, colorAttributeCheck),
    }
    genericTypeCheck(data, data_name, list)
    n = 1
    for jet in data:
        # check entries of the Track
        genericCheck(jet, entries, '%s, jet %d' % (data_name, n), 'Jet')
        n += 1
        
def hitsCheck(data_name, data):
    '''Check that the object is a valid Hits entry'''
    # data should be a list of "hits"
    genericTypeCheck(data, data_name, list)
    # empty list is the easy case
    if len(data) == 0: return
    # check whether we have a list of position triplets or a list of objects
    if isinstance(data[0], list):
        # we have a list of positions, each of them should be a riplet of floats
        n = 0
        for position in data:
            pos_name = '%s, position %d' % (data_name, n)
            genericTypeCheck(position, data_name, list)
            if len(position) != 3:
                raise PhoenixFormatError(
                    "Expected Hits to be triplets of values. Not the case for %s" % pos_name)
            floatCheck(position[0], pos_name + ', coordinate x')
            floatCheck(position[1], pos_name + ', coordinate y')
            floatCheck(position[2], pos_name + ', coordinate z')
            n += 1
    else:
        # we have a list of "Hit" objects
        entries =  {
            'type' : (True, hitTypeCheck),
            'pos' : (False, floatListCheck),
            'color' : (True, colorAttributeCheck),
        }
        n = 0
        for hit in data:
            # check Hit structure
            genericCheck(hit, entries,'%s, hit %d' % (data_name, n), "Hit")
            # check type and len of pos match
            typ = hit['type'] if 'type' in hit else 'Point'
            npos = len(hit['pos'])
            expNpos = 3 if typ == 'Point' else 6
            if npos != expNpos:
                raise PhoenixFormatError(
                    "Expected %d coordinates per Hit in %s. Found %d in hit %d" % (expNpos, data_name, npos, n))
            n += 1

def clustersCheck(data_name, data):
    '''Check that the object is a valid CaloClusters/CaloCells entry'''
    # data should be a list of CaloClusters or CaloCells
    genericTypeCheck(data, data_name, list)
    # check entries' structure
    entries =  {
        'energy' : (False, floatCheck),
        'phi' : (False, floatCheck),
        'eta' : (False, floatCheck),
    }
    n = 0
    for item in data:
        genericCheck(item, entries, '%s, entry %d' % (data_name, n), 'CaloCluster/CaloCell')
        n += 1

def planarCaloCheck(data_name, data):
    '''Check that the object is a valid PlanarCaloCells entry'''
    # data should be an object
    genericTypeCheck(data, data_name, dict)
    # check entries
    entries = {
        'plane' : (False, lambda j, n : floatListCheck(j, n, 4)),
        'cells' : (False, lambda j, name : genericTypeCheck(j, name + ", cells attribute", list)),
    }
    genericCheck(data, entries, data_name, 'PlanarCaloCells')
    # check each cell
    cellEntries = {
        'cellSize' : (False, floatCheck),
        'energy' : (False, floatCheck),
        'pos' : (False, lambda j, n : floatListCheck(j, n, 2)),
        'color' : (True, colorAttributeCheck),
    }
    n = 0
    for cell in data['cells']:
        genericCheck(cell, cellEntries, data_name + ', cell %d' % n, 'CaloCell')
        n += 1

def verticesCheck(data_name, data):
    '''Check that the object is a valid Vertices entry'''
    # data should be a list of Vertices
    genericTypeCheck(data, data_name, list)
    # check Vertices' structure
    entries =  {
        'x' : (False, floatCheck),
        'y' : (False, floatCheck),
        'z' : (False, floatCheck),
        'color' : (True, colorAttributeCheck),
    }
    n = 0
    for item in data:
        genericCheck(item, entries, '%s, vertex %d' % (data_name, n), 'Vertex')
        n += 1

def missingECheck(data_name, data):
    '''Check that the object is a valid MissingEnergy entry'''
    # data should be a list of objects
    genericTypeCheck(data, data_name, list)
    # check entries' structure
    entries =  {
        'etx' : (False, floatCheck),
        'ety' : (False, floatCheck),
        'color' : (True, colorAttributeCheck),
    }
    n = 0
    for item in data:
        genericCheck(item, entries, '%s, object %d' % (data_name, n), 'MissingEnergy')
        n += 1

def compoundCheck(data_name, data):
    # no check for the moment. To be fixed
    return

'''table of known dataTypes and their checking function'''
KnownDataTypes = {
    'Tracks': tracksCheck,
    'Jets': jetsCheck,
    'Hits': hitsCheck,
    'CaloClusters': clustersCheck,
    'CaloCells': clustersCheck,
    'PlanarCaloCells': planarCaloCheck,
    'Vertices': verticesCheck,
    'MissingEnergy': missingECheck,
    'Muons': compoundCheck,
    'Photons': compoundCheck,
    'Electrons': compoundCheck,
}

def eventDataCheck(event_name, data_type, data):
    '''
    Checks the structure of Phoenix event;s data
    raises a PhoenixFormatError in case it is not correct, with indication of the problem
    '''
    # the data_type must be one of the authorized objects types
    if data_type not in KnownDataTypes.keys():
        raise PhoenixFormatError("Unknown data type found : '%s'" % data_type)
    # for each collection of this data type, check the structure
    for collection_name in data:
        KnownDataTypes[data_type]("event '%s', collection '%s'" % (event_name, collection_name), data[collection_name])

def eventCheck(event_name, event):
    '''
    Checks the structure of a Phoenix event object
    raises a PhoenixFormatError in case it is not correct, with indication of the problem
    '''
    # events are supposed to be objects with an event number and a run number    
    entries = {
        'event number' : {False, noCheck},
        'run number' : {False, noCheck},
    }
    genericCheck(event, entries, 'top level event ' + event_name, 'Event')
    # check event data, ignoring entries not holding a dictionnary
    for data in event:
        if isinstance(event[data], dict):
            eventDataCheck(event_name, data, event[data])

def check(topJson):
    '''
    checks whether the given json data respects the phoenix format
    raises a PhoenixFormatError in case it does not, with indication of the problem
    '''
    # a top level phoenix json is simply a list of events
    if not isinstance(topJson, dict):
        raise PhoenixFormatError("Expected a dictionary at top level")
    else:
        # check all events one by one
        for eventKey in topJson:
            eventCheck(eventKey, topJson[eventKey])

# in case we are called as an executable, expect as argument the file to check
if __name__ == '__main__':
    if len (sys.argv) != 2:
        print ("Wrong number of arguments")
        print ("Syntax : %s <fileName>" % sys.argv[0])
        sys.exit(1)
    import json
    json_file = open(sys.argv[1])
    topJson = json.load(json_file)
    check(topJson)
