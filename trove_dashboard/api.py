"""
Simple Trove API
===================

This is meant to be a simple wrapper around the Trove API.

"""
import logging
from django.conf import settings
from troveclient import client
from troveclient.auth import ServiceCatalog
from trove_dashboard.tools.horizon_attrs import get_horizon_parameter


LOG = logging.getLogger(__name__)

client._logger.setLevel(get_horizon_parameter('TROVE_LOGLEVEL', True))


class TokenAuth(object):
    """Simple Token Authentication handler for trove api"""

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

def instance_delete(request, instance_id):
    return rdclient(request).instances.delete(instance_id)

def instance_create(request, name, volume, flavor, databases=None, users=None,
                    restore_point=None):
    vol = {'size': volume}
    return rdclient(request).instances.create(name, flavor, vol,
                                              databases=databases,
                                              users=users,
                                              restorePoint=restore_point)

def instance_restart(request, instance_id):
    return rdclient(request).instances.restart(instance_id)

def database_list(request, instance_id):
    return rdclient(request).databases.list(instance_id)

def backup_list(request, limit=None, marker=None):
    return rdclient(request).backups.list()

def backup_get(request, backup_id):
    return rdclient(request).backups.get(backup_id)

def backup_delete(request, backup_id):
    return rdclient(request).backups.delete(backup_id)

def backup_create(request, name, instance_id, description=None):
    return rdclient(request).backups.create(name, instance_id, description)

def flavor_list(request):
    return rdclient(request).flavors.list()

def flavor_get(request, flavor_id):
    return rdclient(request).flavors.get(flavor_id)
