from sfa.rspecs.rspec import RSpec
import json, sys
#test your .rspec file 's validation 
if len(sys.argv) != 3:
    print 'usage : python hot_to_rspec.py dir/to/template.json sliver_name'
    sys.exit()
json_string = open(sys.argv[1]).read()
template = json.loads(json_string)
slivers=OSSliver(template=template, sliver_name=sys.argv[2], sliver_type='openstack')
rspec = Rspec('<?xml version="1.0" encoding="UTF-8"?>\
<rspec xmlns="http://www.geni.net/resources/rspec/3"\
       xmlns:openstack="http://203.255.254.100:8888/resources/sfa/rspecs/openstack" \
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
       xsi:schemaLocation="http://www.geni.net/resources/rspec/3/request.xsd http://203.255.254.100:8888/resources/sfa/rspecs/openstack/openstack.xsd"\
       type="request"/>')


for sliver in slivers:\
    rspec.version.get_os_sliver_nodes(

rspec_string = open(sys.argv[1]).read()
rspec_sfa = RSpec(rspec_string)
rspec_sfa_dict = rspec_sfa.version.get_nodes_with_slivers()
name, template = rspec_sfa_dict[0]['slivers'][0].to_hot(tenant_id=sys.argv[2])
rspec_sfa = Rspec('<?xml version="1.0" encoding="UTF-8"?>
<rspec xmlns="http://www.geni.net/resources/rspec/3"
       xmlns:openstack="http://203.255.254.100:8888/resources/sfa/rspecs/openstack" 
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
       xsi:schemaLocation="http://www.geni.net/resources/rspec/3/request.xsd http://203.255.254.100:8888/resources/sfa/rspecs/openstack/openstack.xsd"
       type="request"/>')

print 'stack name : %s' %name
print template
#import pdb; pdb.set_trace()
