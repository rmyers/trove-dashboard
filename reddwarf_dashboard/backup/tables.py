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
from django.utils.translation import string_concat, ugettext_lazy as _

from horizon.conf import HORIZON_CONFIG
from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils.filters import replace_underscores

from reddwarf_dashboard import api


LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("COMPLETED", "FAILED")


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, backup_id):
        return api.backup_get(request, backup_id)


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
                         verbose_name=_("Name"))
    location = tables.Column("locationRef", verbose_name=_("Backup File"))
    instance = tables.Column("instance", verbose_name=_("Database"))
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
