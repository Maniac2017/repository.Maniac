# -*- coding: utf-8 -*-

import urllib2
import datetime
from libs.tools import *


def evento_terminado(hora_evento_str):

    return False

def build_list(item):
    itemlist = []
    page = urllib2.urlopen(urllib2.Request(item.url, headers={'Accept': 'application/json'})).read()
    agenda = load_json(page)
    agenda = eval(agenda['snippet'])

    for evento in agenda:
        hora_evento = "%s %02d:%02d:00" % (evento['date'],int(evento['time'].split(':')[0]),int(evento['time'].split(':')[1]))
        if not evento['channels'] or evento_terminado(hora_evento):
            continue

        new_item = item.clone(
            label="%s %s (%s) %s" %(evento['date'],evento['time'], evento['competition'],evento['title']),
            title= evento['title']
        )

        if len(evento['channels']) == 1:
            new_item.action = 'play'
            new_item.url= 'plugin://program.plexus/?mode=1&url=%s&name=Video' % evento['channels'][0][0]
        else:
            new_item.action = 'list_options'
            new_item.options=evento['channels']


        itemlist.append(new_item)

    return itemlist


def list_options(item):
    itemlist = list()

    itemlist.append(item.clone(action=''))

    for i, op in enumerate(item.options):
        itemlist.append(item.clone(
            label='Opcion %s [%s]' %(i+1, op[2]),
            action='play',
            url = 'plugin://program.plexus/?mode=1&url=%s&name=Video' % op[0]
        ))

    return itemlist

