trove-dashboard
==================

Horizon dashboard for the trove project.

Quickstart
----------

#. Install trove per: https://wiki.openstack.org/wiki/Trove-installation
#. Clone this repo to your machine.
#. Run ``python setup.py develop``
#. Run ``python setup.py sdist``
#. Edit ``horizon/openstack_dashboard/settings.py`` variable ``INSTALLED_APPS=(... , 'trove_dashboard',)``
#. Run the command: ``touch horizon/openstack_dashboard/wsgi/django.wsgi``
#. Log into to the horizon dashboard and make Databases.

Help
----

Use the source Luke!
