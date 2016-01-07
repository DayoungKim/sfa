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
        sliver_elem = xml.add_element('{%s}sliver' %xml.namespaces['openstack'])
        ret = Korenv2SliverType.get_os_sliver_nodes(sliver_elem, slivers, OSSliver)
        return ret
        #return Korenv2SliverType.get_os_sliver_nodes(sliver_elem, slivers, OSSliver)

    @staticmethod
    def get_os_sliver_nodes(xml, slivers, OSNodeClass=None, fields=None):
        if len(slivers) == 0: 
            return None
        if fields==None : fields = OSNodeClass.fields
        for sliver in slivers:
            for key, value in sliver.items():
                if value:
                    if isinstance(fields[key], type):
                        os_elem = xml.add_element('{%s}%s' %(xml.namespaces['openstack'], key))
                        Korenv2SliverType.get_os_sliver_nodes(xml=os_elem, 
                                                              slivers=value, 
                                                              OSNodeClass=fields[key])
                    elif isinstance(fields[key], types.DictType):
                        os_elem = xml.add_element('{%s}%s' %(xml.namespaces['openstack'], key))
                        if fields[key]['class']:
                            Korenv2SliverType.get_os_sliver_nodes(os_elem, value, None, 
                                                                  fields[key]['fields'])
                        else:
                            Korenv2SliverType.get_os_sliver_nodes(os_elem, [value], None, 
                                                                  fields[key]['fields'])
                    elif isinstance(fields[key], types.StringType):
                        if fields[key] == 'get_resource':
                            xml.set(key, value['get_resource'])
                        elif fields[key] == 'simple_list':
                            for v in value:
                                os_elem = xml.add_element('{%s}%s' %(xml.namespaces['openstack'], key))
                                os_elem.set('value', v)
                    else:
                        xml.set(key, value)

    @staticmethod
    def get_os_slivers(xml, filter=None):
        if filter is None: filter={}
        return Korenv2SliverType.get_os_element(xml.xpath("./openstack:sliver"), OSSliver)

    @staticmethod    
    def get_os_element (rspec_nodes, OSNodeClass, fields=None):
        if len(rspec_nodes) == 0: 
            return None
        ret_list = []
        if fields == None: fields = OSNodeClass.fields
        for rspec_node in rspec_nodes:
            os_node = OSNodeClass(fields)
            for tag, value in fields.items() : 
                os_node[tag]=None
                if isinstance(value, type):
                    #1. openstack resource type
                    os_node[tag] = Korenv2SliverType.get_os_element(
                                        rspec_node.xpath("./openstack:%s"%tag), 
                                        value, fields=None)
                elif isinstance(value, types.DictType):
                    if value['class']:
                        #2. form of list of element [{...}, ...]
                        os_node[tag]= Korenv2SliverType.get_os_element(
                                            rspec_node.xpath("./openstack:%s"%tag),
                                            value['class'], fields=value['fields'])
                    else : 
                        #3. form of single element {...}
                        dummy_node = Korenv2SliverType.get_os_element(
                                            rspec_node.xpath("./openstack:%s"%tag),
                                            OSResource, fields=value['fields'])
                        if dummy_node: os_node[tag]=dummy_node[0]
                elif isinstance(value, types.StringType):
                    if value == 'get_resource':
                        #4. hot function type (value=='get_resource', ...)
                        if tag in rspec_node.attrib : 
                            os_node[tag]={value:rspec_node.attrib[tag]}
                    elif value == 'simple_list':
                        #5. simple list type [value, ... 
                        dummy_nodes = Korenv2SliverType.get_os_element(
                                        rspec_node.xpath("./openstack:%s"%tag),
                                        OSResource, fields={'value':None})
                        if dummy_nodes: 
                            os_node[tag] = [dummy_node['value'] for dummy_node in dummy_nodes]
                else: # 6. xml attribute / simple str, int, bool
                    if tag in rspec_node.attrib: os_node[tag]=rspec_node.attrib[tag]
            ret_list.append(os_node)
        return ret_list
