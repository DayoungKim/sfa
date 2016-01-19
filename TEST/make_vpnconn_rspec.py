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
    print 'usage : python %s sliver1_name sliver2_name' %__file__

slivers = [('1',sys.argv[1]), ('2',sys.argv[2])]
change_list = []
for router in neutron.list_routers()['routers']:
    for num, sliver_name in slivers:
        router_ip = router['external_gateway_info']['external_fixed_ips'][0]['ip_address']
        if sliver_name in router['name']:
            base = 'router%s' %num
            change_list = change_list + [('%s_id'%base,router['id']), ('%s_ip'%base,router_ip)]
    #print 'router|name|%s|id|%s|ip|%s' %(router['name'], router['id'], router_ip)
for subnet in neutron.list_subnets()['subnets']:
    for num, sliver_name in slivers:
        if sliver_name in subnet['name']:
            base = 'subnet%s' %num
            change_list = change_list + [('%s_id'%base,subnet['id']),('%s_cidr'%base,subnet['cidr'])]
            print [('%s_id'%base,subnet['id']),('%s_cidr'%base,subnet['cidr'])]
    #print 'sunnet|name|%s|id|%s|cidr|%s' %(subnet['name'],subnet['id'],subnet['cidr'])

src_file = 'vpnconn_template.rspec'
dst_file = 'vpnconn.rspec'
InputRspec(source_file=src_file, dst_file=dst_file, change_list=change_list).write()
