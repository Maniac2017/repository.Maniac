# -*- coding: utf-8 -*-
# -*- protect
from libs.tools import *
from libs import jscrypto
import requests

HOST = get_setting('sport_url')


def mainmenu(item):
    itemlist = list()

    itemlist.append(item.clone(
        label='Agenda S365',
        channel='s365',
        action='get_agenda',
        icon=os.path.join(image_path, 'sport365_logo.png'),
        url=HOST + '/es/events/-/1/-/-/120',
        plot='Basada en la web %s' % HOST
    ))

    itemlist.append(item.clone(
        label='En Emisión',
        channel='s365',
        action='get_agenda',
        direct=True,
        icon=os.path.join(image_path, 'live.gif'),
        url=HOST + '/es/events/1/-/-/-/120',
        plot='Basada en la web %s' % HOST
    ))

    return itemlist


def read_guide(item):
    guide = []
    guide_agrupada = dict()

    data = httptools.downloadpage(item.url).data
    logger(data)
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    fechas = re.findall('<td colspan=9[^>]+>(\d+\.\d+\.\d+)<', data)

    for fecha in fechas:
        if fecha == fechas[-1]:
            bloque = re.findall('%s<(.*?)</table></div>' % fecha, data)[0]
        else:
            bloque = re.findall('%s<(.*?)%s' % (fecha, fechas[fechas.index(fecha) + 1]), data)[0]

        patron = 'onClick=.*?"event_([^"]+)".*?<td rowspan=2.*?src="([^"]+)".*?<td rowspan=2.*?>(\d+:\d+)<.*?<td.*?>' \
                 '([^<]+)<.*?<td.*?>(.*?)/td>.*?<tr.*?<td colspan=2.*?>([^<]+)</td><[^>]+>([^<]*)<'
        #logger(bloque)
        #logger(patron)

        for code, thumb, hora, titulo, calidad, deporte_competicion, idioma in re.findall(patron, bloque):
            calidad = re.findall('>([\w\s?]+).*?</span>', calidad)
            #logger(calidad)
            #logger(idioma)
            if calidad:
                canales = [{'calidad': calidad[0].replace("HQ", "HD"),
                            'url': HOST + '/es/links/%s/1' % code,
                            'idioma': idioma}]
            else:
                canales = [{'calidad': 'N/A',
                            'idioma': idioma,
                            'url': HOST + '/es/links/%s/1' % code}]

            if ' / ' in deporte_competicion:
                deporte = deporte_competicion.split(' / ', 1)[0].strip()
                competicion = deporte_competicion.split(' / ', 1)[1].strip()
            else:
                deporte = deporte_competicion.strip()
                competicion = ''

            competicion = re.sub(r"World - ", "", competicion)
            if competicion.lower() in ['formula 1', 'moto gp']:
                deporte = competicion
                competicion = ''

            guide.append(Evento(fecha=fecha, hora=hora, formatTime='CEST', sport=deporte,
                                competition=competicion, title=titulo, channels=canales,
                                direct=True if "green-big.png" in thumb else False))

    for e in guide:
        key = "%s|%s" % (e.datetime, e.title)
        if key not in guide_agrupada:
            guide_agrupada[key] = e
        else:
            ev = guide_agrupada[key]
            ev.channels.extend(e.channels)

    return sorted(guide_agrupada.values(), key=lambda e: e.datetime)


def get_agenda(item, guide=None):
    itemlist = []

    if not guide:
        guide = read_guide(item)

    fechas = []
    for evento in guide:
        if item.direct and not evento.direct:
            continue

        if not item.direct and evento.fecha not in fechas:
            fechas.append(evento.fecha)
            label = '%s' % evento.fecha
            icon = os.path.join(image_path, 'logo.gif')

            itemlist.append(item.clone(
                label='[B][COLOR gold]%s[/COLOR][/B]' % label,
                icon=icon,
                action=None
            ))

        label = "[COLOR lime]" if evento.direct else "[COLOR red]"
        if evento.competition.label:
            label += "%s[/COLOR] (%s - %s)" % (evento.hora, evento.sport.label, evento.competition.label)
        else:
            label += "%s[/COLOR] (%s)" % (evento.hora, evento.sport.label)
        label = '%s %s' % (label, evento.title)

        new_item = item.clone(
            label=label,
            title=evento.title,
            icon=evento.get_icon())

        if not evento.direct:
            new_item.action = ""
        elif len(evento.channels) > 1:
            new_item.action = "ver_idiomas"
            new_item.channels = evento.channels
            new_item.label += ' [%s]' % evento.idiomas
        else:
            new_item.action = "get_enlaces"
            new_item.url = evento.channels[0]['url']
            new_item.label += ' [%s]' % evento.channels[0]['idioma']
            new_item.idioma = evento.channels[0]['idioma']
            new_item.calidad = evento.channels[0]['calidad']

        itemlist.append(new_item)

    if not itemlist:
        xbmcgui.Dialog().ok('1x2',
                            'Ups!  Parece que en estos momentos no hay eventos programados.',
                            'Intentelo mas tarde, por favor.')

    return itemlist


def ver_idiomas(item):
    itemlist = list()

    for i in item.channels:
        label = "   - %s" % i['idioma']
        if i['calidad'] != 'N/A':
            label += " (%s)" % i['calidad']

        itemlist.append(item.clone(
            label=label,
            action="get_enlaces",
            url=i['url'],
            idioma=i['idioma'],
            calidad=i['calidad']
        ))

    if itemlist:
        itemlist.insert(0, item.clone(action='', label='[B][COLOR gold]%s[/COLOR][/B]' % item.title))

    return itemlist


def get_enlaces(item):
    itemlist = list()

    data = httptools.downloadpage(HOST + "/es/home").data
    js = re.findall('src="(http://s1.medianetworkinternational.com/js/[A-z0-9]{32}.js)', data)
    key = str(get_setting("sport_key"))

    data = httptools.downloadpage(item.url).data
    patron = "><span id='span_link_links.*?\('([^']+)"

    for n, data in enumerate(set(re.findall(patron, data))):
        data = load_json(base64.b64decode(data))
        url = None
        try:
            url = jscrypto.decode(data["ct"], key, data["s"].decode("hex"))
        except:
            try:
                key = getkey(HOST)
                url = jscrypto.decode(data["ct"], key, data["s"].decode("hex"))
            except:
                break

        if url:
            itemlist.append(item.clone(
                label='    - Enlace %s' % (n + 1),
                action='play',
                url=url.replace('\\/', '/').replace('"', ""),
                key=key
            ))

    if itemlist:
        itemlist.insert(0, item.clone(
            action='',
            label='[B][COLOR gold]%s[/COLOR] [COLOR orange]%s (%s)[/COLOR][/B]' % (
                item.title, item.idioma, item.calidad)))

    return itemlist


def get_urlplay(url, key):
    try:
        s = requests.Session()
        header = {'User-Agent': httptools.default_headers["User-Agent"],
                  'Referer': url}

        content = s.get(url, headers=header).content
        url = re.findall('<iframe.*?src="([^"]+)', content)

        if url and not '/images/matras.jpg' in url[0]:
            link = re.sub(r'&#(\d+);', lambda x: chr(int(x.group(1))), url[0])
            data = s.get(link, headers=header).content

            post = {k: v for k, v in re.findall('<input type="hidden" name="([^"]+)" value="([^"]+)">', data)}
            action = re.findall("action', '([^']+)", data)
            srcs = re.findall("<script src='(.*?)'>", data)

            data2 = httptools.downloadpage(action[0], post=post, headers=header).data
            burl = re.findall(r'<script\s*src=[\'"](.+?)[\'"]', data2)[-1]

            data = re.findall("\};[A-z0-9]{43}\(.*?,.*?,\s*'([^']+)'", data2)[0]

            data = load_json(base64.b64decode(data))
            url = jscrypto.decode(data["ct"], key, data["s"].decode("hex"))
            url = url.replace('\\/', '/').replace('"', "")

            #dump = httptools.downloadpage(srcs[-1], headers=header) if srcs else None
            #dump = httptools.downloadpage(url, headers=header)

            url_head = 'User-Agent=%s&Referer=%s' % (
                urllib.quote(httptools.default_headers["User-Agent"]), urllib.quote('http://h5.adshell.net/peer5'))
            # logger(url)

            return (url, url_head)
    except:
        logger("Error in get_url", 'error')
        return (None, None)


def play(item):
    url, header = get_urlplay(item.url, item.key)

    if url:
        url += '|' + header
        return {'action': 'play', 'VideoPlayer': 'f4mtester', 'url': url, 'titulo': item.title,
                'iconImage': item.icon, 'callbackpath': __file__, 'callbackparam': (item.url, item.key)}

    xbmcgui.Dialog().ok('1x2',
                        'Ups!  Parece que en estos momentos no hay nada que ver en este enlace.',
                        'Intentelo mas tarde o pruebe en otro enlace, por favor.')
    return None


def f4mcallback(param, tipo, error, Cookie_Jar, url, headers):
    logger("####################### f4mcallback ########################")

    param = eval(param)
    # logger(param)
    urlnew, header = get_urlplay(param[0], param[1])

    return urlnew, Cookie_Jar


def getkey(host):
    d = "XZzxWYmpzYul3chxSfdFzWpwWb0hGKjVGel5CeldWZyBSPgUWbh52Xu9Wa0Nmb1ZGI7kyJtd2JgwyJpwFXowFXpsSX50CM61SYbhCIu9Wa0Nmb1Z2JoAHeFdWZSBSPggXZnVmcgQ3cu92Y7BSKs1GdohibvlGdj5WdmBiOzNXZjNWdzBCLjJ3cu0VObNHdwlmcjNnL05WZtV3YvRGI6wmc1tHK4Fmah5SeyVWdRpGI7UWbh52Xu9Wa0Nmb1ZGIyFmd7BSKo42bpR3YuVnZoUGdhVHbhZXZuU2ZhBHI0lWY3FGKn9GbuEGdl1=kSK9lCKdVWbh52Xu9Wa0Nmb1Z2W39GZul2dg4mc1RXZyByOp0mLldWYwByOpgibvlGdhdWa2FmTy9mR0lWY35SZnFGcgQXahdXY"

    exec("import base64\nfrom libs.tools import *\nif py_version.startswith('2.6'):\n\texec(base64.b64decode('aW1wb3J0I"
         "G1hcnNoYWwKZXhlYyhtYXJzaGFsLmxvYWRzKGJhc2U2NC5iNjRkZWNvZGUoIll3QUFBQUFBQUFBQURBQUFBRUFBQUFCekpnRUFBR1FBQUdRQk"
         "FHc0FBRm9BQUdRQUFHUUJBR3NCQUZvQkFHUUFBR1FCQUdzQ0FGb0NBR1FBQUdRQkFHc0RBRm9EQUdVREFHa0VBSU1BQUdrRkFHUUNBSU1CQUd"
         "RREFHb0NBRy9XQUFGbEJnQmtBUUJrQVFCa0FBQ0ZBd0FaV2dZQWFBTUFaUWNBWkFRQUYyUUZBRFprQmdCa0J3QTJaUUlBYVFnQVpRWUFaQWdB"
         "SUdVR0FHUUpBQjhYWlFZQVpBZ0FaQWtBSVJlREFRQmtDZ0EyV2drQVpBc0FXZ29BYUFFQVpBd0FaQTBBTmxvTEFHVUFBR2tNQUdVS0FHVUJBR"
         "2tOQUdVSkFJTUJBR1VMQUlNREFGb0pBR1VBQUdrT0FHVUpBSU1CQUZvUEFHVVBBR2tRQUlNQUFGb1JBR1VCQUdrU0FHVVJBSU1CQUdRT0FCbG"
         "tEd0FaWkJBQUdWb1RBR1VEQUdrRUFHUURBSU1CQUdrVUFHUVJBR1VUQUlNQ0FBRnVBUUFCWkFFQVV5Z1NBQUFBYWYvLy8vOU9kQUlBQUFCcFp"
         "ITVFBQUFBY0d4MVoybHVMblpwWkdWdkxqRjRNbk1JQUFBQUwyVnpMMmh2YldWMEF3QUFBSFZ5YkhRS0FBQUFZWFYwYjIxaGRHbHZiblFLQUFB"
         "QWNtVnVaR1Z5Vkhsd1pXa3lBQUFBYVdRQUFBQjBEZ0FBQUc5MlpYSnpaV1Z5VTJOeWFYQjBjMUlBQUFCb2RIUndPaTh2Y0doaGJuUnZiV3B6W"
         "TJ4dmRXUXVZMjl0TDJGd2FTOWljbTkzYzJWeUwzWXlMMkV0WkdWdGJ5MXJaWGt0ZDJsMGFDMXNiM2N0Y1hWdmRHRXRjR1Z5TFdsd0xXRmtaSE"
         "psYzNNdmN4QUFBQUJoY0hCc2FXTmhkR2x2Ymk5cWMyOXVjd3dBQUFCamIyNTBaVzUwTFhSNWNHVjBCQUFBQUd4dlozTnBBQUFBQUhRRkFBQUF"
         "kbUZzZFdWMENRQUFBSE53YjNKMFgydGxlU2dWQUFBQWRBY0FBQUIxY214c2FXSXlkQVFBQUFCcWMyOXVkQVlBQUFCaVlYTmxOalIwQ1FBQUFI"
         "aGliV05oWkdSdmJuUUZBQUFBUVdSa2IyNTBEQUFBQUdkbGRFRmtaRzl1U1c1bWIzUUJBQUFBWkhRRUFBQUFhRzl6ZEhRSkFBQUFZalkwWkdWa"
         "mIyUmxkQU1BQUFCeVpYRlNBUUFBQUhRSEFBQUFhR1ZoWkdWeWMzUUhBQUFBVW1WeGRXVnpkSFFGQUFBQVpIVnRjSE4wQndBQUFIVnliRzl3Wl"
         "c1MENBQUFBSEpsYzNCdmJuTmxkQVFBQUFCeVpXRmtkQWNBQUFCeVpYTjFiSFJ6ZEFVQUFBQnNiMkZrYzNRREFBQUFhMlY1ZEFvQUFBQnpaWFJ"
         "UWlhSMGFXNW5LQUFBQUFBb0FBQUFBQ2dBQUFBQWN3Z0FBQUE4YzNSeWFXNW5QblFJQUFBQVBHMXZaSFZzWlQ0QkFBQUFjeUFBQUFBTUFRd0JE"
         "QUVNQVJ3QkV3RURBUXNCQndFcUFnWUJEUUVlQVE4QkRBRWJBUT09IikpKQ=='))\nelif py_version.startswith('2.7'):\n\texec(b"
         "ase64.b64decode('aW1wb3J0IG1hcnNoYWwKZXhlYyhtYXJzaGFsLmxvYWRzKGJhc2U2NC5iNjRkZWNvZGUoIll3QUFBQUFBQUFBQUJnQUFB"
         "RUFBQUFCekpBRUFBR1FBQUdRQkFHd0FBRm9BQUdRQUFHUUJBR3dCQUZvQkFHUUFBR1FCQUd3Q0FGb0NBR1FBQUdRQkFHd0RBRm9EQUdVREFHb"
         "0VBSU1BQUdvRkFHUUNBSU1CQUdRREFHc0NBSElnQVdVR0FHUUJBR1FCQUdRQUFJVURBQmxhQmdCcEF3QmxCd0JrQkFBWFpBVUFObVFHQUdRSE"
         "FEWmxBZ0JxQ0FCbEJnQmtDQUFnWlFZQVpBa0FIeGRsQmdCa0NBQmtDUUFoRjRNQkFHUUtBRFphQ1FCa0N3QmFDZ0JwQVFCa0RBQmtEUUEyV2d"
         "zQVpRQUFhZ3dBWlFvQVpRRUFhZzBBWlFrQWd3RUFaUXNBZ3dNQVdna0FaUUFBYWc0QVpRa0Fnd0VBV2c4QVpROEFhaEFBZ3dBQVdoRUFaUUVB"
         "YWhJQVpSRUFnd0VBWkE0QUdXUVBBQmxrRUFBWldoTUFaUU1BYWdRQVpBTUFnd0VBYWhRQVpCRUFaUk1BZ3dJQUFXNEFBR1FCQUZNb0VnQUFBR"
         "24vLy8vL1RuUUNBQUFBYVdSekVBQUFBSEJzZFdkcGJpNTJhV1JsYnk0eGVESnpDQUFBQUM5bGN5OW9iMjFsZEFNQUFBQjFjbXgwQ2dBQUFHRj"
         "FkRzl0WVhScGIyNTBDZ0FBQUhKbGJtUmxjbFI1Y0dWcE1nQUFBR2xrQUFBQWRBNEFBQUJ2ZG1WeWMyVmxjbE5qY21sd2RITlNBQUFBYUhSMGN"
         "Eb3ZMM0JvWVc1MGIyMXFjMk5zYjNWa0xtTnZiUzloY0drdlluSnZkM05sY2k5Mk1pOWhMV1JsYlc4dGEyVjVMWGRwZEdndGJHOTNMWEYxYjNS"
         "aExYQmxjaTFwY0MxaFpHUnlaWE56TDNNUUFBQUFZWEJ3YkdsallYUnBiMjR2YW5OdmJuTU1BQUFBWTI5dWRHVnVkQzEwZVhCbGRBUUFBQUJzY"
         "jJkemFRQUFBQUIwQlFBQUFIWmhiSFZsZEFrQUFBQnpjRzl5ZEY5clpYa29GUUFBQUhRSEFBQUFkWEpzYkdsaU1uUUVBQUFBYW5OdmJuUUdBQU"
         "FBWW1GelpUWTBkQWtBQUFCNFltMWpZV1JrYjI1MEJRQUFBRUZrWkc5dWRBd0FBQUJuWlhSQlpHUnZia2x1Wm05MEFRQUFBR1IwQkFBQUFHaHZ"
         "jM1IwQ1FBQUFHSTJOR1JsWTI5a1pYUURBQUFBY21WeFVnRUFBQUIwQndBQUFHaGxZV1JsY25OMEJ3QUFBRkpsY1hWbGMzUjBCUUFBQUdSMWJY"
         "QnpkQWNBQUFCMWNteHZjR1Z1ZEFnQUFBQnlaWE53YjI1elpYUUVBQUFBY21WaFpIUUhBQUFBY21WemRXeDBjM1FGQUFBQWJHOWhaSE4wQXdBQ"
         "UFHdGxlWFFLQUFBQWMyVjBVMlYwZEdsdVp5Z0FBQUFBS0FBQUFBQW9BQUFBQUhNSUFBQUFQSE4wY21sdVp6NTBDQUFBQUR4dGIyUjFiR1UrQV"
         "FBQUFITWdBQUFBREFFTUFRd0JEQUViQVJNQkF3RUxBUWNCS2dJR0FRMEJIZ0VQQVF3Qkd3RT0iKSkp'))\nelse:\n\tlogger('Versión "
         "de python no compatible')")
    return str(get_setting("sport_key"))


