# -*- coding: utf-8 -*-

from libs.tools import *
from libs import jscrypto
import requests

HOST =  get_setting('sport_url')

def mainmenu(item):
    itemlist = list()

    itemlist.append(item.clone(
        label='Agenda Sport365',
        channel='sport365',
        action='get_agenda',
        icon=os.path.join(image_path, 'sport365_logo.png'),
        url=HOST + '/es/events/-/1/-/-/120',
        plot='Basada en la web %s' % HOST
    ))

    itemlist.append(item.clone(
        label='En Emisión',
        channel='sport365',
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
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;","",data)

    fechas = re.findall('<td colspan=9[^>]+>(\d+\.\d+\.\d+)<', data)
    for fecha in fechas:
        if fecha == fechas[-1]:
            bloque = re.findall('%s<(.*?)</table>' % fecha, data)[0]
        else:
            bloque = re.findall('%s<(.*?)%s' % (fecha, fechas[fechas.index(fecha)+1]), data)[0]


        patron = 'onClick=.*?"event_([^"]+)".*?<td rowspan=2.*?src="([^"]+)".*?<td rowspan=2.*?>(\d+:\d+)<.*?<td.*?>' \
                 '([^<]+)<.*?<td.*?>(.*?)/td>.*?<tr.*?<td colspan=2.*?>([^<]+)<'

        for code, thumb, hora, titulo, datos, deporte_competicion in re.findall(patron, bloque):
            if "<span" in datos:
                calidad, idioma = re.findall('>([\w\s?]+).*?</span>([^<]+)<', datos)[0]
                canales = [{'calidad':calidad.replace("HQ", "HD"),
                            'url': HOST + '/es/links/%s/1' % code, 
                            'idioma': idioma}]
            else:
                canales = [{'calidad': 'N/A',
                            'idioma': datos[:-1], 
                            'url' : HOST + '/es/links/%s/1' % code}]

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
        key = "%s|%s" %(e.datetime,e.title)
        if key not in guide_agrupada:
            guide_agrupada[key] = e
        else:
            ev = guide_agrupada[key]
            ev.channels.extend(e.channels)

    return sorted(guide_agrupada.values(),key=lambda e: e.datetime)


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
                label= '[B][COLOR gold]%s[/COLOR][/B]' % label,
                icon= icon,
                action= None
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
        elif len(evento.channels) >1:
            new_item.action = "ver_idiomas"
            new_item.channels = evento.channels
            new_item.label += ' [%s]' % evento.idiomas
        else:
            new_item.action = "get_enlaces"
            new_item.url = evento.channels[0]['url']
            new_item.label += ' [%s]' % evento.channels[0]['idioma']
            new_item.idioma=evento.channels[0]['idioma']
            new_item.calidad=evento.channels[0]['calidad']

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
            url= i['url'],
            idioma=i['idioma'],
            calidad=i['calidad']
        ))

    if itemlist:
        itemlist.insert(0, item.clone(action='', label='[B][COLOR gold]%s[/COLOR][/B]' % item.title))

    return itemlist


def get_enlaces(item):
    itemlist = list()
    logger(item.url)
    data = httptools.downloadpage(item.url).data
    patron = "><span id='span_link_links.*?\('([^']+)"

    for n, data in enumerate(set(re.findall(patron,data))):
        data = load_json(base64.b64decode(data))
        url = None
        key = getkey()
        try:
            url = jscrypto.decode(data["ct"], key, data["s"].decode("hex"))
        except:
            try:
                key = getkey(True)
                url = jscrypto.decode(data["ct"], key, data["s"].decode("hex"))
            except:
                pass

        if url:
            itemlist.append(item.clone(
                label='    - Enlace %s' % (n + 1),
                action='play',
                key=key,
                url=url.replace('\\/','/').replace('"',"")
            ))
            logger(url.replace('\\/','/').replace('"',""))

    if itemlist:
        itemlist.insert(0, item.clone(
                        action='',
                        label='[B][COLOR gold]%s[/COLOR] [COLOR orange]%s (%s)[/COLOR][/B]' % (item.title, item.idioma, item.calidad)))

    return itemlist


def play(item):
    try:
        s = requests.Session()
        header = {'User-Agent': httptools.default_headers["User-Agent"],
                  'Referer': item.url}

        content = s.get(item.url, headers=header).content
        url = re.findall('<iframe.*?src="([^"]+)', content)

        if url and not '/images/matras.jpg' in url[0]:
            link = re.sub(r'&#(\d+);', lambda x: chr(int(x.group(1))), url[0])
            data = s.get(link, headers=header).content

            post = {k: v for k, v in re.findall('<input type="hidden" name="([^"]+)" value="([^"]+)">', data)}
            action = re.findall("action', '([^']+)", data)
            srcs = re.findall("<script src='(.*?)'>", data)

            data2 = httptools.downloadpage(action[0], post=post,headers=header).data
            burl = re.findall(r'<script\s*src=[\'"](.+?)[\'"]', data2)[-1]


            banners(s,burl, header, action[0])

            data = re.findall("\};[A-z0-9]{43}\(.*?,.*?,\s*'([^']+)'", data2)[0]

            data = load_json(base64.b64decode(data))
            url = jscrypto.decode(data["ct"], item.key, data["s"].decode("hex"))
            url = url.replace('\\/', '/').replace('"', "")

            dump = httptools.downloadpage(srcs[-1], headers=header) if srcs else None
            dump = httptools.downloadpage(url,headers=header)

            url_head = 'User-Agent=%s&Referer=%s' %(urllib.quote(httptools.default_headers["User-Agent"]), urllib.quote('http://h5.adshell.net/peer5'))
            #logger(url)

            ret = {'action': 'play',
                   'VideoPlayer': 'f4mtester',
                   'url': url + '|' + url_head,
                   'titulo': item.title}

            return ret
    except:
        pass

    xbmcgui.Dialog().ok('1x2',
                        'Ups!  Parece que en estos momentos no hay nada que ver en este enlace.',
                        'Intentelo mas tarde o pruebe en otro enlace, por favor.')
    return None


def banners(s, burl, bheaders, breferer):
    bheaders['Referer'] = breferer
    bsrc = s.get(burl, headers=bheaders).content

    burl = re.findall(r"url:'([^']+)", bsrc)[0]
    bsrc = s.get(burl, headers=bheaders).content

    burl = re.findall(r'window.location.replace\("([^"]+)"\);\s*}\)<\/script><div', bsrc)[0]
    bsrc = s.get(urllib.quote(burl, ':/()!@#$%^&;><?')).status_code


def getkey(overwrite=False):
    key = get_setting("sport_key")
    if not key or overwrite:
        data = httptools.downloadpage(HOST + "/es/home").data

        js = re.findall('src="(http://s1.medianetworkinternational.com/js/[A-z0-9]{32}.js)', data)
        data_js = httptools.downloadpage(js[-1]).data

        result = ''
        str_wise = re.findall(".join\(''\);\}\('(.*?)\)\);", data_js)
        while str_wise:
            result = unwise(str_wise[0])
            if not "w,i,s,e" in result:
                break
            str_wise = re.findall(".join\(''\);\}\('(.*?)\)\);", result)

        key = re.findall('return "([^"]+)"', result)
        if key:
            key = set_setting("sport_key", key[0])
        logger('key: %s' %key)
    return key


def unwise(data):
    cadena1, cadena2, cadena3, cadena4 = data.split("','")
    cadena4 = cadena4.replace("'", "")
    j = 0
    c = 0
    i = 0
    list1 = []
    list2 = []
    while True:
        if j < 5:
            list2.append(cadena1[j])
        else:
            if j < len(cadena1):
                list1.append(cadena1[j])
        j += 1
        if c < 5:
            list2.append(cadena2[c])
        else:
            if c < len(cadena2):
                list1.append(cadena2[c])
        c += 1
        if i < 5:
            list2.append(cadena3[i])
        else:
            if i < len(cadena3):
                list1.append(cadena3[i])
        i += 1
        if (len(cadena1) + len(cadena2) + len(cadena3) + len(cadena4)) == (len(list1) + len(list2) + len(cadena4)):
            break
    cadena5 = "".join(list1)
    cadena6 = "".join(list2)
    c = 0
    resultado = []
    j = 0
    for j in range(0, len(list1), 2):
        operando = -1
        if (ord(cadena6[c]) % 2):
            operando = 1

        try:
            resultado.append(chr(int(cadena5[j:j + 2], 36) - operando))
        except:
            pass
        c += 1
        if c >= len(list2):
            c = 0
    result = "".join(resultado)

    return result