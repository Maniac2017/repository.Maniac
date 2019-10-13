# -*- coding: utf-8 -*-

from libs.tools import *
from libs import jsunpack
import threading

def list_all_channels(item):
    itemlist = list()
    canales =list()

    canales.extend(get_channels_dailysport(item))
    canales.extend(get_channels_sportzonline(item))
    canales.extend(get_channels_sporttv(item))
    canales.extend(get_channels_live_sports_stream(item))


    for n, url_idioma in enumerate(canales):
        logger(url_idioma)
        label = '[COLOR red]Canal %s[/COLOR]' % (n + 1)

        itemlist.append(item.clone(
            label = (label + ' (%s)' % url_idioma[1]) if url_idioma[1] else label,
            title = 'Canales [COLOR red]24[/COLOR] - Canal %s' % (n+1),
            action='play',
            isPlayable=True,
            url=url_idioma[0]
        ))

    return itemlist


def get_channels_dailysport(item):
    threads = list()
    ret = []

    def get_online(canal, ret):
        data = httptools.downloadpage(canal[1]).data
        url = re.findall(".*?source:\s*'(.*?)'", data)
        if url and httptools.downloadpage(url[-1], headers={'Referer': canal[1]}).code == 200:
            ret.append(canal)


    for n in range(1,11):
        url = 'https://dailysport.pw/c%s.php' % n
        t = threading.Thread(target=get_online, args=((n,url), ret))
        threads.append(t)
        t.setDaemon(True)
        t.start()

    running = [t for t in threads if t.isAlive()]
    while running:
        time.sleep(0.5)
        running = [t for t in threads if t.isAlive()]

    return [(x[1],'') for x in sorted(ret, key=lambda x: x[0])]


def play__dailysport(item):
    url = None
    header = 'User-Agent=%s&Referer=%s' % (urllib.quote(httptools.default_headers["User-Agent"]),
                                           item.url)

    try:
        data = httptools.downloadpage(item.url).data
        url = re.findall(".*?source:\s*'(.*?)'", data)[-1]
        url = url + '|' + header

        return {'action': 'play', 'VideoPlayer': 'f4mtester', 'url': url, 'titulo': item.title}

    except:
        pass

    xbmcgui.Dialog().ok('1x2',
                        'Ups!  Parece que en estos momentos no hay nada que ver en este enlace.',
                        'Intentelo mas tarde o pruebe en otro enlace, por favor.')
    return None


def get_channels_sportzonline(item):
    idiomas = {1: "Ingles", 2: "Ingles", 3: "Aleman", 4: "Frances", 5: "Ingles", 6: "Español"}
    return [('https://sportzonline.co/channels/hd/hd%s.php' %n, idiomas[n]) for n in range(1, 7)]


def play_sportzonline(item):
    try:
        data = httptools.downloadpage(item.url).data
        url = 'https:' + re.findall('<iframe src="([^"]+)', data)[0]
        data = httptools.downloadpage(url, headers={'Referer': url}).data
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

        packed = re.findall('<script>(eval.*?)</script>', data)[0]
        url = re.findall('source:"([^"]+)',  jsunpack.unpack(packed))

        ret = {'action': 'play',
               'url': url[0],
               'VideoPlayer': 'f4mtester',
               'titulo': item.title}

        return ret

    except:
        pass

    xbmcgui.Dialog().ok('1x2',
                        'Ups!  Parece que en estos momentos no hay nada que ver en este enlace.',
                        'Intentelo mas tarde o pruebe en otro enlace, por favor.')
    return None


def get_channels_sporttv(item):
    a = [('https://sportzonline.co/channels/bra/br%s.php' %n, 'Brasileño') for n in range(1, 4)]
    a.extend([('https://v2.sportzonline.to/channels/pt/sporttv%s.php' %n, 'Portugues') for n in range(1, 6)])
    return a


def get_channels_live_sports_stream(item):
    #url = 'https://live-sports-stream.net/schedule/'

    threads = list()
    ret = []

    def get_online(canal, ret):
        data = httptools.downloadpage(canal[1]).data
        url = re.findall('<iframe src="([^"]+)"', data)
        if url:
            ret.append((canal[0],url[0]))


    for n in range(1,81):
        url = "https://live-sports-stream.net/embed/video.php?channel=%s" % n
        t = threading.Thread(target=get_online, args=((n,url), ret))
        threads.append(t)
        t.setDaemon(True)
        t.start()

    running = [t for t in threads if t.isAlive()]
    while running:
        time.sleep(0.5)
        running = [t for t in threads if t.isAlive()]

    return [(x[1],'') for x in sorted(ret, key=lambda x: x[0])]


def play_live_sports_stream(item):
    from random import choice
    data = httptools.downloadpage(item.url).data

    edges = choice(re.findall('"([^"]+)"', re.findall('window.edges = ([^;]+);',data)[0]))
    p = re.findall('var p = new SevenPlayer\("100%","100%","player","([^"]+)', data)[0]

    ret = {'action': 'play',
           'url': 'https://%s.weplaylive.stream/stream/%s/masterm.m3u8|referer=%s' %(edges, p, item.url),
           'VideoPlayer': 'f4mtester',
           'titulo': item.title}

    return ret


def play(item):
    logger(item)
    if 'dailysport.pw' in item.url:
        return play__dailysport(item)

    elif 'sportzonline' in item.url:
        return play_sportzonline(item)

    elif 'weplaylive.stream' in item.url:
        return play_live_sports_stream(item)