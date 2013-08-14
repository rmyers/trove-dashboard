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

"""
Views for managing instances.
"""
import logging

from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon import tables
from horizon import workflows

from trove_dashboard import api
from .tabs import InstanceDetailTabs
from .tables import InstancesTable
from .tables import DatabaseTable
from .tables import UsersTable
from .workflows import LaunchInstance


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = InstancesTable
    template_name = 'dbaas/index.html'

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        marker = self.request.GET. \
            get(InstancesTable._meta.pagination_param, None)
        # Gather our instances
        try:
            instances = api.trove.instance_list(self.request, marker=marker)
            LOG.info(msg=_("Obtaining instances at %s class"
                           % repr(IndexView.__class__)))
            self._more = False
        except:
            self._more = False
            instances = []
            LOG.critical("Http 500. Internal server error. "
                         "Unable to retrieve instances.")
            return instances
            #exceptions.handle(self.request, ignore=True)
            # Gather our flavors and correlate our instances to them
        if instances:
            try:
                flavors = api.trove.flavor_list(self.request)
                LOG.info(msg=_("Obtaining flavor list from nova at %s class"
                               % repr(IndexView.__class__)))
            except:
                flavors = []
                LOG.critical(msg=_("Nova exception while obtaining "
                                   "flavor list at % class"
                                   % repr(IndexView.__class__)))
                exceptions.handle(self.request, ignore=True)

            full_flavors = SortedDict([(str(flavor.id), flavor)
                                       for flavor in flavors])
            # Loop through instances to get flavor info.
            for instance in instances:
                try:
                    flavor_id = instance.flavor["id"]
                    if flavor_id in full_flavors:
                        instance.full_flavor = full_flavors[flavor_id]
                    else:
                        # If the flavor_id is not in full_flavors list,
                        # get it via nova api.trove.
                        instance.full_flavor = api.trove.flavor_get(
                            self.request, flavor_id)
                except:
                    msg = _('Unable to retrieve instance size information')
                    LOG.critical(msg + _(" at %s class"
                                         % repr(IndexView.__class__)))
                    exceptions.handle(self.request, msg)
        return instances


class LaunchInstanceView(workflows.WorkflowView):
    workflow_class = LaunchInstance
    template_name = "dbaas/launch.html"

    def get_initial(self):
        initial = super(LaunchInstanceView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        return initial


class DetailView(tabs.TabbedTableView):
    tab_group_class = InstanceDetailTabs
    template_name = 'dbaas/detail.html'


    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["instance"] = self.get_data()
        return context

    def get_data(self):
        if not hasattr(self, "_instance"):
            try:
                instance_id = self.kwargs['instance_id']
                instance = api.trove.instance_get(self.request, instance_id)
                LOG.info(msg=_("Obtaining instance for detailed view "
                               "at %s class" % repr(DetailView.__class__)))
                instance.full_flavor = api.trove.flavor_get(
                    self.request, instance.flavor["id"])
            except:
                redirect = reverse('horizon:database:databases:index')
                LOG.critical(msg=_("Exception while btaining instance"
                                   " for detailed view at %s class"
                                   % repr(DetailView.__class__)))
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'instance "%s".') % instance_id,
                                  redirect=redirect)
            self._instance = instance
        return self._instance

    def get_tabs(self, request, *args, **kwargs):
        instance = self.get_data()
        return self.tab_group_class(request, instance=instance, **kwargs)
