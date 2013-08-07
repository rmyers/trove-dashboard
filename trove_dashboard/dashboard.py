from django.utils.translation import ugettext_lazy as _

import horizon

class TrovePanels(horizon.PanelGroup):
    slug = "database"
    name = _("Manage Databases")
    panels = ['databases', 'backup', ]


class Dbaas(horizon.Dashboard):
    name = _("Databases")
    slug = "database"
    panels = [TrovePanels]
    default_panel = 'databases'
    supports_tenants = True


horizon.register(Dbaas)