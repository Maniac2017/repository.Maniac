# -*- coding: utf-8 -*-

from libs.tools import *
import threading


def run_plexus(id, title, ids):
    url = 'plugin://program.plexus/?mode=1&url=acestream://%s&name=%s' % (id, title)
    xbmc.executebuiltin('RunPlugin(' + url + ')')

    time.sleep(45)

    if xbmc.Player().isPlaying():
        xbmc.Player().stop()
        logger('%s: %s OK' % (title, id))
        ids[id] = title
    else:
        logger('%s: %s ERROR' % (title, id))


def mainmenu(item):
    ids = dict()
    threads = list()

    url = 'https://pastebin.com/raw/v7crBBsi'
    data = httptools.downloadpage(url).data

    patron = ".*?#EXTINF:-1 .*?,\s?\.?(.*?)\s?\(.*?acestream:\/\/(\w{40})"
    for title, id in re.findall(patron, data, re.DOTALL):
        if id in ids: continue

        t = threading.Thread(target=run_plexus, args=(id, title, ids))
        threads.append(t)
        logger('lanzando hilo')
        t.start()
        t.join()

    logger(ids)