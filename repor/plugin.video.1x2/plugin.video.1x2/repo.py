# -*- coding: utf-8 -*-

import urllib, re, requests, xbmcgui, xbmc, xbmcaddon, time
import os

def forceUpdate(silent=False):
    ebi('UpdateAddonRepos()')
    ebi('UpdateLocalAddons()')
    if silent == False: LogNotify("[COLOR %s]%s[/COLOR]" % (COLOR1, ADDONTITLE), '[COLOR %s]Forzando actualizacion 1x2[/COLOR]' % COLOR2)


def ebi(proc):
    xbmc.executebuiltin(proc)
