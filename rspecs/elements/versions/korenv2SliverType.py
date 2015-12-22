#from sfa.rspecs.elements.element import Element
from sfa.rspecs.elements.openstackv2 import *
from sfa.rspecs.elements.element import Element
from sfa.util.sfalogging import logger
import types

class Korenv2SliverType:

    @staticmethod
    def add_os_slivers(xml, slivers):
        if not slivers:
            return 
        if not isinstance(slivers, list):
            slivers = [slivers]
        for sliver in slivers:
            sliver_elem = xml.add_element('{%s}sliver' % xml.namespaces['openstack'])
            attrs = ['component_id', 'sliver_id', 'sliver_name', 'sliver_type']
            for attr in attrs:
                if sliver.get(attr):
                    sliver_elem.set(attr, sliver[attr])
           
            availability_zone = sliver['availability_zone']
            if availability_zone and isinstance(availability_zone, dict):
                sliver_elem.add_instance('{%s}availability_zone' % xml.namespaces['openstack'], \
                                         availability_zone, OSZone.fields)

            security_groups = sliver['security_groups']
            if security_groups and isinstance(security_groups, list):
                for security_group in security_groups:
                    if security_group.get('rules'):
                        rules = security_group.pop('rules')
                    group_sliver_elem = sliver_elem.add_instance('{%s}security_group' % xml.namespaces['openstack'], \
                                                                 security_group, OSSecGroup.fields)
                    if rules and isinstance(rules, list):
                        for rule in rules:
                            group_sliver_elem.add_instance('{%s}rule' % xml.namespaces['openstack'], \
                                                           rule, OSSecGroupRule.fields)

            flavor = sliver['flavor']
            if flavor and isinstance(flavor, dict):
                flavor_sliver_elem = sliver_elem.add_instance('{%s}flavor' % xml.namespaces['openstack'], \
                                                              flavor, OSFlavor.fields)
                boot_image = sliver.get('boot_image')
                if boot_image and isinstance(boot_image, dict):
                    flavor_sliver_elem.add_instance('{%s}image' % xml.namespaces['openstack'], \
                                                    boot_image, OSImage.fields)    

            images = sliver['images']
            if images and isinstance(images, list):
                for image in images:
                    # Check if the minimum quotas requested is suitable or not
                    if image['minRam'] <= flavor_sliver_elem.attrib['ram'] and \
                       image['minDisk'] <= flavor_sliver_elem.attrib['storage']:
                        flavor_sliver_elem.add_instance('{%s}image' % xml.namespaces['openstack'], \
                                                        image, OSImage.fields)

            addresses = sliver['addresses']
            if addresses and isinstance(addresses, list):
                for address in addresses:
                    # Check if the type of the address
                    if address.get('private'):
                        sliver_elem.add_instance('{%s}address' % xml.namespaces['openstack'], \
                                                 address.get('private'), OSSliverAddr.fields)
                    elif address.get('public'):
                        sliver_elem.add_instance('{%s}address' % xml.namespaces['openstack'], \
                                                 address.get('public'), OSSliverAddr.fields)

                        
    @staticmethod
    def get_os_slivers(xml, filter=None):
        if filter is None: filter={}
        #xpath = './openstack:'
        #sliver_elems = xml.xpath(xpath)
        return Korenv2SliverType.get_os_element(xml.xpath("./openstack:sliver"), 
                                                OSSliver)
        
    
    @staticmethod    
    def get_os_element (rspec_nodes, OSNodeClass, fields=None):
        if len(rspec_nodes) == 0: 
            return None
        ret_list = []
        if fields == None: fields = OSNodeClass.fields
        for rspec_node in rspec_nodes:
            #os_node = OSNodeClass(rspec_node.attrib)
            os_node = OSNodeClass(fields)
            for tag, value in fields.items() : 
                if isinstance(value, type):
                    #1. openstack resource type (OSResource, must contain name and OS::type)
                    os_node[tag] = Korenv2SliverType.get_os_element(
                                        rspec_node.xpath("./openstack:%s"%tag), 
                                        value, fields=None)
                elif isinstance(value, types.DictType):
                    if value['class']:
                        #1. form of list of element [{...}, ...] type (Element)
                        os_node[tag]= Korenv2SliverType.get_os_element(
                                            rspec_node.xpath("./openstack:%s"%tag),
                                            value['class'], fields=value['fields'])
                    else : 
                        #2. form of single element {k1:value,k2:elem,...}
                        dummy_node = Korenv2SliverType.get_os_element(
                                            rspec_node.xpath("./openstack:%s"%tag),
                                            OSResource, fields=value['fields'])
                        if dummy_node: os_node[tag]=dummy_node[0]
                elif isinstance(value, types.StringType):
                    #1. hot function type (value=='get_resource', ...)
                    #   entering existing resource_id(uuid) is not allowed!!!!
                    if value == 'get_resource':
                        if tag in rspec_node.attrib : os_node[tag]={value:rspec_node.attrib[tag]}
                    #2. simple list type [value, ... ]
                    elif value == 'simple_list':
                        dummy_nodes = Korenv2SliverType.get_os_element(
                                        rspec_node.xpath("./openstack:%s"%tag),
                                        OSResource, fields={'value':None})
                        if dummy_nodes: 
                            os_node[tag] = [dummy_node['value'] for dummy_node in dummy_nodes]
                else: #elif isinstance(value, types.NoneType):
                    # xml attribute / simple str, int, bool
                    if tag in rspec_node.attrib: os_node[tag]=rspec_node.attrib[tag]
                    else : os_node[tag]=None
            ret_list.append(os_node)
        return ret_list
