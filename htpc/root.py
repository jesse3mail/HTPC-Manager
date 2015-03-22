#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Root for webserver. Specifies frontpage, errorpage (default),
and pages for restarting and shutting down server.
"""
import os
import sys
import cherrypy
import htpc
import logging
import urllib
from threading import Thread
from cherrypy.lib.auth2 import *


def do_restart():
    arguments = sys.argv[:]
    arguments.insert(0, sys.executable)
    if sys.platform == 'win32':
        arguments = ['"%s"' % arg for arg in arguments]
    os.chdir(os.getcwd())
    # Fix for rotation logs on windows
    logging.shutdown()
    os.execv(sys.executable, arguments)


class RestrictedArea:
    # all methods in this controller (and subcontrollers) is
    # open only to members of the admin group
    _cp_config = {
        'auth.require': [member_of('admin')]
    }


class Root(object):
    """ Root class """
    def __init__(self):
        """ Do nothing on load """
        self.logger = logging.getLogger('htpc.root')
        pass

    auth = AuthController()
    restricted = RestrictedArea()

    @cherrypy.expose()
    @require()
    def index(self):
        """ Load template for frontpage """
        return htpc.LOOKUP.get_template('dash.html').render(scriptname='dash')

    @cherrypy.expose()
    def default(self, *args, **kwargs):
        """ Show error if no matching page can be found """
        return "An error occured"

    @cherrypy.expose()
    @require(member_of("admin"))
    def shutdown(self):
        """ Shutdown CherryPy and exit script """
        self.logger.info("Shutting down htpc-manager.")
        cherrypy.engine.exit()
        # Fix for rotation logs on windows
        logging.shutdown()
        os._exit(0)
        return "HTPC Manager has shut down"

    @cherrypy.expose(alias='robots.txt')
    def robots(self):
        if htpc.settings.get('robots'):
            r = "User-agent: *\nDisallow: /\n"
        else:
            r = "User-agent: *\nDisallow: /logout/\nDisallow: /restart/\nDisallow: /shutdown/\nDisallow: /update/\n"
        return cherrypy.lib.static.serve_fileobj(r, content_type='text/plain', disposition=None, name='robots.txt', debug=False)

    @cherrypy.tools.json_out()
    @cherrypy.expose()
    @require()
    def restart(self):
        """ Shutdown script and rerun with the same variables """
        self.logger.info("Restarting htpc-manager.")
        Thread(target=do_restart).start()
        return "Restart in progress."

    @cherrypy.expose()
    @require()
    def logout(self, from_page="/"):
        sess = cherrypy.session
        username = sess.get(SESSION_KEY, None)
        sess[SESSION_KEY] = None
        if username:
            cherrypy.request.login = None
        raise cherrypy.HTTPRedirect(str(htpc.WEBDIR) or from_page)
        
    @cherrypy.tools.json_out()
    @cherrypy.expose()
    @require()
    def save_dash(self, dash_order=0):
        htpc.settings.set("dash_order", urllib.unquote(dash_order).decode('utf-8'))
        return "Dashboard saved."

    @cherrypy.tools.json_out()
    @cherrypy.expose()
    @require()
    def save_menu(self, menu_order=0):
        htpc.settings.set("menu_order", urllib.unquote(menu_order).decode('utf-8'))
        return "Menu order saved."
