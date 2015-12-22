from sfa.rspecs.elements.element import Element  

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

    def __init__(self, fields=None, element=None, keys=None, hot_type=None):
        Element.__init__(self, fields, element, keys)
        if fields: self.fields = fields 
        if hot_type: self.hot_type = hot_type

    def to_hot(self, arg_dict):
        # get tenant_id from user is allowed, but not suggested
        # getting tenant_id keystone client is more safe way
        properties = {}
        for key, value in self.items():
            if value:
                if hasattr(value, 'to_hot'):
                    properties.update({key:value.to_hot(arg_dict)})
                else:
                    properties.update({key:value})
            else:
                if key in arg_dict: 
                    properties.update({key:arg_dict[key]})

        if self.hot_type == None:
            return properties

        properties.pop('name')
        return {
            self['name']:{
                'type':self.hot_type,
                'properties':properties
            }
        }
"""
class (OSResource):
    fields = {
    }
    hot_type = ''
"""

class OSNeutronVPNService(OSResource):
    fields = {
        'name':None,
        'admin_state_up':None,
        'description':None,
        'router':'get_resource',
        'subnet':'get_resource'
    }
    hot_type = 'OS::Neutron::VPNService'

class OSNeutronIKEPolicy(OSResource):
    fields = {
        'name':None,
        'auth_algorith':None,#sha1 only allowed
        'descrition':None,
        'encryption_algorithm':None,#3des, aes-128(defaulted), aes-192, aes-256
        'ike_version':None,#v1(default), v2
        'lifetime':{'class':None,'fields':{'value':None,'units':None}},#units:seconds(default), kilobytes
        'pfs':None,#group2, group5(default), group14
        'phase1_negotiation_mode':None#main
    }
    hot_type = 'OS::Neutron::IPsecPolicy'

class OSNeutronIPsecSiteConnection(OSResource):
    fields = {
        'name':None,        
        'admin_state_up': None,
        'description': None,
        'dpd': {'class':None, 'fields':{'actions': None, 'interval': None, 'timeout': None}},
        #actions (clear, disabled, hold, restart, restart-py-peer
        #interval(default 30) timout(default 120)
        'ikepolicy_id': None, #not optional
        'initiator': None,#bi-directinal(default), response-only
        'ipsecpolicy_id': None, #not optional
        'mtu': None,#1500(default)
        'peer_address': None, #not optional
        'peer_cidrs': 'simple_list',#not optional
        'peer_id': None,#remote branch router id
        'psk': None,#
        'vpnservice_id': 'get_resource'
    }
    hot_type = 'OS::Neutron::IPsecSiteConnection'

class OSNeutronFirewall(OSRsource):
    fields = {
        'admin_state_up': None,
        'description': None,
        'firewall_policy_id': None
        #'shared': Boolean(Available since 2015.1 (Kilo))
        #'value_specs': {...}(Available since 5.0.0 (Liberty))
    }
    hot_type = 'OS::Neutron::Firewall'

class OSNeutronFirewallPolicy(OSResource):
    fields = {
        'audited': None,
        'description': None,
        'firewall_rules': 'simple_list',
        'shared': None
    }
    hot_type='OS::Neutron::FirewallPolicy'

class OSNeutronFirewallRule(OSResource):
    fields = {
        'action': None,#Allowed values: allow, deny
        'description': None,
        'destination_ip_address': None,
        'destination_port': None,
        'enabled': None,
        'ip_version': None,#Allowed values: 4, 6
        'protocol': None,#Allowed values: tcp, udp, icmp, any
        'shared': None,#Whether this rule should be shared across all tenants
        'source_ip_address': None,
        'source_port': None
    }
    hot_type = 'OS::Neutron::FirewallRule'

class OSNeutronFloatingIP(OSResource):
    fields = {
        'fixed_ip_address': None,
        'floating_ip_address': None,#Available since 5.0.0 (Liberty)
        'floating_network': 'get_resource',
        'port_id': 'ger_resource'#String(Value must be of type neutron.port)
        #'value_specs': {...}
    }
    hot_type = 'OS::Neutron::FloatingIP'

class OSNeutronFloatingIPAssociation(OSResource):
    fields = {
        'fixed_ip_address': None,
        'floatingip_id': None,#not optional
        'port_id': 'get_resource'#not optional
    }
    hot_type = 'OS::Neutron::FloatingIPAssociation'

class OSNeutronLoadBalancer(OSResource):
    fields = {
        'members': 'simple_list',
        'pool_id': None,
        'protocol_port': None#0 to 65535
    }
    hot_type = 'OS::Neutron::LoadBalancer'

"""
class (OSResource):
    fields = {
    }
    hot_type = ''
"""

class OSNeutronNet(OSResource):
    fields = {
        'name':None,
        'tenant_id': None 
    }
    hot_type = 'OS::Neutron::Net'

class OSNeutronSubnet(OSResource):
    fields = {
        'name':None,
        'cidr':None,
        'tenant_id':None, 
        'network':'get_resource',
        'ip_version':None,
        'enable_dhcp':None,
        'gateway_ip':None,
        'dns_nameservers':'simple_list',
        'allocation_pools':{'class':OSResource,'fields':{'start':None,'end':None}}
    }
    hot_type = 'OS::Neutron::Subnet'

class OSNeutronRouter(OSResource):
    fields = {
        'name':None,
        'admin_state_up':None,
        'external_gateway_info':{'class':None,'fields':{'enable_snat':None,'network':None}}
    }
    hot_type = 'OS::Neutron::Router'

class OSNeutronRouterInterface(OSResource):
    fields = { 
        'name':None,
        'router_id': 'get_resource', 
        'subnet': 'get_resource' 
    }
    hot_type = 'OS::Neutron::RouterInterface'

class OSNovaServer(OSResource):
    fields = {
        'name':None,
        'flavor':None,
        'image':None,
        'networks':{'class':OSResource,'fields':{'network':'get_resource'}},
        'availability_zone':None,
        'key_name':None,
        'security_groups':'simple_list'
    }
    hot_type = 'OS::Nova::Server'

class OSSliver(Element):
    fields = {
        'component_id':None,
        'sliver_name':None, 
        'sliver_type':None, 
        'network':OSNeutronNet,
        'router':OSNeutronRouter,
        'subnet':OSNeutronSubnet,
        'router_interface':OSNeutronRouterInterface,
        'server':OSNovaServer,
        'vpnservice':OSNeutronVPNService,
        'ikepolicy':OSNeutronIKEPolicy,
        'ipSecSiteConnection':OSNeutronIPsecSiteConnection,
        'firewall':OSNeutronFirewall,
        'firewallpolicy':OSNeutronFirewallPolicy,
        'firewallrull':OSNeutronFirewallRule,
        'floatingip':OSNeutronFloatingIP,
        'floatingipAssociation':OSNeutronFloatingIPAssociation,
        'loadbalancer':OSNeutronLoadBalancer
    }

    def to_hot(self, arg_dict):# hot yaml(x) hot json(o)
        resources = {}
        for rsrc_list in self.values():
            if isinstance(rsrc_list, list):
                for resource in rsrc_list:
                    resources.update(resource.to_hot(arg_dict))
        return self['sliver_name'], {
            'heat_template_version':"2013-05-23",
            'description':{'component_id':self['component_id']},
            'resources': resources
        }
