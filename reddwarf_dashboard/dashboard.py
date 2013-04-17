from django.utils.translation import ugettext_lazy as _

import horizon


class ReddwarfPanels(horizon.PanelGroup):
    slug = "database"
    name = _("Manage Databases")
    panels = ['dbaas']


class Dbaas(horizon.Dashboard):
    name = _("Database")
    slug = "database"
    panels = [ReddwarfPanels]
    default_panel = 'databases'
    supports_tenants = True


horizon.register(Dbaas)