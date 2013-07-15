# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Rackspace Hosting
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

from django.template.defaultfilters import title
from django.utils.translation import ugettext_lazy as _

from horizon.conf import HORIZON_CONFIG
from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils.filters import replace_underscores

from trove_dashboard import api
from django.core import urlresolvers


LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("COMPLETED", "FAILED")


def date(string):
    """Strip off the T from the datetime string"""
    return string.replace('T', ' ')


class LaunchLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Backup")
    url = "horizon:database:backups:create"
    classes = ("btn-launch", "ajax-modal")

    def allowed(self, request, datum):
        return True  # The action should always be displayed


class RestoreLink(tables.LinkAction):
    name = "restore"
    verbose_name = _("Restore Backup")
    url = "horizon:database:databases:launch"
    classes = ("btn-launch", "ajax-modal")

    def get_link_url(self, datam):
        url = urlresolvers.reverse(self.url)
        return url + '?backup=%s' % datam.id


class DeleteBackup(tables.BatchAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Scheduled deletion of")
    data_type_singular = _("Backup")
    data_type_plural = _("Backups")
    classes = ('btn-danger', 'btn-terminate')

    def allowed(self, request, instance=None):
        return True

    def action(self, request, obj_id):
        api.backup_delete(request, obj_id)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, backup_id):
        backup = api.backup_get(request, backup_id)
        backup.instance = api.instance_get(request, backup.instanceRef)
        return backup


class BackupsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("COMPLETED", True),
        ("FAILED", True),
        ("suspended", True),
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
                            filters=[date])
    location = tables.Column("file", empty_value=_("Download"),
                             link=lambda obj: obj.locationRef,
                             verbose_name=_("Backup File"))
    instance = tables.Column(lambda obj: obj.instance.name, 
                             verbose_name=_("Database"))
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
        table_actions = (LaunchLink, DeleteBackup)
        row_actions = (RestoreLink, DeleteBackup)