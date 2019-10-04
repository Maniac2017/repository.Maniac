# -*- coding: utf-8 -*-

from libs.tools import *


def list_all_channels(item):
    itemlist = list()

    for d in ['https://dailysport.pw', 'http://acestreampi.ddns.net/sports.php']:
        data = httptools.downloadpage(d).data

        canales = sorted(set(re.findall("<a href=([^>]+)>Channel (\d+) (.*?)</a>", data)), key=lambda c: int(c[1]))
        for url, n, idioma in canales:
            itemlist.append(item.clone(
                label='[COLOR red]Canal %s %s[/COLOR]' % (n, idioma),
                canal=n,
                action='play',
                isPlayable=True,
                url=('https://dailysport.pw/' + url) if not 'dailysport.pw' in url else url.replace("'", "")
            ))
        if itemlist: break

    return itemlist


def play(item):
    url = None
    header = 'User-Agent=%s&Referer=%s' % (urllib.quote(httptools.default_headers["User-Agent"]),
                                           'https://dailysport.pw/c%s.php' % item.canal)

    if item.url.endswith('.m3u8'):
        url = item.url
    else:
        try:
            data = httptools.downloadpage(item.url).data
            url = re.findall(".*?source:\s*'(.*?)'", data)[-1]
        except:
            pass

    if url:
        url = url + '|' + header
        return {'action': 'play', 'VideoPlayer': 'f4mtester', 'url': url, 'titulo': item.label}

    xbmcgui.Dialog().ok('1x2',
                        'Ups!  Parece que en estos momentos no hay nada que ver en este enlace.',
                        'Intentelo mas tarde o pruebe en otro enlace, por favor.')
    return None