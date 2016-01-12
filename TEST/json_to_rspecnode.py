from sfa.rspecs.rspec import RSpec
from sfa.rspecs.elements.openstackv2 import *
from sfa.rspecs.version_manager import VersionManager
from sfa.rspecs.elements.node import NodeElement

import json, sys
#test your .rspec file 's validation 
if len(sys.argv) != 3:
    print 'usage : python json_to_rspec.py dir/to/json.json sliver_name'
    sys.exit()
json_string = open(sys.argv[1]).read()
template = json.loads(json_string)

version_manager = VersionManager()
rspec_version = version_manager._get_version('KOREN', '2', 'request')
rspec = RSpec(version=rspec_version)

rspec_node = NodeElement()
rspec_node['component_id']='urn:publicid:IDN+koren+node+openstack'
rspec_node['slivers']= OSSliver(sliver_name=sys.argv[2], template=template, sliver_type='openstack') 
xml = rspec.version.add_nodes([rspec_node])
print xml[0].toxml()
