# -*- coding: utf-8 -*-

from libs.tools import *
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

            # FIX horario invierno
            fecha_hora = datetime.datetime.strptime("%s %s" % (fecha, hora), '%d.%m.%Y %H:%M') - datetime.timedelta(hours=1)

            guide.append(Evento(fecha=fecha_hora.date().strftime('%d/%m/%Y'), hora=fecha_hora.time().strftime('%H:%M'),
                                formatTime='CEST', sport=deporte,
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

    data = httptools.downloadpage(item.url).data
    patron = "><span id='span_link_links.*?\('([^']+)"

    for n, data in enumerate(set(re.findall(patron, data))):
        url = decrypt(data)
        if url:
            itemlist.append(item.clone(
                label='    - Enlace %s' % (n + 1),
                action='play',
                url=url
            ))

    if itemlist:
        itemlist.insert(0, item.clone(
            action='',
            label='[B][COLOR gold]%s[/COLOR] [COLOR orange]%s (%s)[/COLOR][/B]' % (
                item.title, item.idioma, item.calidad)))

    return itemlist


def get_urlplay(url):
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
            data2 = httptools.downloadpage(action[0], post=post, headers=header).data
            data = re.findall("function\(\)\s*{\s*[a-z0-9]{43}\(.*?,.*?,\s*'([^']+)'", data2)[0]

            url = decrypt(data)
            if not url: raise ()

            url_head = 'User-Agent=%s&Referer=%s' % (
                urllib.quote(httptools.default_headers["User-Agent"]), urllib.quote('http://h5.adshell.net/peer5'))

            return (url, url_head)
    except:
        logger("Error in get_url", 'error')
        return (None, None)


def decrypt(text):
    plaintext = ''
    exec("import base64\nfrom libs.tools import *\nif py_version.startswith('2.6'):\n\texec(base64.b64decode('aW1wb3J0I"
         "G1hcnNoYWwKZXhlYyhtYXJzaGFsLmxvYWRzKGJhc2U2NC5iNjRkZWNvZGUoIll3QUFBQUFBQUFBQUpRQUFBRUFBQUFCelF3TUFBR1FBQUdRQk"
         "FHc0FBRm9BQUdRQUFHUUJBR3NCQUZvQkFHUUFBR1FCQUdzQ0FGb0NBR1FBQUdRQkFHc0RBRm9EQUdRQUFHUUNBR3NFQUd3RkFGb0ZBQUZrQUF"
         "Ca0F3QnJCZ0JzQndCYUJ3QUJaQVFBaEFBQVdnZ0FaQVVBaEFBQVdna0FaUW9BYVFzQWFRd0FaUU1BYVEwQVpRSUFhUTRBWkFZQVpBY0FhUThB"
         "WkFnQWhBQUFaQWtBWkFvQVpBc0FaQXdBWkEwQVpBNEFaQThBWkJBQVpBMEFaQkVBWkJJQVpCTUFaQThBWkJRQVpCVUFaQllBWnhBQVJJTUJBS"
         "U1CQUJhREFRQnBFQUJrRndDREFRQ0RBUUNEQVFCYUVRQmxDZ0JwQ3dCcEVnQmxDZ0JwQ3dCcER3QmxFUUJrQmdCa0J3QnBEd0JrR0FDRUFBQm"
         "tDUUJrQ2dCa0N3QmtEQUJrRFFCa0RnQmtEd0JrRUFCa0RRQmtFUUJrRWdCa0V3QmtEd0JrQ2dCa0RRQmtFQUJrRWdCa0dRQmtFQUJrR2dCa0V"
         "nQmtHd0JrSEFCa0RRQmtIUUJuR1FCRWd3RUFnd0VBRm9NQ0FJTUJBRzhSQUFGbEJ3QmtIZ0JrSHdDREFnQUJidFVCQVdVQ0FHa09BSU1BQUdr"
         "UUFHUWdBSU1CQUdRR0FHUUhBR2tQQUdRaEFJUUFBR1FKQUdRS0FHUUxBR1FNQUdRTkFHUU9BR1FQQUdRUUFHUU5BR1FSQUdRU0FHUVRBR1FQQ"
         "UdRVUFHUVZBR1FXQUdjUUFFU0RBUUNEQVFBV1pBWUFaQWNBYVE4QVpDRUFoQUFBWkFrQVpBb0FaQXNBWkF3QVpBMEFaQTRBWkE4QVpCQUFaQT"
         "BBWkJFQVpCSUFaQk1BWkE4QVpDSUFaQ01BWkNRQVpDVUFaQklBWkNZQVpCa0FaQklBWkJzQVp4WUFSSU1CQUlNQkFCWm5BZ0JxQmdCdkJRRUJ"
         "lWkVBWlFrQVpSTUFaQVlBWkFjQWFROEFaQ2NBaEFBQVpDWUFaQWtBWkJNQVpCc0FaQmtBWkNnQVpDa0FaQklBWkNvQVp3a0FSSU1CQUlNQkFC"
         "YURBUUNEQVFCY0FnQmFGQUJhRlFCbEJRQnBGZ0JsRlFCbEZBQ0RBZ0JwRndCbEdBQnBDUUJrS3dDREFRQ0RBUUJhR1FCbEdnQnBHd0JrTEFCb"
         "EdRQ0RBZ0JrTFFBWmFRa0FaQ3NBZ3dFQVdoa0FWM0UvQXdFQkFYbFdBR1VJQUlNQUFGd0NBRm9VQUZvVkFHVUZBR2tXQUdVVkFHVVVBSU1DQU"
         "drWEFHVVlBR2tKQUdRckFJTUJBSU1CQUZvWkFHVWFBR2tiQUdRc0FHVVpBSU1DQUdRdEFCbHBDUUJrS3dDREFRQmFHUUJYY1M0REFRRUJaQWN"
         "BV2hrQWNTNERXSEUvQTFodURnQUJaUWNBWkM0QVpCOEFnd0lBQVdRQkFGTW9Md0FBQUduLy8vLy9UaWdCQUFBQWRBTUFBQUJoWlhNb0FRQUFB"
         "SFFHQUFBQWJHOW5aMlZ5WXdBQUFBQUNBQUFBTkFBQUFFTUFBQUJ6YWdFQUFHUUJBR1FDQUdrQUFHUURBSVFBQUdRRUFHUUZBR1FGQUdRR0FHU"
         "UhBR1FJQUdRSkFHUUpBR1FLQUdRTEFHUU1BR1FOQUdRT0FHUVBBR1FHQUdRUUFHUUhBR1FGQUdRTkFHUVJBR1FTQUdRVEFHUVVBR1FKQUdRRU"
         "FHUU5BR1FWQUdRV0FHUVhBR1FZQUdRWkFHUWFBR1FiQUdRY0FHUWRBR1FlQUdRYkFHUWZBR1FnQUdRU0FHUVpBR1FoQUdRaUFHUWpBR1FMQUd"
         "RSkFHUUxBR1FRQUdRWkFHY3hBRVNEQVFDREFRQVdmUUFBZEFFQWFRSUFkQUVBYVFNQWZBQUFnd0VBZ3dFQWFRUUFnd0FBZlFFQWRBVUFhUVlB"
         "WkFFQVpBSUFhUUFBWkNRQWhBQUFaQVlBWkNVQVpCc0FaQ1lBWkF3QVpBNEFaQkVBWkJvQVpBd0FaQThBWkEwQVpCTUFaQkVBWkNjQVpDSUFaQ"
         "2dBWnhBQVJJTUJBSU1CQUJhREFRQnBCd0JrQVFCa0FnQnBBQUJrSkFDRUFBQmtCd0JrQmdCa0V3QmtDd0JrQlFCa0tRQmtGZ0JrRFFCa0tnQm"
         "5DUUJFZ3dFQWd3RUFGbndCQUlNQ0FBRjBDQUI4QVFDREFRQlRLQ3NBQUFCT2N3SUFBQUFsYzNRQUFBQUFZd0VBQUFBQ0FBQUFBd0FBQUhNQUF"
         "BQnpId0FBQUhnWUFId0FBRjBSQUgwQkFIUUFBSHdCQUlNQkFGWUJjUVlBVjJRQUFGTW9BUUFBQUU0b0FRQUFBSFFEQUFBQVkyaHlLQUlBQUFC"
         "MEFnQUFBQzR3ZEFFQUFBQjVLQUFBQUFBb0FBQUFBSE1JQUFBQVBITjBjbWx1Wno1ekNRQUFBRHhuWlc1bGVIQnlQZ2NBQUFCekFnQUFBQWtBY"
         "VdnQUFBQnBkQUFBQUdsd0FBQUFhWE1BQUFCcE9nQUFBR2t2QUFBQWFXWUFBQUJwY2dBQUFHbHBBQUFBYVdVQUFBQnBiZ0FBQUdsa0FBQUFhV0"
         "VBQUFCcExnQUFBR2xqQUFBQWFXOEFBQUJwYlFBQUFHbFlBQUFBYVdzQUFBQnBTQUFBQUdsU0FBQUFhWGNBQUFCcGRnQUFBR2wxQUFBQWFVNEF"
         "BQUJwUlFBQUFHbFFBQUFBYVZVQUFBQnBOQUFBQUdrekFBQUFhWGdBQUFCcE9RQUFBR01CQUFBQUFnQUFBQU1BQUFCekFBQUFjeDhBQUFCNEdB"
         "QjhBQUJkRVFCOUFRQjBBQUI4QVFDREFRQldBWEVHQUZka0FBQlRLQUVBQUFCT0tBRUFBQUJTQXdBQUFDZ0NBQUFBVWdRQUFBQlNCUUFBQUNnQ"
         "UFBQUFLQUFBQUFCekNBQUFBRHh6ZEhKcGJtYytjd2tBQUFBOFoyVnVaWGh3Y2o0SkFBQUFjd0lBQUFBSkFHbHNBQUFBYVdjQUFBQnBNUUFBQU"
         "dreUFBQUFhVjhBQUFCcGVRQUFBQ2dKQUFBQWRBUUFBQUJxYjJsdWRBY0FBQUIxY214c2FXSXlkQWNBQUFCMWNteHZjR1Z1ZEFjQUFBQlNaWEY"
         "xWlhOMGRBUUFBQUJ5WldGa2RBa0FBQUI0WW0xallXUmtiMjUwQlFBQUFFRmtaRzl1ZEFvQUFBQnpaWFJUWlhSMGFXNW5kQVlBQUFCa1pXTnZa"
         "R1VvQWdBQUFIUURBQUFBZFhKc2RBWUFBQUJwZGw5clpYa29BQUFBQUNnQUFBQUFjd2dBQUFBOGMzUnlhVzVuUG5RR0FBQUFaMlYwYTJWNUJnQ"
         "UFBSE1JQUFBQUFBR3dBUjRCa2dGakFRQUFBQUlBQUFBSEFBQUFRd0FBQUhOdUFBQUFkQUFBZkFBQVpBRUFHWU1CQUgwQkFId0FBR1FCQUNCOU"
         "FBQjhBQUJrQUFCa0FBQmtBUUNGQXdBWmZRQUFmQUFBWkFJQUlId0FBR1FEQUI4WGZBQUFaQUlBWkFNQUlSZGtCQUI4QVFBVUYzMEFBSFFCQUd"
         "rQ0FId0FBSU1CQUgwQUFId0FBR2tEQUdRRkFJTUJBRk1vQmdBQUFFNXAvLy8vLzJrRUFBQUFhUWdBQUFCMEFRQUFBRDEwQVFBQUFId29CQUFB"
         "QUhRREFBQUFhVzUwZEFZQUFBQmlZWE5sTmpSMENRQUFBR0kyTkdSbFkyOWtaWFFGQUFBQWMzQnNhWFFvQWdBQUFGSVFBQUFBZEFRQUFBQndZV"
         "zVrS0FBQUFBQW9BQUFBQUhNSUFBQUFQSE4wY21sdVp6NVNEZ0FBQUFzQUFBQnpEQUFBQUFBQkVBRUtBUk1CSlFFUEFYTUNBQUFBSlhOU0FnQU"
         "FBR01CQUFBQUFnQUFBQU1BQUFCakFBQUFjeDhBQUFCNEdBQjhBQUJkRVFCOUFRQjBBQUI4QVFDREFRQldBWEVHQUZka0FBQlRLQUVBQUFCT0t"
         "BRUFBQUJTQXdBQUFDZ0NBQUFBVWdRQUFBQlNCUUFBQUNnQUFBQUFLQUFBQUFCekNBQUFBRHh6ZEhKcGJtYytjd2tBQUFBOFoyVnVaWGh3Y2o0"
         "U0FBQUFjd0lBQUFBSkFHbHdBQUFBYVd3QUFBQnBkUUFBQUdsbkFBQUFhV2tBQUFCcGJnQUFBR2t1QUFBQWFYWUFBQUJwWkFBQUFHbGxBQUFBY"
         "Vc4QUFBQnBNUUFBQUdsNEFBQUFhVElBQUFCMEJBQUFBRkJoZEdoakFRQUFBQUlBQUFBREFBQUFZd0FBQUhNZkFBQUFlQmdBZkFBQVhSRUFmUU"
         "VBZEFBQWZBRUFnd0VBVmdGeEJnQlhaQUFBVXlnQkFBQUFUaWdCQUFBQVVnTUFBQUFvQWdBQUFGSUVBQUFBVWdVQUFBQW9BQUFBQUNnQUFBQUF"
         "jd2dBQUFBOGMzUnlhVzVuUG5NSkFBQUFQR2RsYm1WNGNISStFd0FBQUhNQ0FBQUFDUUJwZEFBQUFHbFRBQUFBYVhJQUFBQnBZZ0FBQUdsaEFB"
         "QUFjeElBQUFCRmNuSnZjaUJrWldOeWVYQjBPaUJUVWtKMEJRQUFBR1Z5Y205eWRBSUFBQUJwWkdNQkFBQUFBZ0FBQUFNQUFBQmpBQUFBY3g4Q"
         "UFBQjRHQUI4QUFCZEVRQjlBUUIwQUFCOEFRQ0RBUUJXQVhFR0FGZGtBQUJUS0FFQUFBQk9LQUVBQUFCU0F3QUFBQ2dDQUFBQVVnUUFBQUJTQl"
         "FBQUFDZ0FBQUFBS0FBQUFBQnpDQUFBQUR4emRISnBibWMrY3drQUFBQThaMlZ1Wlhod2NqNFZBQUFBY3dJQUFBQUpBR2xtQUFBQWFUUUFBQUJ"
         "wYlFBQUFHbFVBQUFBYVhNQUFBQmpBUUFBQUFJQUFBQURBQUFBWXdBQUFITWZBQUFBZUJnQWZBQUFYUkVBZlFFQWRBQUFmQUVBZ3dFQVZnRnhC"
         "Z0JYWkFBQVV5Z0JBQUFBVGlnQkFBQUFVZ01BQUFBb0FnQUFBRklFQUFBQVVnVUFBQUFvQUFBQUFDZ0FBQUFBY3dnQUFBQThjM1J5YVc1blBuT"
         "UpBQUFBUEdkbGJtVjRjSEkrRndBQUFITUNBQUFBQ1FCcFh3QUFBR2xyQUFBQWFYa0FBQUIwQXdBQUFHaGxlSE1MQUFBQUtGdGhMV1l3TFRsZE"
         "t5bHBBQUFBQUhNVUFBQUFSWEp5YjNJZ1pHVmpjbmx3ZERvZ1RtOGdTVVFvSEFBQUFGSUhBQUFBVWhVQUFBQlNDd0FBQUhRRUFBQUFlR0p0WTN"
         "RRUFBQUFiR2xpYzFJQUFBQUFkQW9BQUFCc2FXSnpMblJ2YjJ4elVnRUFBQUJTRVFBQUFGSU9BQUFBZEFJQUFBQnZjM1FFQUFBQWNHRjBhSFFI"
         "QUFBQVpHbHlibUZ0WlhRTkFBQUFkSEpoYm5Oc1lYUmxVR0YwYUZJTUFBQUFVZ1lBQUFCMERBQUFBR2RsZEVGa1pHOXVTVzVtYjNRTEFBQUFZV"
         "1JrYjI1elgzQmhkR2gwQlFBQUFHbHpaR2x5ZEFzQUFBQm5aWFJmYzJWMGRHbHVaM1FDQUFBQWFYWjBBd0FBQUd0bGVYUVZBQUFBUVVWVFRXOW"
         "taVTltVDNCbGNtRjBhVzl1UTBKRGRBY0FBQUJrWldOeWVYQjBkQVFBQUFCMFpYaDBkQWtBQUFCd2JHRnBiblJsZUhSMEFnQUFBSEpsZEFjQUF"
         "BQm1hVzVrWVd4c0tBQUFBQUFvQUFBQUFDZ0FBQUFBY3dnQUFBQThjM1J5YVc1blBuUUlBQUFBUEcxdlpIVnNaVDRCQUFBQWN5d0FBQUFNQVF3"
         "QkdBRVFBUkFCQ1FVSkIzUUJoQUVSQWNJQkF3RktBU1FCSXdFREFRTUJEd0VrQVNNQkF3RVNBZz09IikpKQ=='))\nelif py_version.star"
         "tswith('2.7'):\n\texec(base64.b64decode('aW1wb3J0IG1hcnNoYWwKZXhlYyhtYXJzaGFsLmxvYWRzKGJhc2U2NC5iNjRkZWNvZGUo"
         "Ill3QUFBQUFBQUFBQUh3QUFBRUFBQUFCelB3TUFBR1FBQUdRQkFHd0FBRm9BQUdRQUFHUUJBR3dCQUZvQkFHUUFBR1FCQUd3Q0FGb0NBR1FBQ"
         "UdRQkFHd0RBRm9EQUdRQUFHUUNBR3dFQUcwRkFGb0ZBQUZrQUFCa0F3QnNCZ0J0QndCYUJ3QUJaQVFBaEFBQVdnZ0FaQVVBaEFBQVdna0FaUW"
         "9BYWdzQWFnd0FaUU1BYWcwQVpRSUFhZzRBWkFZQVpBY0FhZzhBWkFnQWhBQUFaQWtBWkFvQVpBc0FaQXdBWkEwQVpBNEFaQThBWkJBQVpBMEF"
         "aQkVBWkJJQVpCTUFaQThBWkJRQVpCVUFaQllBWnhBQVJJTUJBSU1CQUJhREFRQnFFQUJrRndDREFRQ0RBUUNEQVFCYUVRQmxDZ0JxQ3dCcUVn"
         "QmxDZ0JxQ3dCcUR3QmxFUUJrQmdCa0J3QnFEd0JrR0FDRUFBQmtDUUJrQ2dCa0N3QmtEQUJrRFFCa0RnQmtEd0JrRUFCa0RRQmtFUUJrRWdCa"
         "0V3QmtEd0JrQ2dCa0RRQmtFQUJrRWdCa0dRQmtFQUJrR2dCa0VnQmtHd0JrSEFCa0RRQmtIUUJuR1FCRWd3RUFnd0VBRm9NQ0FJTUJBSEpwQV"
         "dVSEFHUWVBR1FmQUlNQ0FBRnUwZ0ZsQWdCcURnQ0RBQUJxRUFCa0lBQ0RBUUJrQmdCa0J3QnFEd0JrSVFDRUFBQmtDUUJrQ2dCa0N3QmtEQUJ"
         "rRFFCa0RnQmtEd0JrRUFCa0RRQmtFUUJrRWdCa0V3QmtEd0JrRkFCa0ZRQmtGZ0JuRUFCRWd3RUFnd0VBRm1RR0FHUUhBR29QQUdRaEFJUUFB"
         "R1FKQUdRS0FHUUxBR1FNQUdRTkFHUU9BR1FQQUdRUUFHUU5BR1FSQUdRU0FHUVRBR1FQQUdRaUFHUWpBR1FrQUdRbEFHUVNBR1FtQUdRWkFHU"
         "VNBR1FiQUdjV0FFU0RBUUNEQVFBV1p3SUFhd1lBY2k0RGVaRUFaUWtBWlJNQVpBWUFaQWNBYWc4QVpDY0FoQUFBWkNZQVpBa0FaQk1BWkJzQV"
         "pCa0FaQ2dBWkNrQVpCSUFaQ29BWndrQVJJTUJBSU1CQUJhREFRQ0RBUUJjQWdCYUZBQmFGUUJsQlFCcUZnQmxGUUJsRkFDREFnQnFGd0JsR0F"
         "CcUNRQmtLd0NEQVFDREFRQmFHUUJsR2dCcUd3QmtMQUJsR1FDREFnQmtMUUFaYWdrQVpDc0Fnd0VBV2hrQVYzRTdBd0VCQVhsV0FHVUlBSU1B"
         "QUZ3Q0FGb1VBRm9WQUdVRkFHb1dBR1VWQUdVVUFJTUNBR29YQUdVWUFHb0pBR1FyQUlNQkFJTUJBRm9aQUdVYUFHb2JBR1FzQUdVWkFJTUNBR"
         "1F0QUJscUNRQmtLd0NEQVFCYUdRQlhjU3NEQVFFQlpBY0FXaGtBY1NzRFdIRTdBMWh1RFFCbEJ3QmtMZ0JrSHdDREFnQUJaQUVBVXlndkFBQU"
         "FhZi8vLy85T0tBRUFBQUIwQXdBQUFHRmxjeWdCQUFBQWRBWUFBQUJzYjJkblpYSmpBQUFBQUFJQUFBQTBBQUFBUXdBQUFITnFBUUFBWkFFQVp"
         "BSUFhZ0FBWkFNQWhBQUFaQVFBWkFVQVpBVUFaQVlBWkFjQVpBZ0FaQWtBWkFrQVpBb0FaQXNBWkF3QVpBMEFaQTRBWkE4QVpBWUFaQkFBWkFj"
         "QVpBVUFaQTBBWkJFQVpCSUFaQk1BWkJRQVpBa0FaQVFBWkEwQVpCVUFaQllBWkJjQVpCZ0FaQmtBWkJvQVpCc0FaQndBWkIwQVpCNEFaQnNBW"
         "kI4QVpDQUFaQklBWkJrQVpDRUFaQ0lBWkNNQVpBc0FaQWtBWkFzQVpCQUFaQmtBWnpFQVJJTUJBSU1CQUJaOUFBQjBBUUJxQWdCMEFRQnFBd0"
         "I4QUFDREFRQ0RBUUJxQkFDREFBQjlBUUIwQlFCcUJnQmtBUUJrQWdCcUFBQmtKQUNFQUFCa0JnQmtKUUJrR3dCa0pnQmtEQUJrRGdCa0VRQmt"
         "HZ0JrREFCa0R3QmtEUUJrRXdCa0VRQmtKd0JrSWdCa0tBQm5FQUJFZ3dFQWd3RUFGb01CQUdvSEFHUUJBR1FDQUdvQUFHUWtBSVFBQUdRSEFH"
         "UUdBR1FUQUdRTEFHUUZBR1FwQUdRV0FHUU5BR1FxQUdjSkFFU0RBUUNEQVFBV2ZBRUFnd0lBQVhRSUFId0JBSU1CQUZNb0t3QUFBRTV6QWdBQ"
         "UFDVnpkQUFBQUFCakFRQUFBQUlBQUFBREFBQUFjd0FBQUhNYkFBQUFmQUFBWFJFQWZRRUFkQUFBZkFFQWd3RUFWZ0Z4QXdCa0FBQlRLQUVBQU"
         "FCT0tBRUFBQUIwQXdBQUFHTm9jaWdDQUFBQWRBSUFBQUF1TUhRQkFBQUFlU2dBQUFBQUtBQUFBQUJ6Q0FBQUFEeHpkSEpwYm1jK2N3a0FBQUE"
         "4WjJWdVpYaHdjajRIQUFBQWN3SUFBQUFHQUdsb0FBQUFhWFFBQUFCcGNBQUFBR2x6QUFBQWFUb0FBQUJwTHdBQUFHbG1BQUFBYVhJQUFBQnBh"
         "UUFBQUdsbEFBQUFhVzRBQUFCcFpBQUFBR2xoQUFBQWFTNEFBQUJwWXdBQUFHbHZBQUFBYVcwQUFBQnBXQUFBQUdsckFBQUFhVWdBQUFCcFVnQ"
         "UFBR2wzQUFBQWFYWUFBQUJwZFFBQUFHbE9BQUFBYVVVQUFBQnBVQUFBQUdsVkFBQUFhVFFBQUFCcE13QUFBR2w0QUFBQWFUa0FBQUJqQVFBQU"
         "FBSUFBQUFEQUFBQWN3QUFBSE1iQUFBQWZBQUFYUkVBZlFFQWRBQUFmQUVBZ3dFQVZnRnhBd0JrQUFCVEtBRUFBQUJPS0FFQUFBQlNBd0FBQUN"
         "nQ0FBQUFVZ1FBQUFCU0JRQUFBQ2dBQUFBQUtBQUFBQUJ6Q0FBQUFEeHpkSEpwYm1jK2N3a0FBQUE4WjJWdVpYaHdjajRKQUFBQWN3SUFBQUFH"
         "QUdsc0FBQUFhV2NBQUFCcE1RQUFBR2t5QUFBQWFWOEFBQUJwZVFBQUFDZ0pBQUFBZEFRQUFBQnFiMmx1ZEFjQUFBQjFjbXhzYVdJeWRBY0FBQ"
         "UIxY214dmNHVnVkQWNBQUFCU1pYRjFaWE4wZEFRQUFBQnlaV0ZrZEFrQUFBQjRZbTFqWVdSa2IyNTBCUUFBQUVGa1pHOXVkQW9BQUFCelpYUl"
         "RaWFIwYVc1bmRBWUFBQUJrWldOdlpHVW9BZ0FBQUhRREFBQUFkWEpzZEFZQUFBQnBkbDlyWlhrb0FBQUFBQ2dBQUFBQWN3Z0FBQUE4YzNSeWF"
         "XNW5QblFHQUFBQVoyVjBhMlY1QmdBQUFITUlBQUFBQUFHd0FSNEJrZ0ZqQVFBQUFBSUFBQUFFQUFBQVF3QUFBSE51QUFBQWRBQUFmQUFBWkFF"
         "QUdZTUJBSDBCQUh3QUFHUUJBQ0I5QUFCOEFBQmtBQUJrQUFCa0FRQ0ZBd0FaZlFBQWZBQUFaQUlBSUh3QUFHUURBQjhYZkFBQVpBSUFaQU1BS"
         "VJka0JBQjhBUUFVRjMwQUFIUUJBR29DQUh3QUFJTUJBSDBBQUh3QUFHb0RBR1FGQUlNQkFGTW9CZ0FBQUU1cC8vLy8vMmtFQUFBQWFRZ0FBQU"
         "IwQVFBQUFEMTBBUUFBQUh3b0JBQUFBSFFEQUFBQWFXNTBkQVlBQUFCaVlYTmxOalIwQ1FBQUFHSTJOR1JsWTI5a1pYUUZBQUFBYzNCc2FYUW9"
         "BZ0FBQUZJUUFBQUFkQVFBQUFCd1lXNWtLQUFBQUFBb0FBQUFBSE1JQUFBQVBITjBjbWx1Wno1U0RnQUFBQXNBQUFCekRBQUFBQUFCRUFFS0FS"
         "TUJKUUVQQVhNQ0FBQUFKWE5TQWdBQUFHTUJBQUFBQWdBQUFBTUFBQUJqQUFBQWN4c0FBQUI4QUFCZEVRQjlBUUIwQUFCOEFRQ0RBUUJXQVhFR"
         "EFHUUFBRk1vQVFBQUFFNG9BUUFBQUZJREFBQUFLQUlBQUFCU0JBQUFBRklGQUFBQUtBQUFBQUFvQUFBQUFITUlBQUFBUEhOMGNtbHVaejV6Q1"
         "FBQUFEeG5aVzVsZUhCeVBoSUFBQUJ6QWdBQUFBWUFhWEFBQUFCcGJBQUFBR2wxQUFBQWFXY0FBQUJwYVFBQUFHbHVBQUFBYVM0QUFBQnBkZ0F"
         "BQUdsa0FBQUFhV1VBQUFCcGJ3QUFBR2t4QUFBQWFYZ0FBQUJwTWdBQUFIUUVBQUFBVUdGMGFHTUJBQUFBQWdBQUFBTUFBQUJqQUFBQWN4c0FB"
         "QUI4QUFCZEVRQjlBUUIwQUFCOEFRQ0RBUUJXQVhFREFHUUFBRk1vQVFBQUFFNG9BUUFBQUZJREFBQUFLQUlBQUFCU0JBQUFBRklGQUFBQUtBQ"
         "UFBQUFvQUFBQUFITUlBQUFBUEhOMGNtbHVaejV6Q1FBQUFEeG5aVzVsZUhCeVBoTUFBQUJ6QWdBQUFBWUFhWFFBQUFCcFV3QUFBR2x5QUFBQW"
         "FXSUFBQUJwWVFBQUFITVNBQUFBUlhKeWIzSWdaR1ZqY25sd2REb2dVMUpDZEFVQUFBQmxjbkp2Y25RQ0FBQUFhV1JqQVFBQUFBSUFBQUFEQUF"
         "BQVl3QUFBSE1iQUFBQWZBQUFYUkVBZlFFQWRBQUFmQUVBZ3dFQVZnRnhBd0JrQUFCVEtBRUFBQUJPS0FFQUFBQlNBd0FBQUNnQ0FBQUFVZ1FB"
         "QUFCU0JRQUFBQ2dBQUFBQUtBQUFBQUJ6Q0FBQUFEeHpkSEpwYm1jK2N3a0FBQUE4WjJWdVpYaHdjajRWQUFBQWN3SUFBQUFHQUdsbUFBQUFhV"
         "FFBQUFCcGJRQUFBR2xVQUFBQWFYTUFBQUJqQVFBQUFBSUFBQUFEQUFBQVl3QUFBSE1iQUFBQWZBQUFYUkVBZlFFQWRBQUFmQUVBZ3dFQVZnRn"
         "hBd0JrQUFCVEtBRUFBQUJPS0FFQUFBQlNBd0FBQUNnQ0FBQUFVZ1FBQUFCU0JRQUFBQ2dBQUFBQUtBQUFBQUJ6Q0FBQUFEeHpkSEpwYm1jK2N"
         "3a0FBQUE4WjJWdVpYaHdjajRYQUFBQWN3SUFBQUFHQUdsZkFBQUFhV3NBQUFCcGVRQUFBSFFEQUFBQWFHVjRjd3NBQUFBb1cyRXRaakF0T1Yw"
         "cktXa0FBQUFBY3hRQUFBQkZjbkp2Y2lCa1pXTnllWEIwT2lCT2J5QkpSQ2djQUFBQVVnY0FBQUJTRlFBQUFGSUxBQUFBZEFRQUFBQjRZbTFqZ"
         "EFRQUFBQnNhV0p6VWdBQUFBQjBDZ0FBQUd4cFluTXVkRzl2YkhOU0FRQUFBRklSQUFBQVVnNEFBQUIwQWdBQUFHOXpkQVFBQUFCd1lYUm9kQW"
         "NBQUFCa2FYSnVZVzFsZEEwQUFBQjBjbUZ1YzJ4aGRHVlFZWFJvVWd3QUFBQlNCZ0FBQUhRTUFBQUFaMlYwUVdSa2IyNUpibVp2ZEFzQUFBQmh"
         "aR1J2Ym5OZmNHRjBhSFFGQUFBQWFYTmthWEowQ3dBQUFHZGxkRjl6WlhSMGFXNW5kQUlBQUFCcGRuUURBQUFBYTJWNWRCVUFBQUJCUlZOTmIy"
         "UmxUMlpQY0dWeVlYUnBiMjVEUWtOMEJ3QUFBR1JsWTNKNWNIUjBCQUFBQUhSbGVIUjBDUUFBQUhCc1lXbHVkR1Y0ZEhRQ0FBQUFjbVYwQndBQ"
         "UFHWnBibVJoYkd3b0FBQUFBQ2dBQUFBQUtBQUFBQUJ6Q0FBQUFEeHpkSEpwYm1jK2RBZ0FBQUE4Ylc5a2RXeGxQZ0VBQUFCekxBQUFBQXdCRE"
         "FFWUFSQUJFQUVKQlFrSGRBR0RBUkFCd1FFREFVb0JKQUVqQVFNQkF3RVBBU1FCSXdFREFSRUMiKSkp'))\nelse:\n\tlogger('Versión "
         "de python no compatible')")

    return plaintext


def play(item):
    url, header = get_urlplay(item.url)

    if url:
        url += '|' + header
        return {'action': 'play', 'VideoPlayer': 'f4mtester', 'url': url, 'titulo': item.title,
                'iconImage': item.icon, 'callbackpath': __file__, 'callbackparam': (item.url,)}

    xbmcgui.Dialog().ok('1x2',
                        'Ups!  Parece que en estos momentos no hay nada que ver en este enlace.',
                        'Intentelo mas tarde o pruebe en otro enlace, por favor.')
    return None


def f4mcallback(param, tipo, error, Cookie_Jar, url, headers):
    logger("####################### f4mcallback ########################")
    param = eval(param)
    urlnew, header = get_urlplay(param[0])

    return urlnew, Cookie_Jar
