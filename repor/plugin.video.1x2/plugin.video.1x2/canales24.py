# -*- coding: utf-8 -*-

import urllib, urllib2
import re

from libs.tools import *

# v2
def list_all_channels(item):
    itemlist = list()

    data = httptools.downloadpage('https://dailysport.pw').data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    canales = sorted(set(re.findall('<a href="([^"]+)">Channel (\d+) (.*?)</a>', data)), key=lambda c: c[1])
    for url, n, idioma in canales:
        itemlist.append(item.clone(
            label='[COLOR red]Canal %s %s[/COLOR]' % (n, idioma),
            action='play',
            isPlayable=True,
            url='https://dailysport.pw/' + url
        ))

    return itemlist


def play(item):
    header = 'User-Agent=%s&Referer=%s' % (urllib.quote(httptools.default_headers["User-Agent"]), item.url)

    data = httptools.downloadpage(item.url).data
    patron = ".*?source: '(.*?)'"
    url = re.findall(patron, data)

    if url:
        url = url[-1] + '|' + header
        return {'action': 'play', 'VideoPlayer': 'f4mtester', 'url': url, 'titulo': item.label} #, 'callbackpath': __file__,'callbackparam': (item.url, item.key)}

    xbmcgui.Dialog().ok('1x2',
                        'Ups!  Parece que en estos momentos no hay nada que ver en este enlace.',
                        'Intentelo mas tarde o pruebe en otro enlace, por favor.')
    return None