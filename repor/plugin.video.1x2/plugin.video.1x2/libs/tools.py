# -*- coding: utf-8 -*-

import sys, os ,re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import base64
import json
import copy
import datetime
import time
import urllib, urllib2

runtime_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('Path'))
data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('Profile'))
image_path = os.path.join(runtime_path,'resources', 'media', 'img')

# Clases auxiliares

class Item(object):
    defaults = {}

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __contains__(self, item):
        return item in self.__dict__

    def __getattribute__(self, item):
        return object.__getattribute__(self, item)

    def __getattr__(self, item):
        if item.startswith("__"):
            return object.__getattribute__(self, item)
        else:
            return self.defaults.get(item, '')

    def __str__(self):
        return '{%s}' % (', '.join(['\'%s\': %s' % (k, repr(self.__dict__[k])) for k in sorted(self.__dict__.keys())]))

    def getart(self):
        if 'fanart' not in self.__dict__:
            self.__dict__['fanart'] = os.path.join(runtime_path,'fanart.jpg')

        return [(k,self.__dict__.get(k)) for k in ['poster', 'icon', 'fanart', 'thumb'] if k in self.__dict__]

    def tourl(self):
        dump = repr(self.__dict__)
        return urllib.quote(base64.b64encode(dump))

    def fromurl(self, url):
        str_item = base64.b64decode(urllib.unquote(url))
        self.__dict__.update(eval(str_item))
        return self

    def tojson(self, path=""):
        if path:
            open(path, "wb").write(dump_json(self.__dict__))
        else:
            return dump_json(self.__dict__)

    def fromjson(self, json_item=None, path=""):
        if path:
            json_item = open(path, "rb").read()

        if type(json_item) == str:
            item = load_json(json_item)
        else:
            item = json_item
        self.__dict__.update(item)
        return self

    def clone(self, **kwargs):
        newitem = copy.deepcopy(self)
        for k, v in kwargs.items():
            '''if k in  ['plot']:
                continue'''
            setattr(newitem, k, v)
        return newitem


class proxydt(datetime.datetime):
    def __init__(self, *args, **kwargs):
        super(proxydt, self).__init__(*args, **kwargs)

    @staticmethod
    def strptime(date_string, format):
        return datetime.datetime(*(time.strptime(date_string, format)[0:6]))



class Competition:
    def __init__(self, label, names, icon=None):
        self.label = label
        self.names = names if isinstance(names, list) else [names]
        self.icon = icon

    def add_names(self,names):
        self.names.extend(names if isinstance(names,list) else [names])


class Deporte:
    def __init__(self, label, names, icon=os.path.join(image_path, 'logo.gif'), time_max=180, competitions=None):
        self.label= label
        self.names = names if isinstance(names,list) else [names]
        self.icon = icon
        self.time_max = time_max
        if isinstance(competitions,list):
            self.competitions = competitions
        elif isinstance(competitions,str):
            self.competitions = [competitions]
        else:
            self.competitions = list()

    def add_names(self,names):
        self.names.extend(names if isinstance(names,list) else [names])


    def add_competitions(self,competitions):
        if not isinstance(competitions,list):
            competitions = [competitions]

        self.competitions.extend(competitions)


    def get_competicion(self, name):
        dict_competiciones = dict()
        for competicion in self.competitions:
            if isinstance(competicion.names, str):
                lista_nombres = [competicion.names]
            else:
                lista_nombres = competicion.names
            dict_competiciones.update({(n.lower(),competicion) for n in lista_nombres})

        return dict_competiciones.get(name.lower(), Competition(name.title(),name))


class Deportes:
    def __init__(self):
        competiciones_soccer=[
            Competition('La Liga',['SPANISH LA LIGA', 'SPANISH LEAGUE'],os.path.join(image_path, 'soccer_liga_espana.png')),
            Competition('La Liga 123',['SPANISH LA LIGA 2','SPANISH LEAGUE 2'],os.path.join(image_path, 'socccer_liga_123.png')),
            Competition('Copa del Rey','COPA DEL REY',os.path.join(image_path, 'soccer_copa_del_rey.png')),
            Competition('Liga de Campeones de la UEFA','UEFA CHAMPIONS LEAGUE',os.path.join(image_path, 'soccer_champions_league.png')),
            Competition('Liga Europa de la UEFA','UEFA EUROPA LEAGUE',os.path.join(image_path, 'soccer_europa_league.png')),
            Competition('Copa Iberica','COPA IBERICA',os.path.join(image_path, 'copa_iberica.png')),
            Competition('International Champions Cup','INTERNATIONAL CHAMPIONS CUP',os.path.join(image_path, 'International_Champions_Cup.png')),
            Competition('Premier League','PREMIER LEAGUE',os.path.join(image_path, 'soccer_liga_inlaterra.png')),
            Competition('Francia Ligue 1','FRANCE LIGUE 1',os.path.join(image_path, 'soccer_liga_francia.png')),
            Competition('Supercopa de Portugal','Portugal - Super Cup',os.path.join(image_path, 'soccer_cup_portugal.png')),
            Competition('Bundesliga', 'BUNDESLIGA',os.path.join(image_path, 'soccer_liga_alemana.png')),
            Competition('Bundesliga 2', ['Germany - 2.Bundesliga', '2.Bundesliga'],os.path.join(image_path, 'soccer_budesliga2.png')),
            Competition('Primera División de México','MEXICO LIGA MX',os.path.join(image_path, 'soccer_liga_mexico.png')),
            Competition('Major League Soccer','USA MLS',os.path.join(image_path, 'soccer_liga_usa.png')),
            Competition('Primera División de Chile','CHILE PRIMERA',os.path.join(image_path, 'soccer_liga_chile.png')),
            Competition('Primera División de Argentina','ARGENTINA SUPERLIGA',os.path.join(image_path, 'soccer_liga_argentina.png')),
            Competition('Supercopa de los Países Bajos','DUTCH SUPERCUP',os.path.join(image_path, 'soccer_dutch_cup.png')),
            Competition('Serie A','ITALY SERIE A',os.path.join(image_path, 'soccer_liga_italia.png')),
            Competition('Liga de las Naciones de la UEFA','UEFA NATIONS LEAGUE',os.path.join(image_path, 'soccer_uefa_nation_league.png')),
            Competition('Clasificación para la Eurocopa 2020','UEFA EURO 2020 QUALIFIERS',os.path.join(image_path, 'soccer_eurocopa.png')),
            Competition('Primeira Liga','PORTUGAL A LIGA',os.path.join(image_path, 'soccer_liga_portugal.png')),
            Competition('Eredivisie',['HOLLAND EREDIVISIE','Netherlands - Eredivisie'],os.path.join(image_path, 'soccer_liga_holanda.png')),
            Competition('A-League','AUSTRALIA A-LEAGUE',os.path.join(image_path, 'soccer_liga_australiana.png')),
            Competition('Copa México','MEXICO COPA MX',os.path.join(image_path, 'soccer_copa_mexico.png')),
            Competition('Ekstraklasa','Poland - Ekstraklasa',os.path.join(image_path, 'soccer_polaco.png')),
            Competition('Campeonato Brasileño de Serie A', 'BRAZIL SERIE A',os.path.join(image_path, 'soccer_liga_brasil.png')),
            Competition('Liga Premier de Rusia', 'Russia - Premier League',os.path.join(image_path, 'soccer_rusia.png')),
            Competition('Liga Juvenil de la UEFA','UEFA YOUTH LEAGUE',os.path.join(image_path, 'soccer_youth_league.png')),
            Competition('Superliga de Suiza','Switzerland - Super League',os.path.join(image_path, 'soccer_suiza.png')),
            Competition('Copa Argentina','ARGENTINA CUP',os.path.join(image_path, 'soccer_copa_argentina.png')),
            Competition('Liga Premier de Ucrania','Ukraine - Premier League',os.path.join(image_path, 'soccer_ucrania.png')),
            Competition('Copa Libertadores de América','COPA LIBERTADORES',os.path.join(image_path, 'soccer_comenbol_libertadores.png')),
            Competition('Superliga de China','CHINESE SUPER LEAGUE',os.path.join(image_path, 'soccer_liga_China.png')),
            Competition('Superliga de Turquia','TURKISH SUPER LIG',os.path.join(image_path, 'soccer_liga_turquia.png')),
            Competition('Liga I','Romania - Liga 1',os.path.join(image_path, 'soccer_rumania.png')),
            Competition('Copa de la Liga de Francia','FRANCE LEAGUE CUP',os.path.join(image_path, 'soccer_copa_francia.png')),
            Competition('Copa de Alemania','DFB POKAL',os.path.join(image_path, 'soccer_copa_alemania.png')),
            Competition('Scottish Premiership','Scotland - Scottish Premiership',os.path.join(image_path, 'soccer_scot.png')),

            Competition('Amistoso',['Club Friendlies','FRIENDLY MATCH'],os.path.join(image_path, 'soccer_amistoso.png'))
        ]

        self.SOCCER = Deporte(label='Futbol', names=['SOCCER', 'Fútbol'], icon=os.path.join(image_path, 'soccer.png'), time_max=120, competitions=competiciones_soccer)
        self.TENNIS = Deporte(label='Tenis',  names=['TENNIS', 'Tenis'], icon=os.path.join(image_path, 'tennis.png'), time_max=180)
        self.MOTOGP = Deporte(label='Moto GP', names=['MOTOGP', 'Moto GP'], icon=os.path.join(image_path, 'motogp.png'), time_max=180)
        self.FORMULA1 = Deporte(label='Formula 1', names=['FORMULA1','FORMULA 1'], icon=os.path.join(image_path, 'formula_1.png'), time_max=180)
        self.RUGBY = Deporte(label='Rugby', names='RUGBY', icon=os.path.join(image_path, 'rugby.png'), time_max=120)
        self.MMA = Deporte(label='Lucha', names='MMA', icon=os.path.join(image_path, 'mma.png'), time_max=120)
        self.BOXING = Deporte(label='Boxeo', names='BOXING', icon=os.path.join(image_path, 'boxeo.png'), time_max=120)
        self.BASKETBALL = Deporte(label='Baloncesto', names='BASKETBALL', icon=os.path.join(image_path, 'basketball.png'), time_max=90)
        self.Baseball = Deporte(label='Grandes Ligas de Béisbol', names='Baseball', icon=os.path.join(image_path, 'mlsi.png'), time_max=190)
        self.CYCLING = Deporte(label='Ciclismo', names='CYCLING', icon=os.path.join(image_path, 'ciclismo.png'), time_max=180)
        self.Cricket = Deporte(label='Cricket', names='Cricket', icon=os.path.join(image_path, 'cricket_ball.png'), time_max=180)
        self.Hockey = Deporte(label='Hockey', names='Hockey', icon=os.path.join(image_path, 'Hockey.png'), time_max=180)



    def get_deporte(self,name):
        dict_deportes = dict()
        for deporte in self.__dict__.values():
            if isinstance(deporte.names, str):
                lista_nombres = [deporte.names]
            else:
                lista_nombres = deporte.names
            dict_deportes.update({(n.lower(),deporte) for n in lista_nombres})

        return dict_deportes.get(name.lower(), Deporte(name.capitalize(),name))


    def get_icon(self,sport,competition=None):
        d= self.get_deporte(sport)
        if competition:
            c = d.get_competicion(competition)
            i = c.icon if c.icon else d.icon
        else:
            i = d.icon
        return i


DEPORTES = Deportes()
class Evento(object):
    def __new__(cls, **kwargs):
        try:
            instance = object.__new__(cls)
            instance.init(kwargs)

            return instance
        except:
            return None

    def init(self, kwargs):
        for k, v in kwargs.items():
            if k in ['sport', 'competition', 'title']:
                v = v.strip()
            setattr(self, k, v)

        if {'fecha', 'hora', 'sport', 'title', 'competition'} - set(self.__dict__):
            raise()

        def date_to_local(fecha, hora, formatTime):
            def get_utc_offset():
                utc_offset = xbmcgui.Window(10000).getProperty('utc_offset')
                if not utc_offset:
                    data = httptools.downloadpage('https://time.is/es/UTC').data
                    utc = re.findall('<div id="twd">(\d+):', data, re.DOTALL)[0]
                    cest = re.findall('<span id="favt4">(\d+):', data, re.DOTALL)[0]
                    utc_offset = str(int(cest) - int(utc))
                    xbmcgui.Window(10000).setProperty('utc_offset', utc_offset)

                return int(utc_offset)

            aux = re.findall('(\d{1,2}/\d{1,2}/)(\d{2})$', fecha)
            if aux:
                fecha = aux[0][0] + '20' + aux[0][1]

            if formatTime == 'CEST':
                cest_datetime = datetime.datetime.strptime("%s %s" % (fecha, hora), '%d/%m/%Y %H:%M')

                utc_datetime = cest_datetime - datetime.timedelta(hours=get_utc_offset())

            else:
                utc_datetime = datetime.datetime.strptime("%s %s" % (fecha, hora), '%d/%m/%Y %H:%M')

            now_timestamp = time.time()
            local = utc_datetime + (
                    datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(
                now_timestamp))

            return local

        if not 'formatTime' in self.__dict__:
            self.formatTime = 'UTC'
        self.datetime = date_to_local(self.fecha.replace(".", "/"), self.hora, self.formatTime)
        self.fecha = self.datetime.date().strftime("%d-%m-%Y")
        self.hora = self.datetime.time().strftime("%H:%M")

        self.sport = DEPORTES.get_deporte(self.sport)
        self.competition = self.sport.get_competicion(self.competition)


    def __getattr__(self, item):
        if item == 'idiomas':
            try:
                channels = self.channels
                if not isinstance(channels, list):
                    channels = [channels]
                l = [c.get('idioma') for c in channels if c.get('idioma')]
                return ", ".join(set(l))
            except:
                return "N/A"


    def __str__(self):
        return str((self.fecha, self.hora, self.sport.label, self.competition.label, self.title, self.channels))


    def isFinished(self):
        ahora = datetime.datetime.now()
        duracion = datetime.timedelta(minutes=self.sport.time_max)
        return ahora > self.datetime + duracion


    def get_icon(self):
        if self.competition.icon:
            return self.competition.icon
        else:
            return self.sport.icon



# Funciones auxiliares

def logger(message, level=None):
    def encode_log(message=""):
        if type(message) == unicode:
            message = message.encode("utf8")
        elif type(message) == str:
            message = unicode(message, "utf8", errors="replace").encode("utf8")
        else:
            message = str(message)
        return message

    texto = '[%s] %s' %(xbmcaddon.Addon().getAddonInfo('id'), encode_log(message))
    if level == 'info':
        xbmc.log(texto, xbmc.LOGNOTICE)
    elif level == 'error':
        xbmc.log("######## ERROR #########", xbmc.LOGERROR)
        xbmc.log(texto, xbmc.LOGERROR)
    else:
        xbmc.log("######## DEBUG #########", xbmc.LOGNOTICE)
        xbmc.log(texto, xbmc.LOGNOTICE)


def load_json(*args, **kwargs):
    def to_utf8(dct):
        if isinstance(dct, dict):
            return dict((to_utf8(key), to_utf8(value)) for key, value in dct.iteritems())
        elif isinstance(dct, list):
            return [to_utf8(element) for element in dct]
        elif isinstance(dct, unicode):
            return dct.encode('utf-8')
        else:
            return dct

    if "object_hook" not in kwargs:
        kwargs["object_hook"] = to_utf8

    try:
        value = json.loads(*args, **kwargs)
    except Exception:
        logger('Error en load_json', 'error')
        value = {}

    return value


def dump_json(*args, **kwargs):
    if not kwargs:
        kwargs = {
            'indent': 4,
            'skipkeys': True,
            'sort_keys': True,
            'ensure_ascii': False
        }

    try:
        value = json.dumps(*args, **kwargs)
    except Exception:
        logger('Error en dump_json', 'error')
        value = ''

    return value


def get_setting(name, default=None):
    value = xbmcaddon.Addon().getSetting(name)

    if not value:
        return default

    elif value == 'true':
        return True

    elif value == 'false':
        return False

    else:
        try:
            value = int(value)
        except ValueError:
            try:
                value = long(value)
            except ValueError:
                pass
        return value


def set_setting(name, value):
    try:
        if isinstance(value, bool):
            if value:
                value = "true"
            else:
                value = "false"

        elif isinstance(value, (int, long)):
            value = str(value)

        xbmcaddon.Addon().setSetting(name, value)

    except Exception, ex:
        logger("Error al convertir '%s' no se guarda el valor \n%s" % (name, ex), 'error')
        return None

    return value


# Main
datetime.datetime = proxydt
dump = datetime.datetime.strptime('20110101', '%Y%m%d')
import httptools