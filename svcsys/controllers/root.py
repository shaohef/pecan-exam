# -*- coding: UTF-8 -*-
# UTF-8 no need for template, we can remove it.

from pecan import expose, redirect
from webob.exc import status_map
from svcsys.controllers.svcsystem import ips


class RootController(object):

    ips = ips.SystemIPController()

    @expose(generic=True, template='demo.html')
    def index(self):
        return dict()

    @index.when(method='POST')
    def index_post(self, q):
        redirect('https://pecan.readthedocs.io/en/latest/search.html?q=%s' % q)

    @expose('error.html')
    def error(self, status):
        try:
            status = int(status)
        except ValueError:  # pragma: no cover
            status = 500
        message = getattr(status_map.get(status), 'explanation', '')
        return dict(status=status, message=message)
