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

import json
import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from trove_dashboard import api

LOG = logging.getLogger(__name__)


class BackupDetailsAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Name"))
    instance = forms.ChoiceField(label=_("Database Instance"))
    description = forms.CharField(max_length=512, label=_("Description"),
                                  widget=forms.TextInput(),
                                  required=False,
                                  help_text=_("Optional Backup Description"))

    class Meta:
        name = _("Details")
        help_text_template = ("dbaas/_backup_details_help.html")

    def populate_instance_choices(self, request, context):
        instances = api.instance_list(request, limit=100)
        LOG.info(msg=_("Obtaining list of instances with limit 100 per page at %s class "
                       % repr(BackupDetailsAction.__class__)))
        return [(i.id, i.name) for i in instances]


class SetBackupDetails(workflows.Step):
    action_class = BackupDetailsAction
    contributes = ["name", "description", "instance"]


class CreateBackup(workflows.Workflow):
    slug = "create_backup"
    name = _("Backup Database")
    finalize_button_name = _("Backup")
    success_message = _('Scheduled backup "%(name)s".')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:database:backups:index"
    default_steps = [SetBackupDetails]

    def get_initial(self):
        initial = super(CreateBackup, self).get_initial()
        initial['instance_id']

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        return message % {"count": _("instance"), "name": name}

    def handle(self, request, context):
        try:
            api.backup_create(request,
                              context['name'],
                              context['instance'],
                              context['description'])
            LOG.info(msg=_("Creating backup at %s class" % repr(CreateBackup.__class__)))
            return True
        except:
            LOG.critical(_("Exception while creating backup at %s class"
                           % repr(CreateBackup.__class__)))
            exceptions.handle(request)
            return False
