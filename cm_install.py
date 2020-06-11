#!/bin/env python3 
import cm_client
import json
import hashlib
import time
from optparse import OptionParser
from cm_client.rest import ApiException
from collections import namedtuple
from pprint import pprint

# API can be called from the browser: http://192.168.0.182:7180/api/v41/cm/deployment

# https://cloudera.github.io/cm_api/docs/python-client-swagger/
# https://archive.cloudera.com/cm7/7.0.3/generic/jar/cm_api/swagger-html-sdk-docs/python/README.html

# https://github.com/mkby/myinstaller/blob/master/deploy_cdh.py
# https://gist.github.com/gdgt/d2eb4abe39da05353a58451c103f41e5

hostname = None
password = None
localrepo = False
parcelsuri = ''

# Configure HTTP basic authorization: basic
cm_client.configuration.username = 'admin'
cm_client.configuration.password = 'admin'

# Path of truststore file in PEM
cm_client.configuration.verify_ssl = True
cm_client.configuration.ssl_ca_cert = '/var/lib/cloudera-scm-server/certmanager/trust-store/cm-auto-in_cluster_ca_cert.pem'

# Construct base URL for API
api_host = 'http://localhost'
port = '7180'
api_version = 'v41'
api_url = api_host + ':' + port + '/api/' + api_version
api_client = cm_client.ApiClient(api_url)


def saveClusterTemplate():
    cluster_api_instance = cm_client.ClustersResourceApi(api_client)

    # Lists all known clusters.
    api_response = cluster_api_instance.read_clusters(view='SUMMARY')
    cluster_name = ''
    for cluster in api_response.items:
        cluster_name = cluster.name
        template = cluster_api_instance.export(cluster_name)

        json_dict = api_client.sanitize_for_serialization(template)
        with open('/tmp/cluster_template.json', 'w') as out_file:
            json.dump(json_dict, out_file, indent=4, sort_keys=True)

        print(cluster.name, "-", cluster.full_version)

def acceptTrial():
    api_instance = cm_client.ClouderaManagerResourceApi(api_client)

    try:
        api_instance.begin_trial()
    except ApiException as e:
        print("Exception when calling ClouderaManagerResourceApi->begin_trial: %s\n" % e)

def loadLocalRepo():
    new_parcel_repo_urls = parcelsuri

    cm_api_instance = cm_client.ClouderaManagerResourceApi(api_client)
    cm_configs = cm_api_instance.get_config(view='full')
    
    new_cm_config = cm_client.ApiConfig(name='REMOTE_PARCEL_REPO_URLS', value=new_parcel_repo_urls)
    new_cm_configs = cm_client.ApiConfigList([new_cm_config])
    updated_cm_configs = cm_api_instance.update_config(body=new_cm_configs)

def appendRemoteRepo():
    new_parcel_repo_urls = parcelsuri

    cm_api_instance = cm_client.ClouderaManagerResourceApi(api_client)
    cm_configs = cm_api_instance.get_config(view='full')
    old_parcel_repo_urls = None
    for cm_config in cm_configs.items:
        if cm_config.name == 'REMOTE_PARCEL_REPO_URLS':
            old_parcel_repo_urls = cm_config.value

    new_parcel_repo_urls = old_parcel_repo_urls + ',' + parcelsuri
    cm_api_instance = cm_client.ClouderaManagerResourceApi(api_client)
    cm_configs = cm_api_instance.get_config(view='full')

    new_cm_config = cm_client.ApiConfig(name='REMOTE_PARCEL_REPO_URLS', value=new_parcel_repo_urls)
    new_cm_configs = cm_client.ApiConfigList([new_cm_config])
    updated_cm_configs = cm_api_instance.update_config(body=new_cm_configs)

def loadTemplateThenInstall():
    # Load the updated cluster template
    with open('/tmp/cluster_template.json') as in_file:
        json_str = in_file.read()
    # Following step is used to deserialize from json to python API model object
    Response = namedtuple("Response", "data")
    dst_cluster_template=api_client.deserialize(response=Response(json_str), response_type=cm_client.ApiClusterTemplate)

    cm_api_instance = cm_client.ClouderaManagerResourceApi(api_client)
    command = cm_api_instance.import_cluster_template(body=dst_cluster_template)

def get_host_resource(hostname):
    api_instance = cm_client.HostsResourceApi(api_client)
    try:
        # Returns the hostIds for all hosts in the system.
        # api_response = api_instance.read_hosts(view=view)
        api_host_response = [x for x in api_instance.read_hosts(view='summary').items
                             if hostname == x.hostname]
    except ApiException as e:
        print("Exception when calling HostsResourceApi->read_hosts: %s\n" % e)

    return api_host_response[0]

def setupCMS():
    service_name = 'mgmt'
    service_type = 'MGMT'.upper()

    api_instance = cm_client.MgmtServiceResourceApi(api_client)

    services_instance = cm_client.MgmtServiceResourceApi(api_client)
    mgmt_role_instance = cm_client.MgmtRolesResourceApi(api_client)
    rcg_instance = cm_client.MgmtRoleConfigGroupsResourceApi(api_client)

    services_instance.setup_cms(body=cm_client.ApiService(name=service_name, type=service_type, display_name='Cloudera Management Service'))
    host_id = getattr(get_host_resource(hostname), 'host_id', None)

    role_list = []
    for role_type in ["REPORTSMANAGER", "EVENTSERVER", "HOSTMONITOR", "ALERTPUBLISHER", "SERVICEMONITOR"]:
        role_name = service_name + "-" + role_type + "-" + hashlib.md5(hostname.encode('utf-8')).hexdigest()
        role_list.append({"name": role_name, "type": role_type, "hostRef": {"hostId": host_id}})

    body = cm_client.ApiRoleList(role_list)
    api_response = mgmt_role_instance.create_roles(body=body)

    api_response = rcg_instance.read_role_config_groups()
    for rcg in api_response.items:
        if rcg.role_type == 'REPORTSMANAGER':
            rcg_instance.update_config(rcg.name, message=None,
                                           body=cm_client.ApiConfigList([
                                                   {'name': 'headlamp_database_host', 'value': hostname},
                                                   {'name': 'headlamp_database_name', 'value': 'rman'},
                                                   {'name': 'headlamp_database_user', 'value': 'rman'},
                                                   {'name': 'headlamp_database_password', 'value': 'supersecret1'},
                                                   {'name': 'headlamp_database_type', 'value': 'postgresql'}
                                               ]))

    services_instance.start_command()

if __name__ == "__main__":
    optp = OptionParser()
    optp.add_option("-n", "--hostname",     dest="hostname",     help="Hostname of the system")
    optp.add_option("-b", "--cdponly" ,     dest="cdponly",      help="Install only CDP")
    optp.add_option("-l", "--localrepo",    dest="localrepo",    help="Use local repositories")
    optp.add_option("-c", "--parcelsuri",   dest="parcelsuri",   help="URLS of parcel location")
    optp.add_option("-p", "--password",     dest="password",     help="Password to user")
    opts, args = optp.parse_args()

    if opts.hostname:
        hostname = str(opts.hostname)

    if opts.localrepo:
        localrepo = opts.localrepo

    if opts.parcelsuri:
        parcelsuri = opts.parcelsuri

    if opts.password:
        password = opts.password

    print("Hostname: " + hostname)

    print("Accepting the trial license")
    acceptTrial()

    if str(localrepo) == '1':
        if str(parcelsuri) != '': 
            print("Load a new local parcel repository location")
            loadLocalRepo()

    if str(parcelsuri) == '':
        parcelsuri = 'https://archive.cloudera.com/cdh7/7.1.1.0/parcels/'
    else:
        parcelsuri = 'https://archive.cloudera.com/cdh7/7.1.1.0/parcels/,' + parcelsuri

    print("Adding additional remote parcel repos")
    appendRemoteRepo()

    print("Sleeping for 10 seconds")
    time.sleep(10)
    
    print("Loading template then starting automated install")
    loadTemplateThenInstall()
    
    print("Setting up Cloudera Management Service")
    setupCMS()
