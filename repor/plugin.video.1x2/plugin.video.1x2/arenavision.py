# -*- coding: utf-8 -*-

import urllib2
import re
from libs.tools import *

headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0'}
dict_deportes = {
    'SOCCER': {
        'max': 120,
        'icon': os.path.join(image_path, 'soccer.png'),
        'label': 'Futbol',
        'competitions': {
            'SPANISH LA LIGA':{
              'label': 'La Liga',
              'icon': os.path.join(image_path, 'soccer_liga_espana.png'),
            },
            'SPANISH LEAGUE':{
              'label': 'La Liga',
              'icon': os.path.join(image_path, 'soccer_liga_espana.png'),
            },
            'SPANISH LA LIGA 2':{
              'label': 'La Liga 123',
              'icon': os.path.join(image_path, 'socccer_liga_123.png'),
            },
            'SPANISH LEAGUE 2':{
              'label': 'La Liga 123',
              'icon': os.path.join(image_path, 'socccer_liga_123.png'),
            },
            'COPA DEL REY':{
              'label': 'Copa del Rey',
              'icon': os.path.join(image_path, 'soccer_copa_del_rey.png'),
            },
            'UEFA CHAMPIONS LEAGUE':{
              'label': 'Liga de Campeones de la UEFA',
              'icon': os.path.join(image_path, 'soccer_champions_league.png'),
            },
            'UEFA EUROPA LEAGUE':{
              'label': 'Liga Europa de la UEFA',
              'icon': os.path.join(image_path, 'soccer_europa_league.png'),
            },
            'COPA IBERICA':{
              'label': 'Copa Iberica',
              'icon': os.path.join(image_path, 'copa_iberica.png'),
            },
            'INTERNATIONAL CHAMPIONS CUP':{
              'label': 'International Champions Cup',
              'icon': os.path.join(image_path, 'International_Champions_Cup.png'),
            },
            'PREMIER LEAGUE':{
              'label': 'Premier League',
              'icon': os.path.join(image_path, 'soccer_liga_inlaterra.png'),
            },
            'FRANCE LIGUE 1':{
              'label': 'Francia Ligue 1',
              'icon': os.path.join(image_path, 'soccer_liga_francia.png'),
            },
            'BUNDESLIGA':{
              'label': 'Bundesliga',
              'icon': os.path.join(image_path, 'soccer_liga_alemana.png'),
            },
            'MEXICO LIGA MX':{
              'label': ' Primera División de México',
              'icon': os.path.join(image_path, 'soccer_liga_mexico.png'),
            },
            'USA MLS':{
              'label': 'Major League Soccer',
              'icon': os.path.join(image_path, 'soccer_liga_usa.png'),
            },
            'COLOMBIA PRIMERA':{
              'label': 'Categoría Primera A',
              'icon': os.path.join(image_path, 'soccer_liga_colombia.png'),
            },
            'FRIENDLY MATCH':{
              'label': 'Amistoso',
              'icon': os.path.join(image_path, 'soccer_amistoso.png'),
            }
        }
    },
    'TENNIS': {
        'max': 180,
        'icon': os.path.join(image_path, 'tennis.png'),
        'label': 'Tenis'
    },
    'MOTOGP': {
        'max': 180,
        'icon': os.path.join(image_path, 'motogp.png'),
        'label': 'Moto GP'
    },
    'FORMULA 1': {
        'max': 180,
        'icon': os.path.join(image_path, 'formula_1.png'),
    },
    'RUGBY': {
        'max': 180,
        'icon': os.path.join(image_path, 'rugby.png'),
    },
    'MMA': {
        'max': 120,
        'icon': os.path.join(image_path, 'mma.png'),
        'label': 'Lucha'
    },
    'BOXING': {
        'max': 120,
        'icon': os.path.join(image_path, 'boxeo.png'),
        'label': 'Boxeo'
    },
    'BASKETBALL': {
        'max': 90,
        'icon': os.path.join(image_path, 'basketball.png'),
        'label': 'Baloncesto'
    },
    'CYCLING': {
        'max': 180,
        'icon': os.path.join(image_path, 'ciclismo.png'),
        'label': 'Ciclismo'
    }
}


def date_to_local(fecha, hora, formatTime='UTC'):
    def get_utc_offset():
        utc_offset = xbmcgui.Window(10000).getProperty('utc_offset')
        if not utc_offset:
            data = urllib2.urlopen(urllib2.Request('https://time.is/es/UTC', headers=headers)).read()
            utc = re.findall('<div id="twd">(\d+):', data, re.DOTALL)[0]
            cest = re.findall('<span id="favt4">(\d+):', data, re.DOTALL)[0]
            utc_offset = str(int(cest) - int(utc))
            xbmcgui.Window(10000).setProperty('utc_offset', utc_offset)

        return int(utc_offset)

    if formatTime == 'CEST':
        try:
            cest_datetime = datetime.datetime.strptime("%s %s" % (fecha, hora), '%d/%m/%Y %H:%M')
        except:
            cest_datetime = datetime.datetime.strptime("%s 2019 %s" % (fecha, hora), '%d %b %Y %H:%M')

        utc_datetime = cest_datetime - datetime.timedelta(hours=get_utc_offset())

    else:
        try:
            utc_datetime = datetime.datetime.strptime("%s %s" % (fecha, hora), '%d/%m/%Y %H:%M')
        except:
            utc_datetime = datetime.datetime.strptime("%s 2019 %s" % (fecha, hora), '%d %b %Y %H:%M')

    now_timestamp = time.time()
    local = utc_datetime + (
            datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp))

    return local


class Evento(object):
    def __new__(cls,** kwargs):
        try:
            datetime = date_to_local(kwargs['fecha'], kwargs['hora'], kwargs['formatTime'])
            instance =  object.__new__(cls)

            # __init__
            instance.datetime = datetime
            instance.fecha = datetime.date().strftime("%d-%m-%Y")
            instance.hora = datetime.time().strftime("%H:%M")
            instance.sport = kwargs['sport'].strip()
            instance.competition = kwargs['competition'].strip()
            instance.title = re.sub('<br\s*/>', '', kwargs['title']).strip()
            instance.channels = kwargs['channels']
            instance.idiomas = ", ".join({c.get('idioma') for c in kwargs['channels'] if c.get('idioma')})

            return instance

        except:

            return None


    def __str__(self):
        return str((self.fecha, self.hora, self.sport, self.competition, self.title, self.channels))


    def isFinished(self):
        if self.sport in dict_deportes:
            ahora = datetime.datetime.now()
            duracion = datetime.timedelta(minutes=dict_deportes[self.sport].get('max'))
            return ahora > self.datetime + duracion
        else:
            return False


    def get_label(self):
        deporte = dict_deportes.get(self.sport, {})
        competicion = deporte.get('competitions', {}).get(self.competition, {})
        competicion_label = competicion.get('label', self.competition.title())

        # TODO ¿colorear etiquetas?
        label = "[COLOR lime]%s[/COLOR] (%s) %s [%s]" \
                % (self.hora, competicion_label, self.title, self.idiomas)

        return label

    def get_icon(self):
        deporte = dict_deportes.get(self.sport, {})
        competicion = deporte.get('competitions', {}).get(self.competition, {})

        return competicion.get('icon', deporte.get('icon'))


def read_guide(url):
    guide = []

    data = urllib2.urlopen(urllib2.Request(url, headers=headers)).read()
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|\xc2\xa0", "", data)

    if 'arenavision' in url:
        url_guide = re.findall('<a href="([^"]+)">EVENTS GUIDE', data)

        if url_guide:
            url += url_guide[0]

            data = urllib2.urlopen(urllib2.Request(url, headers=headers)).read()
            data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;|\xc2\xa0", "", data)

            url_canal= {canal:url for url, canal in re.findall('<a href="([^"]+)">ArenaVision (\d+)</a>', data)}

            patron = '<tr[^>]*><td [^<]+>([^<]+)</td><td [^>]+>([^<]+)</td><td [^>]+>([^<]+)</td><td [^>]+>([^<]+)</td>' \
                     '<td [^>]+>(.*?)</td><td [^>]+>(.*?)</td></tr>'

            for e in re.findall(patron, data, re.DOTALL):
                channels = list()
                for canal_idioma in e[5].split('<br />'):
                    canales, idioma = re.findall('(.*?)(\w{3})', canal_idioma, re.DOTALL)[0]
                    for num in re.findall('(\d+)', canales, re.DOTALL):
                        channels.append(
                            {'url': get_setting('arena_url') + url_canal[num],
                             'num': num,
                             'idioma': idioma})

                if channels:
                    evento = Evento(fecha=e[0],hora=e[1].replace(' CEST', ''),formatTime='CEST', sport=e[2],
                                    competition=e[3],title=e[4],channels=channels)
                    if evento:
                        guide.append(evento)


    elif 'acelisting' in url:
        patron = '<td class="text-right">([^<]+)</td></tr><tr><td class="xsmall text-muted">([^<]+)</td></tr></table>' \
                 '</td><td>([^<]+)</td><td><table class="table-no-spacing"><tr><td colspan="2">([^<]+)</td></tr><tr>' \
                 '<td class="xsmall text-muted">([^<]+)</td></tr></table></td><td class="align-middle">(.*?)</td>'

        for e in re.findall(patron, data, re.DOTALL):
            channels = list()
            for url, num, idioma in re.findall('href="([^"]+)".*?>Channel\s(\d+).*?Language\s(\w{3})', e[5], re.DOTALL):
                channels.append(
                    {'url': url,
                     'num': num,
                     'idioma': idioma})

            if channels:
                evento = Evento(fecha=e[1], hora=e[0], formatTime='UTC', sport=e[2],
                                competition=e[4], title=e[3], channels=channels)
                if evento:
                    guide.append(evento)

    return guide


def get_categorias(item):
    itemlist = []

    guide = read_guide(item.url)
    guide = list(filter(lambda e: not e.isFinished(), guide))

    sports_in_guide = {evento.sport for evento in guide}
    competitions_in_guide = {evento.competition for evento in guide}

    for sp in sports_in_guide:
        if sp in dict_deportes:
            deporte = dict_deportes[sp]
            itemlist.append(item.clone(
                label='%s' % deporte.get('label', sp.capitalize()),
                action='get_agenda',
                icon=deporte.get('icon'),
                sport=sp
            ))

            for comp in competitions_in_guide:
                if comp in deporte.get('competitions', []):
                    competicion = deporte.get('competitions')[comp]
                    itemlist.append(item.clone(
                        label='    - %s' % competicion.get('label', comp.capitalize()),
                        action='get_agenda',
                        icon=competicion.get('icon', item.icon),
                        sport=sp,
                        competition=comp
                    ))

    if itemlist:
        itemlist.insert(0, item.clone(label='Ver todos los eventos', action='get_agenda'))
    else:
        itemlist = get_agenda(item)

    return itemlist


def get_agenda(item):
    itemlist = []

    guide = read_guide(item.url)
    guide = list(filter(lambda e: not e.isFinished(), guide))

    fechas = []
    for evento in guide:
        if item.sport and (item.sport != evento.sport or (item.competition and item.competition != evento.competition)):
            continue

        if evento.fecha not in fechas:
            fechas.append(evento.fecha)
            itemlist.append(item.clone(
                label= '[B][COLOR gold]%s[/COLOR][/B]' % evento.fecha, # TODO ¿colorear etiquetas?
                icon= os.path.join(image_path, 'logo.png'),
                action= None
            ))

        icon_evento = evento.get_icon()

        itemlist.append(item.clone(
            title=evento.title,
            label=evento.get_label(),
            icon=icon_evento if icon_evento else item.icon,
            action = 'list_channels',
            channels = evento.channels
        ))

    return itemlist


def list_channels(item):
    itemlist = list()

    for c in item.channels:
        url = c['url']

        if not url.startswith('acestream://'):
            data = urllib2.urlopen(urllib2.Request(url, headers=headers)).read()
            data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
            url = re.findall('<a href="(acestream[^"]+)"', data, re.DOTALL)
            url = url[0] if url else None

        if url:
            itemlist.append(item.clone(
                label='Canal [COLOR red]%s[/COLOR] [COLOR lime][%s][/COLOR]' % (c['num'], c['idioma']), # TODO ¿colorear etiquetas?
                action='play',
                url='plugin://program.plexus/?mode=1&url=%s&name=Video' % url
            ))

    return itemlist


def main(item):
    if 'arenavision' in item.url:
        item.url = get_setting('arena_url')

    if get_setting('get_categorias'):
        itemlist =  get_categorias(item)
    else:
        itemlist = get_agenda(item)

    if not itemlist:
        xbmcgui.Dialog().ok('1x2',
                            'Ups!  Parece que en estos momentos no hay eventos programados.',
                            'Intentelo mas tarde, por favor.')


    return itemlist