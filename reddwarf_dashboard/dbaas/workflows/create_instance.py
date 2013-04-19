# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import json
import logging

from django.utils.text import normalize_newlines
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import glance
from openstack_dashboard.usage import quotas

from reddwarf_dashboard import api as rd_api

LOG = logging.getLogger(__name__)


class SetInstanceDetailsAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Database Name"))
    flavor = forms.ChoiceField(label=_("Flavor"),
                               help_text=_("Size of image to launch."))
    volume = forms.IntegerField(label=_("Volume Size"),
                               min_value=1,
                               initial=1,
                               help_text=_("Size of the volume in GB."))

    class Meta:
        name = _("Details")
        help_text_template = ("dbaas/_launch_details_help.html")

    def populate_flavor_choices(self, request, context):
        try:
            flavors = api.nova.flavor_list(request)
            flavor_list = [(flavor.id, "%s" % flavor.name)
                           for flavor in flavors]
        except:
            flavor_list = []
            exceptions.handle(request,
                              _('Unable to retrieve instance flavors.'))
        return sorted(flavor_list)

    def get_help_text(self):
        extra = {}
        try:
            extra['usages'] = quotas.tenant_quota_usages(self.request)
            extra['usages_json'] = json.dumps(extra['usages'])
            flavors = json.dumps([f._info for f in
                                       api.nova.flavor_list(self.request)])
            extra['flavors'] = flavors
        except:
            exceptions.handle(self.request,
                              _("Unable to retrieve quota information."))
        return super(SetInstanceDetailsAction, self).get_help_text(extra)


class SetInstanceDetails(workflows.Step):
    action_class = SetInstanceDetailsAction
    contributes = ("name", "volume", "flavor")


class AddDatabasesAction(workflows.Action):
    database_name = forms.CharField(label=_('Initial Database'),
                                    required=False,
                                    help_text=_('Create initial database'))

    class Meta:
        name = _("Initialize Databases")
        help_text_template = ("dbaas/_launch_initialize_help.html")

class InitializeDatabase(workflows.Step):
    action_class = AddDatabasesAction
    contributes = ["database_name"]


class RestoreAction(workflows.Action):
    backup = forms.ChoiceField(label=_("Backup"),
                               required=False,
                               help_text=_('Select a backup to Restore'))

    class Meta:
        name = _("Restore From Backup")
        help_text_template = ("dbaas/_launch_restore_help.html")

    def populate_restore_point_choices(self, request, context):
        try:
            backups = rd_api.backup_list(request)
            # TODO (rmyers): add in the date/sort by the latest?
            backup_list = [(b.id, b.name) for b in backups]
        except:
            backup_list = []
        return backup_list


class RestoreBackup(workflows.Step):
    action_class = RestoreAction
    contributes = ['backup']


class LaunchInstance(workflows.Workflow):
    slug = "launch_database"
    name = _("Launch Database")
    finalize_button_name = _("Launch")
    success_message = _('Launched %(count)s named "%(name)s".')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:database"
    default_steps = (SetInstanceDetails, InitializeDatabase, RestoreBackup)

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        return message % {"count": _("instance"), "name": name}

    def handle(self, request, context):
        try:
            rd_api.instance_create(request,
                                   context['name'],
                                   context['volume'],
                                   context['flavor'])
            # TODO (rmyers): handle databases, users, restore_point
            return True
        except:
            exceptions.handle(request)
            return False
