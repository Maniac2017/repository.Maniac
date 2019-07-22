# -*- coding: utf-8 -*-

import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import base64
import json
import copy
import datetime
import time
import urllib

runtime_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('Path'))
image_path = os.path.join(runtime_path,'resources', 'media', 'img')

class Item(object):
    defaults = {}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __contains__(self, item):
        return item in self.__dict__

    def __getattribute__(self, item):
        return object.__getattribute__(self, item)

    def __getattr__(self, item):
        if item.startswith("__"):
            return object.__getattribute__(self, item)
        else:
            return self.defaults.get(item, '')

    def __str__(self):
        return '{%s}' % (', '.join(['\'%s\': %s' % (k, repr(self.__dict__[k])) for k in sorted(self.__dict__.keys())]))

    def getart(self):
        if 'fanart' not in self.__dict__:
            self.__dict__['fanart'] = os.path.join(runtime_path,'fanart.jpg')

        return [(k,self.__dict__.get(k)) for k in ['poster', 'icon', 'fanart', 'thumb'] if k in self.__dict__]

    def tourl(self):
        dump = repr(self.__dict__)
        return urllib.quote(base64.b64encode(dump))

    def fromurl(self, url):
        str_item = base64.b64decode(urllib.unquote(url))
        self.__dict__.update(eval(str_item))
        return self

    def tojson(self, path=""):
        if path:
            open(path, "wb").write(dump_json(self.__dict__))
        else:
            return dump_json(self.__dict__)

    def fromjson(self, json_item=None, path=""):
        if path:
            json_item = open(path, "rb").read()

        if type(json_item) == str:
            item = load_json(json_item)
        else:
            item = json_item
        self.__dict__.update(item)
        return self

    def clone(self, **kwargs):
        newitem = copy.deepcopy(self)
        for k, v in kwargs.items():
            setattr(newitem, k, v)
        return newitem


class proxydt(datetime.datetime):
    def __init__(self, *args, **kwargs):
        super(proxydt, self).__init__(*args, **kwargs)

    @staticmethod
    def strptime(date_string, format):
        return datetime.datetime(*(time.strptime(date_string, format)[0:6]))

datetime.datetime = proxydt
dump = datetime.datetime.strptime('20110101', '%Y%m%d')


def logger(message, level=None):
    def encode_log(message=""):
        if type(message) == unicode:
            message = message.encode("utf8")
        elif type(message) == str:
            message = unicode(message, "utf8", errors="replace").encode("utf8")
        else:
            message = str(message)
        return message

    texto = '[%s] %s' %(xbmcaddon.Addon().getAddonInfo('id'), encode_log(message))
    if level == 'info':
        xbmc.log(texto, xbmc.LOGNOTICE)
    elif level == 'error':
        xbmc.log("######## ERROR #########", xbmc.LOGERROR)
        xbmc.log(texto, xbmc.LOGERROR)
    else:
        xbmc.log("######## DEBUG #########", xbmc.LOGNOTICE)
        xbmc.log(texto, xbmc.LOGNOTICE)


def load_json(*args, **kwargs):
    def to_utf8(dct):
        if isinstance(dct, dict):
            return dict((to_utf8(key), to_utf8(value)) for key, value in dct.iteritems())
        elif isinstance(dct, list):
            return [to_utf8(element) for element in dct]
        elif isinstance(dct, unicode):
            return dct.encode('utf-8')
        else:
            return dct

    if "object_hook" not in kwargs:
        kwargs["object_hook"] = to_utf8

    try:
        value = json.loads(*args, **kwargs)
    except Exception:
        logger('Error en load_json', 'error')
        value = {}

    return value


def dump_json(*args, **kwargs):
    if not kwargs:
        kwargs = {
            'indent': 4,
            'skipkeys': True,
            'sort_keys': True,
            'ensure_ascii': False
        }

    try:
        value = json.dumps(*args, **kwargs)
    except Exception:
        logger('Error en dump_json', 'error')
        value = ''

    return value


def get_setting(name, default=None):
    value = xbmcaddon.Addon().getSetting(name)

    if not value:
        return default

    elif value == 'true':
        return True

    elif value == 'false':
        return False

    else:
        try:
            value = int(value)
        except ValueError:
            try:
                value = long(value)
            except ValueError:
                pass
        return value


def set_setting(name, value):
    try:
        if isinstance(value, bool):
            if value:
                value = "true"
            else:
                value = "false"

        elif isinstance(value, (int, long)):
            value = str(value)

        xbmcaddon.Addon().setSetting(name, value)

    except Exception, ex:
        logger("Error al convertir '%s' no se guarda el valor \n%s" % (name, ex), 'error')
        return None

    return value
