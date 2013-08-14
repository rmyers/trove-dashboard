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

from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon import workflows
from horizon.views import APIView

from trove_dashboard import api
from .tables import BackupsTable
from .workflows import CreateBackup
from horizon.views import APIView
from horizon import exceptions

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = BackupsTable
    template_name = 'dbaas/backup_index.html'

    def has_more_data(self, table):
        return self._more

    def _get_extra_data(self, backup):
        """Apply extra info to the backup."""
        instance_id = backup.instance_id
        if not hasattr(self, '_instances'):
            self._instances = {}
        instance = self._instances.get(instance_id)
        if instance is None:
            try:
                instance = api.instance_get(self.request, instance_id)
            except:
                instance = _('Not Found')
        backup.instance = instance
        return backup

    def get_data(self):
        marker = self.request.GET.get(BackupsTable._meta.pagination_param)
        try:
            backups = api.backup_list(self.request, marker=marker)
            backups = map(self._get_extra_data, backups)
            LOG.info(msg=_("Obtaining all backups "
                           "at %s class" % repr(IndexView.__class__)))
            self._more = False
        # TODO: (rmyers) Pagination is broken in trove api.
        except:
            self._more = False
            backups = []
            LOG.critical(msg=_("Exception while obtaining "
                               "all backups at %s class"
                               % repr(IndexView.__class__)))
        return backups
        # Gather all the instances for these backups


class BackupView(workflows.WorkflowView):
    workflow_class = CreateBackup
    template_name = "dbaas/backup.html"

    def get_context_data(self, **kwargs):
        context = super(BackupView, self).get_context_data(**kwargs)
        context["instance_id"] = kwargs.get("instance_id")
        self._instance = context['instance_id']
        return context


def parse_date(date_string):
    import datetime
    return datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S')


class DetailView(APIView):
    template_name = "dbaas/backup_details.html"

    def get_data(self, request, context, *args, **kwargs):
        backup_id = kwargs.get("backup_id")
        try:
            backup = api.backup_get(request, backup_id)
            backup.created_at = parse_date(backup.created)
            backup.updated_at = parse_date(backup.updated)
            backup.duration = backup.updated_at - backup.created_at
        except:
            exceptions.handle(request,
                              _('Unable to retrieve backup.'))
        try:
            instance = api.instance_get(request, backup.instance_id)
        except:
            instance = None
        context['backup'] = backup
        context['instance'] = instance
        return context
