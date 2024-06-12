#!/usr/bin/python3
# -*- coding:utf8 -*-
#/bin/env python


import sys, os
import argparse
import re
import datetime
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__
USAGE = 'usage: ' + sys.argv[0] + ' -d <path to the dump of database>' # -e <environment of deployment>'
parser = argparse.ArgumentParser(description='Backup archiving: The connection string must be in environment variables as AZURE_STORAGE_CONNECTION_STRING')
parser.add_argument('-d', '--dump', dest='dump', help='path to the dump of database')
#parser.add_argument('-e', '--env', dest='env', help='environment of deployment')
args = parser.parse_args()

#test input dump 
if args.dump == None:
    print('No file specified') 
    print(USAGE)
    sys.exit(1) 
if re.match('^.*\.sql$', args.dump) == None:
    print('the file must be compressed sql file')
    print(USAGE)
    sys.exit(1)
if not os.path.isfile(args.dump):
    print("The file doesn't exist")
    print(USAGE)
    sys.exit(1)

#test input env
# env_list = ['dev','int','sbx','ppr','prd']
# if args.env == None:
#     print('No environment specified') 
#     print(USAGE)
#     sys.exit(1) 
# if re.match('^[a-z][a-z][a-z]$', args.env) == None:
#     print('env must be a trigram')
#     print(USAGE)
#     sys.exit(1)
# if not args.env in env_list:
#     print(args.env + " environment doesn't exist")
#     print(USAGE)
#     sys.exit(1)
# env = args.env

dump = args.dump
dump_path = dump.split('/')
local_file_name = dump_path[-1]

connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
if connect_str == None:
    print('No connection string specified : The connection string must be in environment variables as AZURE_STORAGE_CONNECTION_STRING')
    sys.exit(2) 
if re.match('^DefaultEndpointsProtocol=https;AccountName=.*AccountKey=.*EndpointSuffix=.*$', connect_str) == None:
    print('Wrong format: The connection string must be in environment variables as AZURE_STORAGE_CONNECTION_STRING="<yourconnectionstring>"')
    sys.exit(2)
# Create the BlobServiceClient object which will be used to create a container client
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

container_name = "backup-telediagnostic-sql" 
# search backup container in account
containers = blob_service_client.list_containers()
containers_list = []
container = None
for c in containers:
    containers_list.append(c.name)
    if container_name == c.name:
        container = c

if container_name in containers_list:
    print("The container " + container_name + " exists")
    
    container_client = blob_service_client.get_container_client(container)
else:
    # Create the container
    container_client = blob_service_client.create_container(container_name)

blobs = container_client.list_blobs()
blobs_list= []
for blob in blobs:
    
    #delete backup older than 2 month
    twomonthsago = datetime.date.today() - datetime.timedelta(days=60)
    #print(twomonthsago)
    if blob.creation_time.date() < twomonthsago :
        print("deleting " + blob.name)
        container_client.delete_blob(blob)
    else:
        # Create blob name list 
        blobs_list.append(blob.name)

if local_file_name in blobs_list:
    print("The blob " + local_file_name + " exists")
    # sys.exit(0)
else:
    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)
    print("\nUploading to Azure Storage as blob:\n\t" + local_file_name)
    
    # Upload the created file
    with open(dump, "rb") as data:
        blob_client.upload_blob(data)
