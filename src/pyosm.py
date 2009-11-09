#! /usr/bin/python
#
# Original version by Rory McCann (http://blog.technomancy.org/)
# Modifications by Christoph Lupprich (http://www.stopbeingcarbon.com)
#
import xml.sax

class Node(object):
    def __init__(self, id=None, lon=None, lat=None, tags=None):
        self.id = id
        self.lon, self.lat = lon, lat
        if tags:
            self.tags = tags
        else:
            self.tags = {}

    def __cmp__(self, other):
        cmp_ref = cmp(self.tags.get('ref',''), other.tags.get('ref',''))
        if cmp_ref:
            return cmp_ref
        cmp_name = cmp(self.tags.get('name',''), other.tags.get('name',''))
        if cmp_name:
            return cmp_name
        return cmp(self.id, other.id)

    def __repr__(self):
        return "Node(id=%r, lon=%r, lat=%r, tags=%r)" % (self.id, self.lon, self.lat, self.tags)

class Way(object):
    def __init__(self, id, nodes=None, tags=None):
        self.id = id
        if nodes:
            self.nodes = nodes
        else:
            self.nodes = []
        if tags:
            self.tags = tags
        else:
            self.tags = {}

    def __cmp__(self, other):
        cmp_ref = cmp(self.tags.get('ref',''), other.tags.get('ref',''))
        if cmp_ref:
            return cmp_ref
        cmp_name = cmp(self.tags.get('name',''), other.tags.get('name',''))
        if cmp_name:
            return cmp_name
        return cmp(self.id, other.id)

    def __repr__(self):
        return "Way(id=%r, nodes=%r, tags=%r)" % (self.id, self.nodes, self.tags)

class Relation(object):
    def __init__(self, id, members=None, tags=None):
      self.id = id
      if members:
          self.members = None
      else:
          self.members = []
      if tags:
          self.tags = tags
      else:
          self.tags = {}
      
    def __cmp__(self, other):
        cmp_ref = cmp(self.tags.get('ref',''), other.tags.get('ref',''))
        if cmp_ref:
            return cmp_ref
        cmp_name = cmp(self.tags.get('name',''), other.tags.get('name',''))
        if cmp_name:
            return cmp_name
        return cmp(self.id, other.id)

    def __repr__(self):
      return "Relation(id=%r, members=%r, tags=%r)" % (self.id, self.members, self.tags)

class NodePlaceHolder(object):
    def __init__(self, id, type=None, role=''):
        self.id = id
        self.type = type
        self.role = role

    def __repr__(self):
        return "NodePlaceHolder(id=%r, type=%r)" % (self.id, self.type)

class OSMXMLFile(object):
    def __init__(self, filename):
        self.filename = filename

        self.nodes = {}
        self.ways = {}
        self.relations = {}
        self.__parse()
        #print repr(self.ways)
    
    def __get_obj(self, id, type, role):
        if type == "way":
            return (self.ways[id], role)
        elif type == "node":
            return (self.nodes[id], role)
        elif type == "relation":
            return (self.relations[id], role)
        else:
            print "Don't know type %r in __get_obj" % (type)
            return None
    
    def __parse(self):
        """Parse the given XML file"""
        parser = xml.sax.make_parser()
        parser.setContentHandler(OSMXMLFileParser(self))
        parser.parse(self.filename)

        # now fix up all the refereneces
        for way in self.ways.values():
            way.nodes = [self.nodes[node_pl.id] for node_pl in way.nodes]
              
        for relation in self.relations.values():
            relation.members = [self.__get_obj(obj_pl.id, obj_pl.type, obj_pl.role) for obj_pl in relation.members]

    def statistic(self):
        """Print a short statistic about the osm object"""
        print "filename:", self.filename
        print "  Nodes:     %i" % len(self.nodes)
        print "  Ways:      %i" % len(self.ways)
        print "  Relations: %i" % len(self.relations)


class OSMXMLFileParser(xml.sax.ContentHandler):
    def __init__(self, containing_obj):
        self.containing_obj = containing_obj
        self.curr_node = None
        self.curr_way = None
        self.curr_relation = None

    def startElement(self, name, attrs):
        if name == 'node':
            self.curr_node = Node(id=attrs['id'], lon=attrs['lon'], lat=attrs['lat'])
            
        elif name == 'way':
            self.curr_way = Way(id=attrs['id'])
            
        elif name == 'tag':
            if self.curr_node:
                self.curr_node.tags[attrs['k']] = attrs['v']
            elif self.curr_way:
                self.curr_way.tags[attrs['k']] = attrs['v']
            elif self.curr_relation:
                self.curr_relation.tags[attrs['k']] = attrs['v']
                
        elif name == "nd":
            assert self.curr_node is None, "curr_node (%r) is non-none" % (self.curr_node)
            assert self.curr_way is not None, "curr_way is None"
            self.curr_way.nodes.append(NodePlaceHolder(id=attrs['ref']))
            
        elif name == "relation":
            assert self.curr_node is None, "curr_node (%r) is non-none" % (self.curr_node)
            assert self.curr_way is None, "curr_way (%r) is non-none" % (self.curr_way)
            assert self.curr_relation is None, "curr_relation (%r) is non-none" % (self.curr_relation)
            self.curr_relation = Relation(id=attrs['id'])
          
        elif name == "member":
            assert self.curr_node is None, "curr_node (%r) is non-none" % (self.curr_node)
            assert self.curr_way is None, "curr_way (%r) is non-none" % (self.curr_way)
            assert self.curr_relation is not None, "curr_relation is None"
            self.curr_relation.members.append(NodePlaceHolder(id=attrs['ref'], type=attrs['type'], role=attrs['role']))
          
        elif name == "osm":
            pass

        elif name == "bound":
            pass

        else:
            print "Don't know element %s" % name


    def endElement(self, name):
        if name == "node":
            self.containing_obj.nodes[self.curr_node.id] = self.curr_node
            self.curr_node = None
            
        elif name == "way":
            self.containing_obj.ways[self.curr_way.id] = self.curr_way
            self.curr_way = None
        
        elif name == "relation":
            self.containing_obj.relations[self.curr_relation.id] = self.curr_relation
            self.curr_relation = None


#################### MAIN            
if __name__ == '__main__':
    import sys
    for filename in sys.argv[1:]:
        osm = OSMXMLFile(filename)
        osm.statistic()
                         