# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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

"""
Views for displaying database backups.
"""
import logging

from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon import tables
from horizon import workflows

from trove_dashboard import api
from .tables import BackupsTable
from .workflows import CreateBackup


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = BackupsTable
    template_name = 'dbaas/backup_index.html'

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        marker = self.request.GET.get(BackupsTable._meta.pagination_param)
        try:
            real_backups = api.backup_list(self.request, marker=marker)
            self._more = False
            instances = {}
            for backup in real_backups:
                LOG.error(dir(backup))
                instance_id = backup.instance_id
                instances[instance_id] = api.instance_get(self.request, instance_id)
                backup.instance_id = (instances.get(instance_id)).name
            return real_backups
        except:
            self._more = False
            backups = []
            exceptions.handle(self.request,
                              _('Unable to retrieve backups.'))
        # Gather all the instances for these backups



class BackupView(workflows.WorkflowView):
    workflow_class = CreateBackup
    template_name = "dbaas/backup.html"

    def get_context_data(self, **kwargs):
        context = super(BackupView, self).get_context_data(**kwargs)
        context["instance_id"] = kwargs.get("instance_id")
        self._instance = context['instance_id']
        return context