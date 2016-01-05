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

keystone =  keystone_client.Client(username=username, 
                                   password=password, 
                                   tenant_name=tenant_name, 
                                   auth_url=auth_url)
tenant_id = keystone.tenants.find(name=tenant_name).id
endpoint =  keystone.auth_ref.service_catalog.get_urls(service_type='orchestration')[0]
heat =      heat_client.Client(token=keystone.auth_token,
                               username=tenant_name,
                               password=password,
                               endpoint=endpoint)
neutron =   client.Client('2.0',username=username,
                          password=password,
                          tenant_name=tenant_name,
                          auth_url=auth_url)
for router in neutron.list_routers()['routers']:
    router_ip = router['external_gateway_info']['external_fixed_ips'][0]['ip_address']
    print 'router|name|%s|id|%s|ip|%s' %(router['name'], router['id'], router_ip)
for vpn in neutron.list_vpnservices()['vpnservices']:
    print 'vpn|name|%s|id|%s' %(vpn['name'],vpn['id'])

"""
for subnet in neutron.list_subnets()['subnets']:
    if 'subnet_a' in subnet['name']:
        sa_id = subnet['id']
    if 'subnet_b' in subnet['name']:
        sb_id = subnet['id']
"""
