"""
Simple Reddwarf API
===================

This is meant to be a simple wrapper around the Reddwarf API.

"""

from django.conf import settings

from reddwarfclient import client
from reddwarfclient.auth import ServiceCatalog


class TokenAuth(object):
    """Simple Token Authentication handler for reddwarf api"""

    def __init__(self, client, auth_strategy, auth_url, username, password, 
                 tenant, region, service_type, service_name, service_url):
        # TODO (rmyers): handle some of these other args 
        self.username = username
        self.service_type = service_type
        self.service_name = service_name

    def authenticate(self):
        catalog = {
            'access': {
                'serviceCatalog': self.username.service_catalog,
                'token': {
                    'id': self.username.token.id,
                }
            }
        }
        return ServiceCatalog(catalog,
                              service_type=self.service_type,
                              service_name=self.service_name)


def rdclient(request):
    rdc = client.Dbaas(username=request.user, 
                       api_key='fake_api_key', 
                       auth_strategy=TokenAuth)
    return rdc

def instance_list(request, limit=None, marker=None):
    return rdclient(request).instances.list(limit=limit, marker=marker)

def instance_get(request, instance_id):
    return rdclient(request).instances.get(instance_id)

def instance_create(request, name, volume, flavor, databases=None, users=None,
                    restore_point=None):
    vol = {'size': volume}
    return rdclient(request).instances.create(name, flavor, vol,
                                              databases=databases,
                                              users=users,
                                              restorePoint=restore_point)

def backup_list(request):
    return rdclient(request).backups.list()

def flavor_list(request):
    return rdclient(request).flavors.list()

def flavor_get(request, flavor_id):
    return rdclient(request).flavors.get(flavor_id)