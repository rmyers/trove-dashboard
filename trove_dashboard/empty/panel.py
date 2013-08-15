from django.utils.translation import ugettext_lazy as _

import horizon

from trove_dashboard import dashboard


class Empty(horizon.Panel):
    name = _("Database Instances")
    slug = 'empty'
    permissions = ('openstack.services.database',)


dashboard.Dbaas.register(Empty)
