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

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import glance
from openstack_dashboard.usage import quotas

from trove_dashboard import api as rd_api

LOG = logging.getLogger(__name__)


class SetInstanceDetailsAction(workflows.Action):
    name = forms.CharField(max_length=80, label=_("Database Name"))
    service_type = forms.ChoiceField(label=_("Service Type"),
                                     help_text=_("Type of database"))
    flavor = forms.ChoiceField(label=_("Flavor"),
                               help_text=_("Size of image to launch."))
    volume = forms.IntegerField(label=_("Volume Size"),
                               min_value=1,
                               initial=1,
                               help_text=_("Size of the volume in GB."))

    class Meta:
        name = _("Details")
        help_text_template = ("dbaas/_launch_details_help.html")

    def populate_service_type_choices(self, request, context):
        # TODO: make an api call for this!
        return [('mysql', 'mysql'), ('percona', 'percona')]

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
    contributes = ("name", "volume", "flavor", "service_type")


class AddDatabasesAction(workflows.Action):
    databases = forms.CharField(label=_('Initial Database'),
                                required=False,
                                help_text=_('Comma separated list of '
                                            'databases to create'))
    user = forms.CharField(label=_('Initial Admin User'),
                           required=False,
                           help_text=_("Initial admin user to add"))
    password = forms.CharField(widget=forms.PasswordInput(),
                               label=_("Password"),
                               required=False)
    host = forms.CharField(label=_("Host (optional)"),
                           required=False,
                           help_text=_("Host or IP that the user is allowed "
                                       "to connect through."))

    class Meta:
        name = _("Initialize Databases")
        help_text_template = ("dbaas/_launch_initialize_help.html")

    def clean(self):
        cleaned_data = super(AddDatabasesAction, self).clean()
        if cleaned_data.get('user') and not cleaned_data.get('password'):
            msg = _('You must specify a password if you create a user.')
            self._errors["password"] = self.error_class([msg])
        return cleaned_data

class InitializeDatabase(workflows.Step):
    action_class = AddDatabasesAction
    contributes = ["databases", 'user', 'password', 'host']


class RestoreAction(workflows.Action):
    backup = forms.ChoiceField(label=_("Backup"),
                               required=False,
                               help_text=_('Select a backup to Restore'))

    class Meta:
        name = _("Restore From Backup")
        help_text_template = ("dbaas/_launch_restore_help.html")

    def populate_backup_choices(self, request, context):
        empty = [('', '-')]
        try:
            backups = rd_api.backup_list(request)
            backup_list = [(b.id, b.name) for b in backups]
        except:
            backup_list = []
        return empty + backup_list

    def clean_backup(self):
        backup = self.cleaned_data['backup']
        if backup:
            try:
                # Make sure the user is not "hacking" the form
                # and that they have access to this backup_id
                bkup = rd_api.backup_get(self.request, backup)
                self.cleaned_data['backup'] = bkup.id
            except:
                raise forms.ValidationError(_("Unable to find backup!"))
        return self.cleaned_data


class RestoreBackup(workflows.Step):
    action_class = RestoreAction
    contributes = ['backup']


class LaunchInstance(workflows.Workflow):
    slug = "launch_database"
    name = _("Launch Database")
    finalize_button_name = _("Launch")
    success_message = _('Launched %(count)s named "%(name)s".')
    failure_message = _('Unable to launch %(count)s named "%(name)s".')
    success_url = "horizon:database:databases:index"
    default_steps = (SetInstanceDetails, InitializeDatabase, RestoreBackup)

    def format_status_message(self, message):
        name = self.context.get('name', 'unknown instance')
        return message % {"count": _("instance"), "name": name}

    def _get_databases(self, context):
        """Returns the initial databases for this instance."""
        databases = None
        if context['databases']:
            databases = [{'name': d} for d in context['databases'].split(',')]
        return databases

    def _get_users(self, context):
        users = None
        if context['user']:
            user = {'name': context['user'], 'password': context['password']}
            if context['host']:
                user['host'] = context['host']
            users = [user]
        return users

    def _get_backup(self, context):
        backup = None
        if context['backup']:
            backup = {'backupRef': context['backup']}
        return backup

    def handle(self, request, context):
        try:
            rd_api.instance_create(request,
                                   context['name'],
                                   context['volume'],
                                   context['flavor'],
                                   databases=self._get_databases(context),
                                   users=self._get_users(context),
                                   restore_point=self._get_backup(context))
            # TODO (rmyers): restore_point
            return True
        except:
            exceptions.handle(request)
            return False