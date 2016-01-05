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
#openstack clients
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
##############stack A#######################
templateA = {
    'heat_template_version':"2013-05-23",
    'description':{'component_id':'1123'},
    'resources': {
    'network_a':{'type':'OS::Neutron::Net',
        'properties':{'tenant_id': tenant_id}},
    'subnet_a':{'type':'OS::Neutron::Subnet',
        'properties':{'cidr':'20.0.0.0/24','tenant_id':tenant_id,'gateway_ip':'20.0.0.1',
                      'network':{'get_resource':'network_a'}}},
    'router_a':{'type':'OS::Neutron::Router',
        'properties':{'external_gateway_info':{'network':'public'}}},
    'rintf_a':{'type':'OS::Neutron::RouterInterface',
        'properties':{'router_id':{'get_resource':'router_a'},
                      'subnet':{'get_resource':'subnet_a'}}},
    'vm_a':{'type': 'OS::Nova::Server',
        'properties':{'flavor':'m1.tiny','image':'cirros-0.3.4-x86_64-uec-ramdisk',
                      'security_groups':['default'],
                      'networks':[{'network':{'get_resource':'network_a'}}]}},
    'vpn_a':{'type':'OS::Neutron::VPNService',
        'properties':{'router':{'get_resource':'router_a'},
                      'subnet':{'get_resource':'subnet_a'}}}
    }
}
###############stack B#####################
templateB = {
    'heat_template_version':"2013-05-23",
    'resources': {
    'network_b':{'type':'OS::Neutron::Net',
        'properties':{'tenant_id': tenant_id }},
    'subnet_b':{'type':'OS::Neutron::Subnet',
        'properties':{'cidr':'10.0.0.0/24','tenant_id':tenant_id,'gateway_ip':'10.0.0.1',
                      'network':{'get_resource':'network_b'}}},
    'router_b':{'type':'OS::Neutron::Router',
        'properties':{'external_gateway_info':{'network':'public'}}},
    'rintf_b':{'type':'OS::Neutron::RouterInterface',
        'properties':{'router_id':{'get_resource':'router_b'},
                      'subnet':{'get_resource':'subnet_b'}}},
    'vm_b':{'type': 'OS::Nova::Server',
        'properties':{'flavor':'m1.tiny','image':'cirros-0.3.4-x86_64-uec-ramdisk',
                      'security_groups':['default'],
                      'networks':[{'network':{'get_resource':'network_b'}}]}},
    'vpn_b':{'type':'OS::Neutron::VPNService',
        'properties':{'router':{'get_resource':'router_b'}, 
                      'subnet':{'get_resource':'subnet_b'}}}
    }
}
###########################################
ra_id = None
ra_ip = None
rb_id = None
rb_ip = None
sa_id = None
sb_id = None
va_id = None
vb_id = None
for router in neutron.list_routers()['routers']:
    if 'router_a' in router['name']:
        ra_id = router['id']
        ra_ip = router['external_gateway_info']['external_fixed_ips'][0]['ip_address']
    if 'router_b' in router['name']:
        rb_id = router['id']
        rb_ip = router['external_gateway_info']['external_fixed_ips'][0]['ip_address']
for subnet in neutron.list_subnets()['subnets']:
    if 'subnet_a' in subnet['name']:
        sa_id = subnet['id']
    if 'subnet_b' in subnet['name']:
        sb_id = subnet['id']

for vpn in neutron.list_vpnservices()['vpnservices']:
    if 'vpn_a' in vpn['name']:
        va_id = vpn['id']
    elif 'vpn_b' in vpn['name']:
        vb_id = vpn['id']
#########stack vpn#########################
templateVPN = {
    'heat_template_version':"2013-05-23",
    'resources': {
    'ikepolicy':{'type':'OS::Neutron::IKEPolicy'},
    'ipsecpolicy':{'type':'OS::Neutron::IPsecPolicy'},

    'conn_a':{'type':'OS::Neutron::IPsecSiteConnection',
        'properties':{
            'ikepolicy_id':{'get_resource':'ikepolicy'},
            'ipsecpolicy_id':{'get_resource':'ipsecpolicy'},
            'peer_address':rb_ip,
            'peer_cidrs':['20.0.0.0/24'],
            'peer_id':rb_ip,
            'psk':'secret',
            'vpnservice_id':va_id
        }},
    'conn_b':{'type':'OS::Neutron::IPsecSiteConnection',
        'properties':{
            'ikepolicy_id':{'get_resource':'ikepolicy'},
            'ipsecpolicy_id':{'get_resource':'ipsecpolicy'},
            'peer_address':ra_ip,
            'peer_cidrs':['10.0.0.0/24'],
            'peer_id':ra_ip,
            'psk':'secret',
            'vpnservice_id':vb_id
        }}
    }
}
#############install vpn###################
#stack_a = heat.stacks.create(stack_name='stack_a',template=json.dumps(templateA))
#stack_b = heat.stacks.create(stack_name='stack_b',template=json.dumps(templateB))
#stack_vpn = heat.stacks.create(stack_name='stack_vpn',template=json.dumps(templateVPN))
#############stack firewall################
templateFW = {
    'heat_template_version':"2013-05-23",
    'resources': {
    'fwrule':{'type':'OS::Neutron::FirewallRule',
        'properties':{'protocol':'tcp','destination_port':'80','action':'allow'}},
    'fwpolicy':{'type':'OS::Neutron::FirewallPolicy',
        'properties':{'firewall_rules':[{'get_resource':'fwrule'}]}},
    'fw':{'type':'OS::Neutron::Firewall',
        'properties':{'firewall_policy_id':{'get_resource':'fwpolicy'}}}
    }
}
#stack_fw = heat.stacks.create(stack_name='stack_fw',template=json.dumps(templateFW))
###########################################
templateLB = {
    'heat_template_version':"2013-05-23",
    'resources': {

    }
}
###########################################
import pdb; pdb.set_trace()
