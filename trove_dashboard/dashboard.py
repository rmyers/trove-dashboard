from django.utils.translation import ugettext_lazy as _

import horizon


class TrovePanels(horizon.PanelGroup):
    slug = "database"
    name = _("Manage Databases")
    panels = ['databases', 'database_backups', 'empty']


class Dbaas(horizon.Dashboard):
    name = _("Databases")
    slug = "database"
    panels = [TrovePanels]
    default_panel = 'empty'
    supports_tenants = True


horizon.register(Dbaas)
