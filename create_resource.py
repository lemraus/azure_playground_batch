#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import argparse

from time import sleep
from datetime import datetime, timedelta

import azure.batch

from azure.mgmt.batch import BatchManagementClient
from azure.storage.blob import ContainerPermissions
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.common.credentials import ServicePrincipalCredentials

import config



parser = argparse.ArgumentParser(
                                description='Creating a resource group containing a batch account and a storage account that has a blob container.',
                                epilog=('Returns a file named "config_resources.py" containing information about the batch '
                                        'account and the blob container that will have been created.'),
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                )
parser.add_argument('--resource_gp_name', help='Name of resource group', dest='resource_gpe_name', default='group-centrale-supelec')
parser.add_argument('--batch_account_name', help='Name of batch account', dest='batch_account_name', default='ab03centralesupelec')
parser.add_argument('--storage_account_name', help='Name of storage account', dest='storage_account_name', default='as03centralesupelec')
parser.add_argument('--blob_container_name', help='Name of blob container', dest='blob_container_name', default='results')
parser.add_argument('--region_name', help='Location where resources will be created', dest='region_name', default='centralus')
args = parser.parse_args()


resource_gpe_name = args.resource_gpe_name
batch_account_name = args.batch_account_name
storage_account_name = args.storage_account_name
blob_container_name = args.blob_container_name
region_name = args.region_name



subscription_id = config.subs
credentials = ServicePrincipalCredentials(
        client_id = config.sp['appId'],
        secret = config.sp['password'],
        tenant = config.sp['tenant']
        )

client = ResourceManagementClient(credentials = credentials, subscription_id = subscription_id)

resource_group_params = {'location': region_name}
batch_account_params = {'location': region_name}
storage_account_params = {'location': region_name, 'sku' : {'name':'Standard_LRS'}}

#create resource group
client.resource_groups.create_or_update(
        resource_group_name = resource_gpe_name,
        parameters = resource_group_params
        )

#create storage account
client.resources.create_or_update(
        resource_group_name = resource_gpe_name,
        resource_provider_namespace = 'Microsoft.Storage',
        parent_resource_path = '',
        resource_type = 'storageAccounts',
        resource_name = storage_account_name,
        api_version = '2017-10-01',
        parameters = storage_account_params
        )

#create batch account
client.resources.create_or_update(
        resource_group_name = resource_gpe_name,
        resource_provider_namespace = 'Microsoft.Batch',
        parent_resource_path = '',
        resource_type = 'batchAccounts',
        resource_name = batch_account_name,
        api_version = '2017-09-01',
        parameters = batch_account_params
        )

batch = {}
batch_client = BatchManagementClient(credentials, subscription_id)

primary_key_batch_account = batch_client.batch_account.get_keys(
                                  resource_group_name = resource_gpe_name, 
                                  account_name = batch_account_name
                                  )
primary_key_batch_account = primary_key_batch_account.primary

endpoint_batch = batch_client.batch_account.get(
                                  resource_group_name = resource_gpe_name, 
                                  account_name = batch_account_name
                                  )
endpoint_batch = endpoint_batch.account_endpoint

batch['name'] = batch_account_name
batch['key'] = primary_key_batch_account
batch['url'] = f'https://{endpoint_batch}'

storage_client = StorageManagementClient(credentials = credentials, subscription_id = subscription_id)
storage_properties = storage_client.storage_accounts.get_properties(
        resource_group_name = resource_gpe_name, 
        account_name = storage_account_name
        ) 

for i in range(18):
    if storage_properties.provisioning_state.name == 'succeeded': break
    else: sleep(10)
    

#create a blob container in a storage account
storage_client.blob_containers.create(
        resource_group_name = resource_gpe_name,
        account_name = storage_account_name,
        container_name = blob_container_name
        )

blob_container = {}
blob_container_url = storage_client.storage_accounts.get_properties(
        resource_group_name = resource_gpe_name,
        account_name = storage_account_name
        )
blob_container_url = f'{blob_container_url.primary_endpoints.blob}{blob_container_name}'

storage_keys = storage_client.storage_accounts.list_keys(resource_gpe_name, storage_account_name)
storage_keys = {v.key_name: v.value for v in storage_keys.keys}

blob_container_sas_token = azure.storage.SharedAccessSignature(
        account_name = storage_account_name,
        account_key = storage_keys['key1']
        )
blob_container_sas_token = blob_container_sas_token.generate_container(
        container_name = blob_container_name,
        permission=ContainerPermissions(read=True, write=True, delete=True, list=True),
        expiry=datetime.utcnow() + timedelta(days=7),
        start=datetime.utcnow() - timedelta(minutes=1),
        )

blob_container['url'] = blob_container_url
blob_container['sas_token'] = f'?{blob_container_sas_token}'

with open('config_resources.py','w') as file_resource:
    file_resource.write(f'resource_gpe_name = "{resource_gpe_name}"\n\n')
    file_resource.write(f'batch = ')
    json.dump(batch,file_resource,indent=4)
    file_resource.write('\n\nblob_container = ')
    json.dump(blob_container,file_resource,indent=4)