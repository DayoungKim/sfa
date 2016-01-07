import os
import socket
import base64
import string
import random
import time   
import json#for heat
from collections import defaultdict
from sfa.util.faults import SliverDoesNotExist
from sfa.util.sfatime import utcparse, datetime_to_string, datetime_to_epoch
from sfa.util.xrn import Xrn, get_leaf, hrn_to_urn
from sfa.util.sfalogging import logger
from sfa.storage.model import SliverAllocation

from sfa.rspecs.rspec import RSpec
from sfa.rspecs.elements.openstackv2 import *
from sfa.rspecs.version_manager import VersionManager
from sfa.rspecs.elements.node import NodeElement

from sfa.rspecs.elements.hardware_type import HardwareType
from sfa.rspecs.elements.sliver import Sliver
from sfa.rspecs.elements.login import Login
from sfa.rspecs.elements.services import ServicesElement

from sfa.client.multiclient import MultiClient
from sfa.openstack.osxrn import OSXrn, hrn_to_os_slicename
from sfa.openstack.security_group import SecurityGroup
from sfa.openstack.osconfig import OSConfig

# for exception
from novaclient import exceptions

def pubkeys_to_user_data(pubkeys):
    user_data = "#!/bin/bash\n\n"
    for pubkey in pubkeys:
        pubkey = pubkey.replace('\n', '')
        user_data += "echo %s >> /root/.ssh/authorized_keys" % pubkey
        user_data += "\n"
        user_data += "echo >> /root/.ssh/authorized_keys"
        user_data += "\n"
    return user_data

def os_image_to_rspec_disk_image(image):
    img = OSImage()
    img['name']    = str(image.name)
    img['minDisk'] = str(image.minDisk)
    img['minRam']  = str(image.minRam)
    img['imgSize'] = str(image._info['OS-EXT-IMG-SIZE:size'])
    img['status']  = str(image.status)
    return img
    
class OSAggregate:

    def __init__(self, driver):
        self.driver = driver

    def get_availability_zones(self, zones=None):
        # Update inital connection info
        self.driver.init_compute_manager_conn()
        zone_list=[]
        if not zones:
            availability_zones = self.driver.shell.compute_manager.availability_zones.list()
            for zone in availability_zones:
                if (zone.zoneState.get('available') == True) and \
                   (zone.zoneName != 'internal'):
                    zone_list.append(zone.zoneName)
        else:
            availability_zones = self.driver.shell.compute_manager.availability_zones.list()
            for a_zone in availability_zones:
                for i_zone in zones:
                    if a_zone.zoneName == i_zone: 
                        if (a_zone.zoneState.get('available') == True) and \
                           (a_zone.zoneName != 'internal'):
                            zone_list.append(a_zone.zoneName)
        return zone_list

    def list_resources(self, version=None, options=None):
        if options is None: options={}
        version_manager = VersionManager()
        version = version_manager.get_version(version)
        rspec_version = version_manager._get_version(version.type, version.version, 'ad')
        rspec = RSpec(version=version, user_options=options)
        nodes = self.get_aggregate_nodes()
        rspec.version.add_nodes(nodes)
        return rspec.toxml()

    def describe(self, urns, version=None, options=None):
        if options is None: options={}
        version_manager = VersionManager()
        version = version_manager.get_version(version)
        rspec_version = version_manager._get_version(version.type, version.version, 'manifest')
        rspec = RSpec(version=rspec_version, user_options=options)
        # Update connection for the current user
        xrn = Xrn(urns[0], type='slice')
        user_name = xrn.get_authority_hrn() + '.' + xrn.leaf.split('-')[0]
        tenant_name = OSXrn(xrn=urns[0], type='slice').get_hrn()
        self.driver.shell.orchest_manager.connect(username=user_name,
                                                  tenant=tenant_name,
                                                  password=user_name)

        time.sleep(3)
        # Get instances from the Openstack
        instances = self.get_instances(xrn)

        # Add sliver(s) from instance(s)
        geni_slivers = []
        rspec.xml.set( 'expires',  datetime_to_string(utcparse(time.time())) )
        rspec_nodes = []
        for instance in instances:
            rspec_nodes.append(self.instance_to_rspec_node(instance))
            geni_sliver = self.instance_to_geni_sliver(instance)
            geni_slivers.append(geni_sliver)
        rspec.version.add_nodes(rspec_nodes)

        result = { 'geni_urn': xrn.get_urn(),
                   'geni_rspec': rspec.toxml(),
                   'geni_slivers': geni_slivers }
        return result

    def get_instances(self, xrn):
        """
        # parse slice names and sliver ids
        slice_names=[]
        sliver_ids=[]
        instances=[]
        if xrn.type == 'slice':
            slice_names.append(xrn.get_hrn())
        else:
            print "[WARN] We don't know the xrn[%s]" % xrn.type
            logger.warn("[WARN] We don't know the xrn[%s], Check it!" % xrn.type)
            
        # look up instances
        try:
            for slice_name in slice_names:
                servers = self.driver.shell.compute_manager.servers.findall()
                instances.extend(servers)
            for sliver_id in sliver_ids:
                servers = self.driver.shell.compute_manager.servers.findall()
                instances.extend(servers)
        except(exceptions.Unauthorized):
            print "[WARN] The instance(s) in Openstack is/are not permitted."
            logger.warn("The instance(s) in Openstack is/are not permitted.")
        return list( set(instances) )
        """
        # parse slice names and sliver ids
        slice_names=[]
        instances=[]
        if xrn.type == 'slice':
            slice_names.append(xrn.get_hrn())
        else:
            print "[WARN] We don't know the xrn[%s]" % xrn.type
            logger.warn("[WARN] We don't know the xrn[%s], Check it!" % xrn.type)
            
        # look up instances
        try:
            for slice_name in slice_names:
                stacks = self.driver.shell.orchest_manager.stacks.list()
                instances.extend(stacks)
        except(exceptions.Unauthorized):
            print "[WARN] The instance(s) in Openstack is/are not permitted."
            logger.warn("The instance(s) in Openstack is/are not permitted.")
        return list( set(instances) )

    def instance_to_rspec_node(self, instance):
        # determine node urn
        node_xrn = instance.description.get('component_id')
        if not node_xrn:
            node_xrn = OSXrn(self.driver.hrn+'.'+'openstack', type='node')
        else:
            node_xrn = OSXrn(xrn=node_xrn, type='node')

        rspec_node = NodeElement()
        if not instance.description.get('component_manager_id'):
            rspec_node['component_manager_id'] = Xrn(self.driver.hrn, type='authority+am').get_urn()
        else:
            rspec_node['component_manager_id'] = instance.description.get('component_manager_id')
        rspec_node['component_id'] = node_xrn.urn
        rspec_node['component_name'] = node_xrn.name
        rspec_node['sliver_id'] = OSXrn(name=('koren'+'.'+ instance.stack_name), 
                                              id=instance.id,
                                              type='node+openstack').get_urn()
        template = self.driver.shell.orchest_manager.stacks.template(instance.id)
        sliver = OSSliver(template=template, sliver_name=instance.stack_name, sliver_type='openstack')
        """
        # get sliver details about quotas of resource
        flavor = self.driver.shell.compute_manager.flavors.find(id=instance.flavor['id'])
        sliver = self.flavor_to_sliver(flavor=flavor, instance=instance, xrn=None)
   
        # get availability zone
        zone_name = instance.to_dict().get('OS-EXT-AZ:availability_zone')    
        sliver['availability_zone'] = OSZone({ 'name': zone_name })

        # get firewall rules
        group_names = instance.security_groups
        sliver['security_groups']=[]
        if group_names and isinstance(group_names, list):
            for group in group_names:
                group = self.driver.shell.compute_manager.security_groups.find(name=group.get('name'))
                sliver['security_groups'].append(self.secgroup_to_rspec(group))

        # get disk image from the Nova service
        image = self.driver.shell.compute_manager.images.get(image=instance.image['id'])
        boot_image = os_image_to_rspec_disk_image(image)
        sliver['boot_image'] = boot_image

        # Get addresses of the sliver
        sliver['addresses']=[]
        addresses = instance.addresses
        if addresses:
            from netaddr import IPAddress
            for addr in addresses.get('private'):
                fields = OSSliverAddr({ 'mac_address': addr.get('OS-EXT-IPS-MAC:mac_addr'),
                                        'version': str(addr.get('version')),
                                        'address': addr.get('addr'),
                                        'type': addr.get('OS-EXT-IPS:type') })
                # Check if ip address is local
                ipaddr = IPAddress(addr.get('addr'))
                if (ipaddr.words[0] == 10) or (ipaddr.words[0] == 172 and ipaddr.words[1] == 16) or \
                   (ipaddr.words[0] == 192 and ipaddr.words[1] == 168):
                    type = { 'private': fields }
                else:
                    type = { 'public': fields }
                sliver['addresses'].append(type)
        """
        rspec_node['slivers'] = [sliver]
        return rspec_node

    def secgroup_to_rspec(self, group):
        rspec_rules=[]
        for rule in group.rules:
            rspec_rule =  OSSecGroupRule({ 'ip_protocol': str(rule['ip_protocol']),
                                           'from_port': str(rule['from_port']),
                                           'to_port': str(rule['to_port']),
                                           'ip_range': str(rule['ip_range'])
                                         })
            rspec_rules.append(rspec_rule)

        rspec = OSSecGroup({ 'id': str(group.id),
                             'name': str(group.name),
                             'description': str(group.description),
                             'rules': rspec_rules
                           })
        return rspec

    def flavor_to_sliver(self, flavor, instance=None, xrn=None):
        if xrn:
            sliver_id = OSXrn(name='koren.sliver', type='node+openstack').get_urn()
            sliver_name = None
        if instance:
            sliver_id = OSXrn(name=('koren'+'.'+ instance.name), id=instance.id, \
                              type='node+openstack').get_urn()
            sliver_name = instance.name
        sliver = OSSliver({ 'sliver_id': str(sliver_id),
                            'sliver_name': str(sliver_name),
                            'sliver_type': 'virtual machine',
                            'flavor': \
                                     OSFlavor({ 'name': str(flavor.name),
                                                'id': str(flavor.id),
                                                'vcpus': str(flavor.vcpus),
                                                'ram': str(flavor.ram),
                                                'storage': str(flavor.disk)
                                              }) })
        return sliver

    def instance_to_geni_sliver(self, instance):
        sliver_id = OSXrn(name=('koren'+'.'+ instance.stack_name), id=instance.id, \
                          type='node+openstack').get_urn()

        constraint = SliverAllocation.sliver_id.in_([sliver_id])
        sliver_allocations = self.driver.api.dbsession().query(SliverAllocation).filter(constraint)
        sliver_allocation_status = sliver_allocations[0].allocation_state

        error = 'None'
        op_status = 'geni_unknown'
        if sliver_allocation_status:
            if sliver_allocation_status == 'geni_allocated':
                op_status = 'geni_pending_allocation'
            elif sliver_allocation_status == 'geni_provisioned':
                state = instance.status.lower()
                if state == 'active':
                    op_status = 'geni_ready'
                elif state == 'build':
                    op_status = 'geni_not_ready'
                elif state == 'error':
                    op_status = 'geni_failed'
                    error = "Retry to provisioning them!"
                else:
                    op_status = 'geni_unknown'
            elif sliver_allocation_status == 'geni_unallocated':
                op_status = 'geni_not_ready'
        else:
            sliver_allocation_status = 'geni_unknown'

        geni_sliver = { 'geni_sliver_urn': sliver_id, 
                        'geni_expires': None,
                        'geni_allocation_status': sliver_allocation_status,
                        'geni_operational_status': op_status,
                        'geni_error': error,
                        'os_sliver_created_time': instance.creation_time
                      }
        return geni_sliver
                        
    def get_aggregate_nodes(self):
        # Get the list of available zones
        zones = self.get_availability_zones()
        # Get the list of available instance types 
        flavors = self.driver.shell.compute_manager.flavors.list() 
        # Get the list of available instance images
        images = self.driver.shell.compute_manager.images.list()
        available_images=[]
        for image in images:
            if ((image.name.find('ramdisk') == -1) and (image.name.find('kernel') == -1)):
                available_images.append(os_image_to_rspec_disk_image(image))
      
        security_groups=[]
        groups = self.driver.shell.compute_manager.security_groups.list()
        for group in groups:
            security_groups.append(self.secgroup_to_rspec(group))

        rspec_nodes=[]
        for zone in zones:
            rspec_node = NodeElement()
            xrn = Xrn(self.driver.hrn+'.'+'openstack', type='node')
            rspec_node['component_id'] = xrn.urn
            rspec_node['component_manager_id'] = Xrn(self.driver.hrn, type='authority+am').get_urn()
            rspec_node['exclusive'] = 'false'

            slivers=[]
            for flavor in flavors:
                sliver = self.flavor_to_sliver(flavor=flavor, instance=None, xrn=xrn)
                sliver['component_id'] = xrn.urn
                sliver['images'] = available_images
                sliver['availability_zone'] = OSZone({ 'name': zone })
                sliver['security_groups'] = security_groups
                slivers.append(sliver)
            rspec_node['slivers'] = slivers
            rspec_node['available'] = 'true'
            rspec_nodes.append(rspec_node)
        
        return rspec_nodes

    def create_tenant(self, tenant_name, description=None):
        tenants = self.driver.shell.auth_manager.tenants.findall(name=tenant_name)
        if not tenants:
            tenant = self.driver.shell.auth_manager.tenants.create(tenant_name, description)
        else:
            tenant = tenants[0]
        return tenant


    def create_user(self, user_name, password, tenant_id, email=None, enabled=True):
        if password is None:
            logger.warning("If you want to make a user, you should include your password!!")
            raise ValueError('You should include your password!!')

        users = self.driver.shell.auth_manager.users.findall()
        for user in users:
            if user_name == user.name:
                user_info = user
                logger.info("The user name[%s] already exists." % user_name)
                break
        else:
            user_info = self.driver.shell.auth_manager.users.create(user_name, password, \
                                                             email, tenant_id, enabled)
        return user_info
    
    def create_security_group(self, slicename, fw_rules=None):
        if fw_rules is None: fw_rules=[]
        # use default group by default
        group_name = 'default' 
        if isinstance(fw_rules, list) and fw_rules:
            # Each sliver get's its own security group.
            # Keep security group names unique by appending some random
            # characters on end.
            random_name = "".join([random.choice(string.letters+string.digits)
                                           for i in xrange(6)])
            group_name = slicename + random_name 
            security_group = SecurityGroup(self.driver)
            security_group.create_security_group(group_name)
            for rule in fw_rules:
                security_group.add_rule_to_group(group_name, 
                                             protocol = rule.get('protocol'), 
                                             cidr_ip = rule.get('cidr_ip'), 
                                             port_range = rule.get('port_range'), 
                                             icmp_type_code = rule.get('icmp_type_code'))
            # Open ICMP by default
            security_group.add_rule_to_group(group_name,
                                             protocol = "icmp",
                                             cidr_ip = "0.0.0.0/0",
                                             icmp_type_code = "-1:-1")
        return group_name

    def add_rule_to_security_group(self, group_name, **kwds):
        security_group = SecurityGroup(self.driver)
        security_group.add_rule_to_group(group_name=group_name, 
                                         protocol=kwds.get('protocol'), 
                                         cidr_ip =kwds.get('cidr_ip'), 
                                         icmp_type_code = kwds.get('icmp_type_code'))

    def check_floatingip(self, instances, value):
        servers = []
        # True: Find servers which not assigned floating IPs
        if value is True:
            for instance in instances:
                for addr in instance.addresses.get('private', []): 
                    if addr.get('OS-EXT-IPS:type') == 'floating':
                        break
                else:
                    servers.append(instance)
        # False: Find servers which assigned floating IPs
        else:
            for instance in instances:
                for addr in instance.addresses.get('private', []):
                    if addr.get('OS-EXT-IPS:type') == 'floating':
                        servers.append(instance)
        return servers 

    def create_floatingip(self, tenant_name, instances):
        config = OSConfig()
        # Information of public network(external network) from configuration file
        extnet_name = config.get('network', 'external_network_name')
        tenant = self.driver.shell.auth_manager.tenants.find(name=tenant_name)
        networks = self.driver.shell.network_manager.list_networks().get('networks')
        for network in networks:
            if (network.get('name') == extnet_name) or \
               (network.get('name') == 'public') or (network.get('name') == 'ext-net'):
                pub_net_id = network.get('id')
                break
        else:
            logger.warning("We shoud need the public network ID for floating IPs!")
            raise ValueError("The public network ID was not found!")
        ports = self.driver.shell.network_manager.list_ports().get('ports')
        for port in ports:
            device_id = port.get('device_id')
            for instance in instances:
                if device_id == instance.id:
                    body = { "floatingip":
                             { "floating_network_id": pub_net_id,
                               "tenant_id": tenant.id,
                               "port_id": port.get('id') } }
                    self.driver.shell.network_manager.create_floatingip(body=body)

    def delete_floatingip(self, instances):
        floating_ips = self.driver.shell.network_manager.list_floatingips().get('floatingips')
        for ip in floating_ips:
            ip_tenant_id = ip.get('tenant_id')
            for instance in instances:
                if ip_tenant_id == instance.tenant_id:
                    self.driver.shell.network_manager.delete_floatingip(floatingip=ip.get('id'))

    def check_server_status(self, server):
        while (server.status.lower() == 'build'):
            time.sleep(0.5)
            server = self.driver.shell.compute_manager.servers.findall(id=server.id)[0]
        return server

    def check_stack_status(self, stack):
        while (stack.stack_status == 'CREATE_IN_PROGRESS'):
            time.sleep(0.5)
            stack = self.driver.shell.orchest_manager.stacks.get(stack.id)
        return stack

    def run_instances(self, tenant_name, user_name, rspec, key_name, pubkeys):
        # TODO : Kulcloud
        zones = self.get_availability_zones()
        self.driver.shell.auth_manager.connect()
        logger.info( "Checking if the created tenant[%s] or not ..." % tenant_name )
        tenant = self.driver.shell.auth_manager.tenants.find(name=tenant_name)
        self.driver.shell.orchest_manager.connect(username=user_name, 
                                                  tenant=tenant_name, 
                                                  password=user_name)
        if len(pubkeys):
            files = None
        else:
            authorized_keys = "\n".join(pubkeys)
            files = {'/root/.ssh/authorized_keys': authorized_keys}
        slivers = []
        rspec = RSpec(rspec)     # TODO  XML Input
        for node in rspec.version.get_nodes_with_slivers():
            instances = node.get('slivers', [])
            for instance in instances:
                try:
                    sliver_name, sliver_heat_dict = instance.to_hot(tenant_id=tenant.id)
                    print sliver_heat_dict
                    sliver = self.driver.shell.orchest_manager.stacks.create(
                                stack_name=sliver_name,
                                template=json.dumps(sliver_heat_dict))
                    print sliver
                    sliver = self.driver.shell.orchest_manager.stacks.get(sliver['stack']['id'])
                    slivers.append(sliver)
                    logger.info("Created Openstack instance [%s]" % sliver_name)
                except Exception, err:
                    logger.log_exc(err)
        return slivers 

    def delete_instance(self, instance):
        def _delete_security_group(inst):
            security_group = inst.metadata.get('security_groups', '')
            if security_group:
                manager = SecurityGroup(self.driver)
                timeout = 10.0 # wait a maximum of 10 seconds before forcing the security group delete
                start_time = time.time()
                instance_deleted = False
                while instance_deleted == False and (time.time() - start_time) < timeout:
                    tmp_inst = self.driver.shell.orchest_manager.stacks.get(id=inst.id)
                    if not tmp_inst:
                        instance_deleted = True
                    time.sleep(.5)
                manager.delete_security_group(security_group)

        multiclient = MultiClient()

        security_group_manager = SecurityGroup(self.driver)
        self.driver.shell.orchest_manager.stacks.delete(instance.id)
        multiclient.run(_delete_security_group, instance)
        return 1

        """
        def _delete_security_group(inst):
            security_group = inst.metadata.get('security_groups', '')
            if security_group:
                manager = SecurityGroup(self.driver)
                timeout = 10.0 # wait a maximum of 10 seconds before forcing the security group delete
                start_time = time.time()
                instance_deleted = False
                while instance_deleted == False and (time.time() - start_time) < timeout:
                    tmp_inst = self.driver.shell.compute_manager.servers.findall(id=inst.id)
                    if not tmp_inst:
                        instance_deleted = True
                    time.sleep(.5)
                manager.delete_security_group(security_group)

        multiclient = MultiClient()
        tenant = self.driver.shell.auth_manager.tenants.find(id=instance.tenant_id)
        
        # Update connection for the current client
        xrn = Xrn(tenant.name)
        user_name = xrn.get_authority_hrn() + '.' + xrn.leaf.split('-')[0]
        self.driver.shell.compute_manager.connect(username=user_name, tenant=tenant.name, password=user_name)

        args = { 'name': instance.name,
                 'id': instance.id }
        instances = self.driver.shell.compute_manager.servers.findall(**args)
        security_group_manager = SecurityGroup(self.driver)
        for instance in instances:
            # destroy instance
            self.driver.shell.compute_manager.servers.delete(instance)
            # deleate this instance's security groups
            multiclient.run(_delete_security_group, instance)
        return 1
        """

    def delete_router(self, tenant_id):
        is_router = False
        ports = self.driver.shell.network_manager.list_ports()
        ports = ports['ports']
        networks = self.driver.shell.network_manager.list_networks()
        networks = networks['networks']

        # find the subnetwork ID for removing the interface related with private network
        # TOPOLOGY: Public Network -- Router -- Private Network -- VM Instance(s)
        for port in ports:
            if (port.get('tenant_id') == tenant_id) and \
               (port.get('device_owner') == 'network:router_interface'):
                router_id = port.get('device_id')
                port_net_id = port.get('network_id')
        for network in networks:
            if network.get('tenant_id') == tenant_id:
                net_id = network.get('id')
                if port_net_id == net_id:
                    sbnet_ids = network.get('subnets')
                    is_router = True

        if is_router:
            # remove the router's interface which is related with private network
            if sbnet_ids:
                body = {'subnet_id': sbnet_ids[0]}
                self.driver.shell.network_manager.remove_interface_router(
                                                  router=router_id, body=body)
            # remove the router's interface which is related with public network
            self.driver.shell.network_manager.remove_gateway_router(router=router_id)
            # delete the router
            self.driver.shell.network_manager.delete_router(router=router_id)
            logger.info("Deleted the router: Router ID [%s]" % router_id)
        return 1

    def delete_network(self, tenant_id):
        is_network = False
        networks = self.driver.shell.network_manager.list_networks()
        networks = networks['networks']

        # find the network ID and subnetwork ID
        for network in networks:
            if network.get('tenant_id') == tenant_id:
                net_id = network.get('id')
                sbnet_ids = network.get('subnets')
                is_network = True

        time.sleep(5)  # This reason for waiting is that OS can't quickly handle "delete API". 
        if is_network:
            # delete the subnetwork and then finally delete the network related with tenant
            self.driver.shell.network_manager.delete_subnet(subnet=sbnet_ids[0])
            self.driver.shell.network_manager.delete_network(network=net_id)
            logger.info("Deleted the network: Network ID [%s]" % net_id)
        return 1

    def stop_instances(self, instance_name, tenant_name, id=None):
        # Update connection for the current client
        xrn = Xrn(tenant_name)
        user_name = xrn.get_authority_hrn() + '.' + xrn.leaf.split('-')[0]
        self.driver.shell.compute_manager.connect(username=user_name, tenant=tenant_name, password=user_name)

        args = { 'name': instance_name }
        if id:
            args['id'] = id
        instances = self.driver.shell.compute_manager.servers.findall(**args)
        for instance in instances:
            self.driver.shell.compute_manager.servers.pause(instance)
        return 1

    def start_instances(self, instance_name, tenant_name, id=None):
        # Update connection for the current client
        xrn = Xrn(tenant_name)
        user_name = xrn.get_authority_hrn() + '.' + xrn.leaf.split('-')[0]
        self.driver.shell.compute_manager.connect(username=user_name, tenant=tenant_name, password=user_name)

        args = { 'name': instance_name }
        if id:
            args['id'] = id
        instances = self.driver.shell.compute_manager.servers.findall(**args)
        for instance in instances:
            self.driver.shell.compute_manager.servers.resume(instance)
        return 1

    def restart_instances(self, instacne_name, tenant_name, id=None):
        # Update connection for the current client
        xrn = Xrn(tenant_name)
        user_name = xrn.get_authority_hrn() + '.' + xrn.leaf.split('-')[0]
        self.driver.shell.compute_manager.connect(username=user_name, tenant=tenant_name, password=user_name)

        self.stop_instances(instance_name, tenant_name, id)
        self.start_instances(instance_name, tenant_name, id)
        return 1 

    def update_instances(self, project_name):
        pass
