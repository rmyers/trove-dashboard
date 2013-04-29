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
from django.template.defaultfilters import title
from django.utils.translation import string_concat, ugettext_lazy as _

from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils.filters import replace_underscores

from reddwarf_dashboard import api


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
