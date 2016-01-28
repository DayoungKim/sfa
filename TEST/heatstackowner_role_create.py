from keystoneclient.v2_0 import client as keystone_client


#change this to your configuration
username='admin'
password='kulcloud'
tenant_name='admin'
auth_url = 'http://10.1.100.43:35357/v2.0'
#openstack clients
keystone =  keystone_client.Client(username=username,
                                   password=password,
                                   tenant_name=tenant_name,
                                   auth_url=auth_url)

roles = keystone.roles.list()
not_exist = True
for r in roles:
    if r.name == 'heat_stack_owner':
        not_exist = True

if not_exist:
    keystone.roles.create('heat_stack_owner')

###########################################
#import pdb; pdb.set_trace()
