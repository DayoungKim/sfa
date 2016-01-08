from sfa.rspecs.rspec import RSpec
import json, sys
#test your .rspec file 's validation 
if len(sys.argv) != 3:
    print 'usage : python rspec.py dir/to/rspec_file.rspec tenant_id'
    sys.exit()
rspec_string = open(sys.argv[1]).read()
rspec_sfa = RSpec(rspec_string)
rspec_sfa_dict = rspec_sfa.version.get_nodes_with_slivers()
name, template = rspec_sfa_dict[0]['slivers'][0].to_hot(tenant_id=sys.argv[2])
print 'stack name : %s' %name
print template
#import pdb; pdb.set_trace()
