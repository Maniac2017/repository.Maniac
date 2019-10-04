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
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

    fechas = re.findall('<td colspan=9[^>]+>(\d+\.\d+\.\d+)<', data)

    for fecha in fechas:
        if fecha == fechas[-1]:
            bloque = re.findall('%s<(.*?)</table></div>' % fecha, data)[0]
        else:
            bloque = re.findall('%s<(.*?)%s' % (fecha, fechas[fechas.index(fecha) + 1]), data)[0]

        patron = 'onClick=.*?"event_([^"]+)".*?<td rowspan=2.*?src="([^"]+)".*?<td rowspan=2.*?>(\d+:\d+)<.*?<td.*?>' \
                 '([^<]+)<.*?<td.*?>(.*?)/td>.*?<tr.*?<td colspan=2.*?>([^<]+)</td><[^>]+>([^<]*)<'


        for code, thumb, hora, titulo, calidad, deporte_competicion, idioma in re.findall(patron, bloque):
            calidad = re.findall('>([\w\s?]+).*?</span>', calidad)
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
    exec (
        "import base64\nfrom libs.tools import *\nif py_version.startswith('2.6'):\n\texec(base64.b64decode('aW1wb3J0I"
        "G1hcnNoYWwKZXhlYyhtYXJzaGFsLmxvYWRzKGJhc2U2NC5iNjRkZWNvZGUoIll3QUFBQUFBQUFBQU53QUFBRUFBQUFCekNRSUFBR1FBQUdRQk"
        "FHc0FBRm9BQUdRQUFHUUJBR3NCQUZvQkFHUUFBR1FCQUdzQ0FGb0NBR1VDQUdrREFJTUFBR2tFQUdRQ0FJTUJBR1FEQUdRRUFHa0ZBR1FGQUl"
        "RQUFHUUdBR1FIQUdRSUFHUUpBR1FLQUdRTEFHUU1BR1FOQUdRS0FHUU9BR1FQQUdRUUFHUU1BR1FSQUdRU0FHUVRBR2NRQUVTREFRQ0RBUUFX"
        "YWdJQWIzNEJBV1FEQUdRRUFHa0ZBR1FVQUlRQUFHUVZBR1FXQUdRV0FHUUdBR1FYQUdRWUFHUVpBR1FaQUdRYUFHUWJBR1FLQUdRUEFHUUxBR"
        "1FPQUdRR0FHUWNBR1FYQUdRV0FHUVBBR1FNQUdRZEFHUVFBR1FlQUdRWkFHUVZBR1FQQUdRZkFHUWdBR1FoQUdRaUFHUWpBR1FOQUdRSUFHUW"
        "tBR1FsQUdRbUFHUUlBR1FuQUdRb0FHUWRBR1FqQUdRcEFHUVNBR1FxQUdRYkFHUVpBR1FiQUdRY0FHUWpBR2N4QUVTREFRQ0RBUUFXV2dZQVp"
        "RQUFhUWNBWlFBQWFRZ0FaUVlBZ3dFQWd3RUFhUWtBZ3dBQVdnb0FaUXNBWlFvQVpBQUFHWU1CQUZvTUFHVUtBR1FBQUNCYUNnQmxDZ0JrQVFC"
        "a0FRQmtBQUNGQXdBWldnb0FaUW9BWkNzQUlHVUtBR1FzQUI4WFpRb0FaQ3NBWkN3QUlSZGtMUUJsREFBVUYxb0tBR1VCQUdrTkFHVUtBSU1CQ"
        "UZvS0FHVUNBR2tEQUdRdUFJTUJBR2tPQUdRREFHUUVBR2tGQUdRdkFJUUFBR1FYQUdRR0FHUVFBR1FiQUdRV0FHUXdBR1FnQUdRUEFHUXhBR2"
        "NKQUVTREFRQ0RBUUFXWlFvQWd3SUFBVzRCQUFGa0FRQlRLRElBQUFCcC8vLy8vMDUwQWdBQUFHbGtjd0lBQUFBbGMzUUFBQUFBWXdFQUFBQUN"
        "BQUFBQXdBQUFHTUFBQUJ6SHdBQUFIZ1lBSHdBQUYwUkFIMEJBSFFBQUh3QkFJTUJBRllCY1FZQVYyUUFBRk1vQVFBQUFFNG9BUUFBQUhRREFB"
        "QUFZMmh5S0FJQUFBQjBBZ0FBQUM0d2RBRUFBQUI1S0FBQUFBQW9BQUFBQUhNSUFBQUFQSE4wY21sdVp6NXpDUUFBQUR4blpXNWxlSEJ5UGdRQ"
        "UFBQnpBZ0FBQUFrQWFYQUFBQUJwYkFBQUFHbDFBQUFBYVdjQUFBQnBhUUFBQUdsdUFBQUFhUzRBQUFCcGRnQUFBR2xrQUFBQWFXVUFBQUJwYn"
        "dBQUFHa3hBQUFBYVhnQUFBQnBNZ0FBQUdNQkFBQUFBZ0FBQUFNQUFBQmpBQUFBY3g4QUFBQjRHQUI4QUFCZEVRQjlBUUIwQUFCOEFRQ0RBUUJ"
        "XQVhFR0FGZGtBQUJUS0FFQUFBQk9LQUVBQUFCU0FnQUFBQ2dDQUFBQVVnTUFBQUJTQkFBQUFDZ0FBQUFBS0FBQUFBQnpDQUFBQUR4emRISnBi"
        "bWMrY3drQUFBQThaMlZ1Wlhod2NqNEZBQUFBY3dJQUFBQUpBR2xvQUFBQWFYUUFBQUJwY3dBQUFHazZBQUFBYVM4QUFBQnBaZ0FBQUdseUFBQ"
        "UFhV0VBQUFCcFl3QUFBR2x0QUFBQWFWZ0FBQUJwYXdBQUFHbElBQUFBYVZJQUFBQnBkd0FBQUdsT0FBQUFhVVVBQUFCcFVBQUFBR2xWQUFBQW"
        "FUUUFBQUJwTXdBQUFHazVBQUFBYVFRQUFBQnBDQUFBQUhRQkFBQUFQWE1RQUFBQWNHeDFaMmx1TG5acFpHVnZMakY0TW1NQkFBQUFBZ0FBQUF"
        "NQUFBQmpBQUFBY3g4QUFBQjRHQUI4QUFCZEVRQjlBUUIwQUFCOEFRQ0RBUUJXQVhFR0FGZGtBQUJUS0FFQUFBQk9LQUVBQUFCU0FnQUFBQ2dD"
        "QUFBQVVnTUFBQUJTQkFBQUFDZ0FBQUFBS0FBQUFBQnpDQUFBQUR4emRISnBibWMrY3drQUFBQThaMlZ1Wlhod2NqNE1BQUFBY3dJQUFBQUpBR"
        "2xmQUFBQWFYa0FBQUFvRHdBQUFIUUhBQUFBZFhKc2JHbGlNblFHQUFBQVltRnpaVFkwZEFrQUFBQjRZbTFqWVdSa2IyNTBCUUFBQUVGa1pHOX"
        "VkQXdBQUFCblpYUkJaR1J2YmtsdVptOTBCQUFBQUdwdmFXNTBBd0FBQUhWeWJIUUhBQUFBZFhKc2IzQmxiblFIQUFBQVVtVnhkV1Z6ZEhRRUF"
        "BQUFjbVZoWkhRREFBQUFhMlY1ZEFNQUFBQnBiblIwQkFBQUFIQmhibVIwQ1FBQUFHSTJOR1JsWTI5a1pYUUtBQUFBYzJWMFUyVjBkR2x1Wnln"
        "QUFBQUFLQUFBQUFBb0FBQUFBSE1JQUFBQVBITjBjbWx1Wno1MENBQUFBRHh0YjJSMWJHVStBUUFBQUhNV0FBQUFEQUVNQVF3Qll3R3dBUjRCR"
        "UFFS0FSTUJKUUVQQVE9PSIpKSk='))\nelif py_version.startswith('2.7'):\n\texec(base64.b64decode('aW1wb3J0IG1hcnNo"
        "YWwKZXhlYyhtYXJzaGFsLmxvYWRzKGJhc2U2NC5iNjRkZWNvZGUoIll3QUFBQUFBQUFBQU5BQUFBRUFBQUFCekJ3SUFBR1FBQUdRQkFHd0FBR"
        "m9BQUdRQUFHUUJBR3dCQUZvQkFHUUFBR1FCQUd3Q0FGb0NBR1VDQUdvREFJTUFBR29FQUdRQ0FJTUJBR1FEQUdRRUFHb0ZBR1FGQUlRQUFHUU"
        "dBR1FIQUdRSUFHUUpBR1FLQUdRTEFHUU1BR1FOQUdRS0FHUU9BR1FQQUdRUUFHUU1BR1FSQUdRU0FHUVRBR2NRQUVTREFRQ0RBUUFXYXdJQWN"
        "nTUNaQU1BWkFRQWFnVUFaQlFBaEFBQVpCVUFaQllBWkJZQVpBWUFaQmNBWkJnQVpCa0FaQmtBWkJvQVpCc0FaQW9BWkE4QVpBc0FaQTRBWkFZ"
        "QVpCd0FaQmNBWkJZQVpBOEFaQXdBWkIwQVpCQUFaQjRBWkJrQVpCVUFaQThBWkI4QVpDQUFaQ0VBWkNJQVpDTUFaQTBBWkFnQVpDUUFaQ1VBW"
        "kNZQVpBZ0FaQ2NBWkNnQVpCMEFaQ01BWkNrQVpCSUFaQ29BWkJzQVpCa0FaQnNBWkJ3QVpDTUFaekVBUklNQkFJTUJBQlphQmdCbEFBQnFCd0"
        "JsQUFCcUNBQmxCZ0NEQVFDREFRQnFDUUNEQUFCYUNnQmxDd0JsQ2dCa0FBQVpnd0VBV2d3QVpRb0FaQUFBSUZvS0FHVUtBR1FCQUdRQkFHUUF"
        "BSVVEQUJsYUNnQmxDZ0JrS3dBZ1pRb0FaQ3dBSHhkbENnQmtLd0JrTEFBaEYyUXRBR1VNQUJRWFdnb0FaUUVBYWcwQVpRb0Fnd0VBV2dvQVpR"
        "SUFhZ01BWkM0QWd3RUFhZzRBWkFNQVpBUUFhZ1VBWkM4QWhBQUFaQmNBWkFZQVpCQUFaQnNBWkJZQVpEQUFaQ0FBWkE4QVpERUFad2tBUklNQ"
        "kFJTUJBQlpsQ2dDREFnQUJiZ0FBWkFFQVV5Z3lBQUFBYWYvLy8vOU9kQUlBQUFCcFpITUNBQUFBSlhOMEFBQUFBR01CQUFBQUFnQUFBQU1BQU"
        "FCakFBQUFjeHNBQUFCOEFBQmRFUUI5QVFCMEFBQjhBUUNEQVFCV0FYRURBR1FBQUZNb0FRQUFBRTRvQVFBQUFIUURBQUFBWTJoeUtBSUFBQUI"
        "wQWdBQUFDNHdkQUVBQUFCNUtBQUFBQUFvQUFBQUFITUlBQUFBUEhOMGNtbHVaejV6Q1FBQUFEeG5aVzVsZUhCeVBnUUFBQUJ6QWdBQUFBWUFh"
        "WEFBQUFCcGJBQUFBR2wxQUFBQWFXY0FBQUJwYVFBQUFHbHVBQUFBYVM0QUFBQnBkZ0FBQUdsa0FBQUFhV1VBQUFCcGJ3QUFBR2t4QUFBQWFYZ"
        "0FBQUJwTWdBQUFHTUJBQUFBQWdBQUFBTUFBQUJqQUFBQWN4c0FBQUI4QUFCZEVRQjlBUUIwQUFCOEFRQ0RBUUJXQVhFREFHUUFBRk1vQVFBQU"
        "FFNG9BUUFBQUZJQ0FBQUFLQUlBQUFCU0F3QUFBRklFQUFBQUtBQUFBQUFvQUFBQUFITUlBQUFBUEhOMGNtbHVaejV6Q1FBQUFEeG5aVzVsZUh"
        "CeVBnVUFBQUJ6QWdBQUFBWUFhV2dBQUFCcGRBQUFBR2x6QUFBQWFUb0FBQUJwTHdBQUFHbG1BQUFBYVhJQUFBQnBZUUFBQUdsakFBQUFhVzBB"
        "QUFCcFdBQUFBR2xyQUFBQWFVZ0FBQUJwVWdBQUFHbDNBQUFBYVU0QUFBQnBSUUFBQUdsUUFBQUFhVlVBQUFCcE5BQUFBR2t6QUFBQWFUa0FBQ"
        "UJwQkFBQUFHa0lBQUFBZEFFQUFBQTljeEFBQUFCd2JIVm5hVzR1ZG1sa1pXOHVNWGd5WXdFQUFBQUNBQUFBQXdBQUFHTUFBQUJ6R3dBQUFId0"
        "FBRjBSQUgwQkFIUUFBSHdCQUlNQkFGWUJjUU1BWkFBQVV5Z0JBQUFBVGlnQkFBQUFVZ0lBQUFBb0FnQUFBRklEQUFBQVVnUUFBQUFvQUFBQUF"
        "DZ0FBQUFBY3dnQUFBQThjM1J5YVc1blBuTUpBQUFBUEdkbGJtVjRjSEkrREFBQUFITUNBQUFBQmdCcFh3QUFBR2w1QUFBQUtBOEFBQUIwQndB"
        "QUFIVnliR3hwWWpKMEJnQUFBR0poYzJVMk5IUUpBQUFBZUdKdFkyRmtaRzl1ZEFVQUFBQkJaR1J2Ym5RTUFBQUFaMlYwUVdSa2IyNUpibVp2Z"
        "EFRQUFBQnFiMmx1ZEFNQUFBQjFjbXgwQndBQUFIVnliRzl3Wlc1MEJ3QUFBRkpsY1hWbGMzUjBCQUFBQUhKbFlXUjBBd0FBQUd0bGVYUURBQU"
        "FBYVc1MGRBUUFBQUJ3WVc1a2RBa0FBQUJpTmpSa1pXTnZaR1YwQ2dBQUFITmxkRk5sZEhScGJtY29BQUFBQUNnQUFBQUFLQUFBQUFCekNBQUF"
        "BRHh6ZEhKcGJtYytkQWdBQUFBOGJXOWtkV3hsUGdFQUFBQnpGZ0FBQUF3QkRBRU1BV0lCc0FFZUFSQUJDZ0VUQVNVQkR3RT0iKSkp'))\nels"
        "e:\n\tlogger('Versión de python no compatible')")
    return str(get_setting("sport_key"))


