from sfa.rspecs.elements.element import Element  

import types

class OSResource(Element):
    
    # resource fields how-to
    # None : xml attribute / simple str, int, bool
    # OSResource class : list of dict, hot resource 
    # {'class':OSResource, 'fields':{..} } : list of dict [{}...], dict may contain other node 
    # {'class':None, 'fields':{..} } : single dict {} , dict may contain other node
    # string :
    #   1. 'get_resource' .... : hot function (xml attribute)
    #   2. 'simple_list' : list of simple value type [ str, ...]
    #                      rspec input <openstack:key value="str"/> (xml elemenet)

    fields = {}
    hot_type = None

    def __init__(self, fields=None, hot_type=None, template=None, name=None):
        if fields: self.fields = fields 
        Element.__init__(self)
        if hot_type: self.hot_type = hot_type
        if name:
            self['osname']=name
        if template:
            self.to_element(template)

    def to_hot(self, tenant_id):
        # get tenant_id from user is allowed, but not suggested
        # getting tenant_id keystone client is more safe way
        properties = {}
        for key, value in self.items():
            if value:
                if isinstance(self.fields[key], types.DictType):
                    if self.fields[key]['class']:#list of dict
                        properties.update({key:[v.to_hot(tenant_id)for v in value]})
                    else:#single dict
                        properties.update({key:value.to_hot(tenant_id)})
                else:#None, get_resource, simple_list
                    properties.update({key:value})
            else:
                if key=='tenant_id': 
                    properties.update({key:tenant_id})

        if self.hot_type == None:
            return properties

        properties.pop('osname')
        if properties == {}: return {self['osname']:{'type':self.hot_type}}
        return { 
            self['osname']:{
                'type':self.hot_type,
                'properties':properties
            }
        }

    def to_element(self, template):
        properties = template.get('properties')
        if properties == None:
            if self.hot_type !=None :
                return
            else:
                properties = template
        for key, value in properties.items():
            if value:
                self[key]=[]
                if isinstance(self.fields[key], types.DictType):
                    if self.fields[key]['class']:
                        OSNodeClass = self.fields[key]['class']
                        for v in value:
                            os_node = OSNodeClass(fields=self.fields[key]['fields'],template=v)
                            self[key].append(os_node)
                    else:
                        self[key] = OSResource(fields=self.fields[key]['fields'],template=value)
                else:
                    if key=='tenant_id': self[key]=None
                    else: self[key]=value
"""
class (OSResource):
    fields = {
        'osname':None,
    }
    hot_type = ''
"""
class OSNeutronNet(OSResource):
    fields = {
        'osname':None,
        'admin_state_up':None,#boolean
        'dhcp_agent_ids':'simple_list',
        'port_security_enabled':None,#boolean
        'shared':None,#boolean,
        'tenant_id': None
        #'value_specs':{...}
    }
    hot_type = 'OS::Neutron::Net'

class OSNeutronSubnet(OSResource):
    fields = {
        'osname':None,
        'allocation_pools':{'class':OSResource,'fields':{'start':None,'end':None}},
        'cidr':None,
        'dns_nameservers':'simple_list',
        'enable_dhcp':None,#boolean default True
        'gateway_ip':None,
        'host_routes':{'class':OSResource, 'fields':{'destination':None,'nexthop':None}},
        'ip_version':None,#Allowed value : 4(default), 6
        'ipv6_address_mode':None,#Allowed values: dhcpv6-statefule, dhcpv6-stateless, slaac
        'ipv6_ra_mode':None,#Allowed values: dhcpv6-stateful, dhcpv6-stateless, slaac
        'network':'get_resource',#?
        #'prefixlen':None,#Available since 6.0.0 (Mitaka)
        #'subnetpool':'get_resource'#Available since 6.0.0 (Mitaka)
        'tenant_id':None
        #'value_specs':{...}
    }
    hot_type = 'OS::Neutron::Subnet'

class OSNeutronRouter(OSResource):
    fields = {
        'osname':None,
        'admin_state_up':None,#boolean
        'distributed':None,#boolean
        'external_gateway_info':{'class':None,'fields':{'enable_snat':None,'network':None}},
        'ha':None,#boolean
        'l3_agent_ids':'simple_list'
        #'value_specs':{...}

    }
    hot_type = 'OS::Neutron::Router'

class OSNeutronRouterInterface(OSResource):
    fields = {
        'osname':None,
        'router_id': 'get_resource',
        'subnet': 'get_resource'
    }
    hot_type = 'OS::Neutron::RouterInterface'

class OSNovaServer(OSResource):
    fields = {
        'osname':None,
        'flavor':None,#not optional
        'admin_pass':None,
        'availability_zone':None,
        'block_device_mapping':{'class':OSResource,'fields':{
            'delete_on_termination':None,#boolean
            'device_name':None,#vda
            'snapshot_id':None,
            'volume_id':None,
            'volume_size':None #GB
        }},
        'block_device_mapping_v2':{'class':OSResource,'fields':{
            'boot_index':None,
            'delete_on_termination':None,#boolean
            'device_name':None,
            'device_type':None,#Allowed values: cdrom, disk
            'disk_bus':None,#Allowed values: ide, lame_bus, scsi, usb, virtio
            'image_id':None,
            'snapshot_id':None,
            'swap_size':None,
            'volume_id':None,
            'volume_size':None
        }},
        'config_drive':None,
        'diskConfig':None,#Allowed values: AUTO, MANUAL
        'flavor_update_policy':None,#Allowed values: RESIZE(default), REPLACE
        'image':None,
        'image_update_policy':None,#Allowed values: REBUILD(default), 
                                   #REPLACE, REBUILD_PRESERVE_EPHEMERAL
        'key_name':None,
        'metadata':None,
        'networks':{'class':OSResource,'fields':{
            'fixed_ip':None,
            'network':'get_resource',
            'port':'get_resource'
            #'port_extra_properties':{'class':OSResource,'fields':{}},#Available in 6.0.0 (Mitaka)
            #'subnet':'get_resource'#Abailable in 5.0.0 (Liberty)
        }},
        #'personality':{},#map value expected (not supported yet in sfa)
        'reservation_id':None,
        #'scheduler_hints':{},#map value expected (not supported yet in sfa)
        'security_groups':'simple_list',
        'software_config_transport':None,#Allowed value: POLL_SERVER_CFN(default), POLL_SERVER_HEAT,
                                         #POLL_TEMP_URL, ZAQAR_MESSAGE
        'user_data':None,
        'user_data_format':None#Allowed value: HEAT_CNFTOOLS(default), RAW, SOFTWARE_CONFIG
    }
    hot_type = 'OS::Nova::Server'

class OSNeutronVPNService(OSResource):
    fields = {
        'osname':None,
        'admin_state_up':None,
        'description':None,
        'router':'get_resource',
        'subnet':'get_resource'
    }
    hot_type = 'OS::Neutron::VPNService'

class OSNeutronIKEPolicy(OSResource):
    fields = {
        'osname':None,
        'auth_algorithm':None,#Allowed value : sha1(default)
        'description':None,
        'encryption_algorithm':None,#Allowed value : 3des, aes-128(default), aes-192, aes-256
        'ike_version':None,#Allowed value : v1(default), v2
        'lifetime':{'class':None, 'fields':{
            'units':None,#Allowed value : seconds(defulat), kilobytes
            'value':None#default 3600
        }},
        'pfs':None,#Allowed value : group2, group5(default), group14
        'phase1_negotiation_mode':None#main(default)
    }
    hot_type = 'OS::Neutron::IKEPolicy'

class OSNeutronIPsecPolicy(OSResource):
    fields = {
        'osname':None,
        'auth_algorithm':None,#Allowed value : sha1(default)
        'description':None,
        'encapsulation_mode':None,#Allowed value : tunnel, transport
        'encryption_algorithm':None,#Allowed value : 3des, aes-128(default), aes-192, aes-256
        'lifetime':{'class':None, 'fields':{
            'unit':None,#Allowed value : seconds(default), kilobytes
            'value':None #default 3600
        }},
        'pfs':None,#Allowed value : group2, group5(default), group14
        'transport_protocol':None #Allowed value : esp(default), ah, ah-esp
    }
    hot_type = 'OS::Neutron::IPsecPolicy'

class OSNeutronIPsecSiteConnection(OSResource):
    fields = {
        'osname':None,
        'admin_state_up':None,
        'description':None,
        'dpd': {'class':None, 'fields':{
            'actions':None,#actions (clear, disabled, hold, restart, restart-py-peer
            'interval':None,#interval(default 30)
            'timeout':None#timout(default 120)
        }},
        'ikepolicy_id':'get_resource',#not optionsal
        'ipsecpolicy_id':'get_resource',#not optional
        'mtu':None,#not optional
        'peer_address':None,#not optional
        'peer_cidrs':'simple_list',
        'peer_id':None,#remote branch router id
        'psk':None,
        'vpnservice_id':'get_resource'
    }
    hot_type = 'OS::Neutron::IPsecSiteConnection'


class OSNeutronFirewall(OSResource):
    fields = {
        'osname':None,
        'admin_state_up':None,
        'description':None,
        'firewall_policy_id':'get_resource',
        'shared':None,#Boolean(Available since 2015.1 (Kilo))
        #'value_specs':{...}(Available since 5.0.0 (Liberty))
    }
    hot_type = 'OS::Neutron::Firewall'

class OSNeutronFirewallPolicy(OSResource):
    fields = {
        'osname':None,
        'audited':None,#boolean
        'description':None,
        'firewall_rules':{'class':OSResource, 'fields':{
            'get_resource':None
        }},
        'shared':None
    }
    hot_type = 'OS::Neutron::FirewallPolicy'

class OSNeutronFirewallRule(OSResource):
    fields = {
        'osname':None,
        'action':None,#Allowed value : allow, deny
        'description':None,
        'destination_ip_address':None,
        'destination_port':None,
        'enabled':None,
        'ip_version':None,#Allowed value : 4, 6
        'protocol':None,#Allowed value : tcp, udp, icmp, any
        'shared':None,#whether this rule should be shared acress all tenants
        'source_ip_address':None,
        'source_port':None
    }
    hot_type = 'OS::Neutron::FirewallRule'

class OSNeutronLoadBalancer(OSResource):
    fields = {
        'osname':None,
        'members':'simple_list',
        'pool_id':None,
        'protocol_pot':None#0 to 65535
    }
    hot_type = 'OS::Neutron::LoadBalancer'

class OSNeutronPool(OSResource):
    fields = {
        'osname':None,
        'admin_state_up':None,#boolean
        'description':None,
        'lb_method':None,#not optional Allowed values : ROUND_ROBIN, LEAST_CONNECTIONS, SOURCE_IP
        'monitors':'simple_list',
        #'provider':'get_resource',#Available since 5.0.0 (Liberty)
        'subnet':None,#not optional
        'vip':{'class':None, 'fields':{
            'address':None,
            'admin_state_up':None,#boolean
            'connection_limit':None,
            'description':None,
            'osname':None,
            'protocol_port':None,
            'session_persistence':{ 'class':None,'fields':{
                'cookie_name':None,#not optional if type is APP_COOKIE
                'type':None#Allowed values: SOURCE_IP, HTTP_COOKIE, APP_COOKIE
            }}
        }}
    }
    hot_type = 'OS::Neutron::Pool'

class OSNeutronPoolMember(OSResource):
    fields = {
        'osname':None,
        'address':None,#not optional
        'admin_state_up':None,#boolean
        'pool_id':None,#not optional
        'protocol_port':None,#not optional range 0 to 65535
        'weight':None#range 0 to 256
    }
    hot_type = 'OS::Neutron::PoolMember'

class OSNeutronHealthMonitor(OSResource):
    fields = {
        'osname':None,
        'admin_state_up':None,
        'delay':None, #not_optional
        'expected_codes':None, #'simple_list'? list of HTTP status codes expected in responce
        'http_method':None,
        'max_retries':None,
        'timeout':None,#not optional
        'type':None,#not optional Allowed values: PING, TCP, HTTP, HTTPS
        'url_path':None
    }
    hot_type = 'OS::Neutron::HealthMonitor'

class OSNeutronFloatingIP(OSResource):
    fields = {
        'osname':None,
        'fixed_ip_address':None,
        'floating_ip_address':None,#Available since 5.0.0 (Liberty)
        'floating_network':'get_resource',
        'port_id':'get_resource'
        #'value_specs':{...}
    }
    hot_type = 'OS::Neutron::FloatingIP'

class OSNeutronFloatingIPAssociation(OSResource):
    fields = {
        'osname':None,
        'fixed_ip_address':None,
        'floatingip_id':None,
        'port_id':'get_resource'
    }
    hot_type = 'OS::Neutron::FloatingIPAssociation'

class OSSliver(Element):
    fields = {
        'component_id':None,
        'sliver_name':None, 
        'sliver_type':None,
 
        'network': OSNeutronNet,
        'router': OSNeutronRouter,
        'subnet': OSNeutronSubnet,
        'router_interface': OSNeutronRouterInterface,
        'server': OSNovaServer,

        'vpnservice': OSNeutronVPNService,
        'ikepolicy': OSNeutronIKEPolicy,
        'ipsecpolicy': OSNeutronIPsecPolicy,
        'ipsecsiteconnection': OSNeutronIPsecSiteConnection,
        'firewall': OSNeutronFirewall,
        'firewallpolicy': OSNeutronFirewallPolicy,
        'firewallrule': OSNeutronFirewallRule,
        'loadbalancer': OSNeutronLoadBalancer,
        'pool': OSNeutronPool,
        'poolmember': OSNeutronPoolMember,
        'healthmonitor': OSNeutronHealthMonitor,

        ######It's not required in SFA ->not tested######
        'floatingip': OSNeutronFloatingIP,
        'floatingipAssociation': OSNeutronFloatingIPAssociation
        ##################################################
    }

    def __init__(self, element=None, keys=None, template=None, sliver_name=None, sliver_type=None):
        Element.__init__(self, element, keys)
        if template and sliver_name and sliver_type:
            self.to_element(template, sliver_name, sliver_type)

    def to_hot(self, tenant_id):# hot yaml(x) hot json(o)
        resources = {}
        for rsrc_list in self.values():
            if isinstance(rsrc_list, list):
                for resource in rsrc_list:
                    resources.update(resource.to_hot(tenant_id))
        return self['sliver_name'], {
            'heat_template_version':"2013-05-23",
            'description':{'component_id':self['component_id']},
            'resources': resources
        }

    def to_element(self, template, sliver_name, sliver_type):
        self['component_id'] = component_id = template.get('description').get('component_id')
        self['sliver_name'] = sliver_name
        self['sliver_type'] = sliver_type
        resources = template.get('resources')

        suports = {}
        for rspec_type, OSClass in self.fields.items():
            if OSClass:
                suports.update(
                    {OSClass.hot_type:(rspec_type,OSClass)})

        for name, value in resources.items():
            rspec_type, OSClass = suports[value['type']]
            rspec_node = OSClass(name=name, template=value)
            if rspec_node:
                if self[rspec_type]==None: self[rspec_type]=[]
                self[rspec_type].append(rspec_node)
