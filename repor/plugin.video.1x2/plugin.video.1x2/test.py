# -*- coding: utf-8 -*-

from libs.tools import *


def mainmenu(item):
    itemlist = list()

    itemlist.append(item.clone(
        label='Test 1',
        action='test1'
    ))


    itemlist.append(item.clone(
        label='Test Youtube',
        action='play',
        VideoPlayer='youtube',
        url='play/?video_id=FuS_bXJNync'
    ))

    '''
    itemlist.append(item.clone(
        label='Test 2',
        action='test2'
    ))
    
    etc...
    '''

    return itemlist


def test1(item):
    # aqui hacemos algo y devolvemos un listado de items
    # por ejemplo una lista de enlaces

    itemlist = []

    itemlist.append(item.clone(
        label='Canal Historia',
        action='play',
        VideoPlayer='f4mtester',
        url= 'https://grifo5.mitopo.me/live/historia/index.m3u8?token=OoUorDNum_zI2tIF8OdIsA&expires=1569705595'
    ))

    itemlist.append(item.clone(
        label='#Vamos',
        action='play',
        VideoPlayer='f4mtester',
        url= 'https://petopa151.caraponi.me/live/vamos/index.m3u8?token=4yLF2NLvN_iPkpFKWABnRw&expires=1569706353'
    ))

    itemlist.append(item.clone(
        label='Multi1',
        action='play',
        VideoPlayer='f4mtester',
        url= 'http://isov.rogen.club/hls/live.m3u8'
    ))

    itemlist.append(item.clone(
        label='Test',
        action='play',
        VideoPlayer='f4mtester',
        url= 'http://stream.tvtap.live:8081/live/es-moviestarmotogp.stream/playlist.m3u8?wmsAuthSign=c2VydmVyX3RpbWU9MTAvMTEvMjAxOSAxMjoxMzowNCBBTSZoYXNoX3ZhbHVlPWRRbHN3QzdoMDlWSm5BY3FZak96MFE9PSZ2YWxpZG1pbnV0ZXM9MjA='
    ))


    return itemlist


def play(item):
    # Esta funcion devolvera el diccionario con los datos necesarios para q se reproduzca el enlace, por ejemplo:

    video_item = {'action': 'play',
           'titulo': 'Titulo del video',
           'url': item.url,
           'VideoPlayer': item.VideoPlayer # Actualmente podria ser: Directo, plexus, InputStream, Streamlink o F4mtester
           # se pueden añadir los pares clave/valor q sea necesario segun el VideoPlayer escogido
    }

    return video_item