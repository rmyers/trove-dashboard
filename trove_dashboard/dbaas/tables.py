# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from django.core import urlresolvers
from django.core.urlresolvers import reverse
from django.template.defaultfilters import title, join
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils.filters import replace_underscores

from trove_dashboard import api
from ..backup.tables import LaunchLink as LaunchBackup
from ..backup.tables import DeleteBackup
from ..backup.tables import RestoreLink


LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("ACTIVE",)

POWER_STATES = {
    0: "NO STATE",
    1: "RUNNING",
    2: "BLOCKED",
    3: "PAUSED",
    4: "SHUTDOWN",
    5: "SHUTOFF",
    6: "CRASHED",
    7: "SUSPENDED",
    8: "FAILED",
    9: "BUILDING",
}

PAUSE = 0
UNPAUSE = 1
SUSPEND = 0
RESUME = 1


class TerminateInstance(tables.BatchAction):
    name = "terminate"
    action_present = _("Terminate")
    action_past = _("Scheduled termination of")
    data_type_singular = _("Instance")
    data_type_plural = _("Instances")
    classes = ('btn-danger', 'btn-terminate')

    def allowed(self, request, instance=None):
        return True

    def action(self, request, obj_id):
        api.instance_delete(request, obj_id)


class RestartInstance(tables.BatchAction):
    name = "restart"
    action_present = _("Restart")
    action_past = _("Restarted")
    data_type_singular = _("Database")
    data_type_plural = _("Databases")
    classes = ('btn-danger', 'btn-reboot')

    def allowed(self, request, instance=None):
        return ((instance.status in ACTIVE_STATES
                 or instance.status == 'SHUTOFF'))

    def action(self, request, obj_id):
        api.instance_restart(request, obj_id)


class DeleteUser(tables.DeleteAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Deleted")
    data_type_singular = _("User")
    data_type_plural = _("Users")

    def delete(self, request, obj_id):
        datum = self.table.get_object_by_id(obj_id)
        api.users_delete(request, datum.instance.id, datum.name)


class DeleteDatabase(tables.DeleteAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Deleted")
    data_type_singular = _("Database")
    data_type_plural = _("Databases")

    def delete(self, request, obj_id):
        datum = self.table.get_object_by_id(obj_id)
        api.database_delete(request, datum.instance.id, datum.name)


class LaunchLink(tables.LinkAction):
    name = "launch"
    verbose_name = _("Launch Instance")
    url = "horizon:database:databases:launch"
    classes = ("btn-launch", "ajax-modal")

    def allowed(self, request, datum):
        return True  # The action should always be displayed


class CreateBackup(tables.LinkAction):
    name = "backup"
    verbose_name = _("Create Backup")
    url = "horizon:database:backups:create"
    classes = ("ajax-modal", "btn-camera")

    def allowed(self, request, instance=None):
        return instance.status in ACTIVE_STATES

    def get_link_url(self, datam):
        url = urlresolvers.reverse(self.url)
        return url + "?instance=%s" % datam.id

class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, instance_id):
        instance = api.instance_get(request, instance_id)
        instance.full_flavor = api.flavor_get(request, instance.flavor['id'])
        return instance


def get_ips(instance):
    if hasattr(instance, "ip"):
        if len(instance.ip):
            return instance.ip[0]
    return _("Not Assigned")


def get_size(instance):
    if hasattr(instance, "full_flavor"):
        size_string = _("%(name)s | %(RAM)s RAM")
        vals = {'name': instance.full_flavor.name,
                'RAM': sizeformat.mbformat(instance.full_flavor.ram)}
        return size_string % vals
    return _("Not available")


STATUS_DISPLAY_CHOICES = (
    ("resize", "Resize/Migrate"),
    ("verify_resize", "Confirm or Revert Resize/Migrate"),
    ("revert_resize", "Revert Resize/Migrate"),
)


class InstancesTable(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("shutoff", True),
        ("suspended", True),
        ("paused", True),
        ("error", False),
    )
    name = tables.Column("name",
                         link=("horizon:database:databases:detail"),
                         verbose_name=_("Database Name"))
    ip = tables.Column(get_ips, verbose_name=_("IP Address"))
    size = tables.Column(get_size,
                         verbose_name=_("Size"),
                         attrs={'data-type': 'size'})
    status = tables.Column("status",
                           filters=(title, replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    class Meta:
        name = "databases"
        verbose_name = _("Databases")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (LaunchLink, TerminateInstance)
        row_actions = (CreateBackup,
                       RestartInstance, TerminateInstance)


class UsersTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("User Name"))
    host = tables.Column("host", verbose_name=_("Allowed Hosts"))
    databases = tables.Column("databases", verbose_name=_("Databases"))

    class Meta:
        name = "users"
        verbose_name = _("Database Instance Users")
        table_actions = [DeleteUser]
        row_actions = [DeleteUser]

    def get_object_id(self, datum):
        return datum.name


class DatabaseTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Database Name"))

    class Meta:
        name = "databases"
        verbose_name = _("Databases")
        table_actions = [DeleteDatabase]
        row_actions = [DeleteDatabase]

    def get_object_id(self, datum):
        return datum.name


class InstanceBackupsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("COMPLETED", True),
        ("FAILED", True),
        ("NEW", False),
        ("paused", True),
        ("error", False),
    )
    STATUS_DISPLAY_CHOICES = (
        ('foo', 'Bar'),
    )
    name = tables.Column("name",
                         link=("horizon:database:backups:detail"),
                         verbose_name=_("Name"))
    created = tables.Column("created", verbose_name=_("Created At"),
                            filters=None)
    location = tables.Column(lambda obj: _("Download"),
                             link=lambda obj: obj.locationRef,
                             verbose_name=_("Backup File"))
    status = tables.Column("status",
                           filters=(title, replace_underscores),
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    class Meta:
        name = "backups"
        verbose_name = _("Backups")
        status_columns = ["status"]
        row_class = UpdateRow
        table_actions = (LaunchBackup, DeleteBackup)
        row_actions = (RestoreLink, DeleteBackup)
