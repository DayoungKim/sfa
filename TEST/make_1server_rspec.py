from heatclient.v1 import client as heat_client
from keystoneclient.v2_0 import client as keystone_client
from neutronclient.neutron import client

import json, yaml

############################################
#change this to your configuration
username='osadmin'
password='kulcloud'
tenant_name='koren'
auth_url = 'http://10.1.100.27:35357/v2.0'
############################################
neutron =   client.Client('2.0',username=username,
                          password=password,
                          tenant_name=tenant_name,
                          auth_url=auth_url)

import sys
from inputrspec import InputRspec

if len(sys.argv) < 2:
    print 'usage : python %s network_namee' %__file__

change_list = []
for network in neutron.list_networks()['networks']:
    if sys.argv[1] in network['name']:
        change_list = change_list + [('network_id',network['id'])]

src_file = '1server_template.rspec'
dst_file = '1server.rspec'
InputRspec(source_file=src_file, dst_file=dst_file, change_list=change_list).write()
