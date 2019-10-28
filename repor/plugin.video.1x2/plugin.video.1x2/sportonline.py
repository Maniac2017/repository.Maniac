# -*- coding: utf-8 -*-

from libs.tools import *
from libs import jsunpack
import threading

def mainmenu(item):
    itemlist = list()

    itemlist.append(item.clone(
        label='Agenda',
        action='get_agenda',
        #icon=os.path.join(image_path, 'arenavisionlogo1.png'),
        plot='Muestra la Agenda SportOnline'
    ))

    itemlist.append(item.clone(
        label='Canales',
        action='list_all_channels',
        # icon=os.path.join(image_path, 'arenavisionlogo1.png'),
        plot='Muestra todos los canales en directo'
    ))

    return itemlist


def list_all_channels(item):
    itemlist = list()

    for n, url in enumerate(get_channels_sportzonline()):
        itemlist.append(item.clone(
            label = '[COLOR red]Canal %s[/COLOR]' % (n + 1),
            title = 'SportOnline - Canal %s' % (n+1),
            action='play',
            isPlayable=True,
            url=url
        ))

    return itemlist


def get_channels_sportzonline():
    threads = list()
    ret = []

    def check_channel(url_ini, ret):
        data = httptools.downloadpage(url_ini).data
        url = 'https:' + re.findall('<iframe src="([^"]+)', data)[0]
        data = httptools.downloadpage(url, headers={'Referer': url}).data
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

        packed = re.findall('<script>(eval.*?)</script>', data)[0]
        url = re.findall('source:"([^"]+)', jsunpack.unpack(packed))

        if url and httptools.downloadpage(url[0]).code == 200:
            ret.append(url_ini)

    for n in range(1, 9):
        url = 'https://sportzonline.co/channels/hd/hd%s.php' %n
        t = threading.Thread(target=check_channel, args=(url, ret))
        threads.append(t)
        t.setDaemon(True)
        t.start()

    running = [t for t in threads if t.isAlive()]
    while running:
        time.sleep(0.5)
        running = [t for t in threads if t.isAlive()]

    return ret



def read_guide():
    guide = list()
    idioma_esp = {
        'ITALIAN': 'Italiano',
        'ENGLISH': 'Inglés',
        'DUTCH': 'Holandes',
        'GERMAN': 'Alemán',
        'POLISH': 'Polaco',
        'FRENCH': 'Francés',
        'SPANISH': 'Español',
        'GREEK': 'Griego',
        'BRAZILIAN': 'Portugues',
        'ROMANIAN': 'Rumano',
        'TURKISH': 'Turco'}
    week = ['MONDAY','TUESDAY','WENSDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY']

    data = re.sub(r"\r", "", httptools.downloadpage('https://sportzonline.to/prog.txt').data)
    data = re.sub(r"(MONDAY|TUESDAY|WENSDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)\n", r"%&%\1\n", data) + '\n%&%'
    #logger(data)

    # dia actualizacion
    fecha_up = re.findall('LAST UPDATE\s?:\s?(\d{1,2}-\d{1,2}-)', data)[0] + '2019'
    up_datetime = datetime.datetime.strptime(fecha_up, '%d-%m-%Y')
    #logger(week[up_datetime.weekday()])

    agenda = re.findall('(MONDAY|TUESDAY|WENSDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)(.*?)%&%', data,re.MULTILINE|re.DOTALL)

    if agenda:
        c1 = week.index(agenda[0][0].upper()) + 1
        if c1 == 7: c1 = 0
        if up_datetime.weekday() == c1:
            up_datetime = up_datetime - datetime.timedelta(days=1)

    # agenda diaria
    for ad in agenda:
        #logger(week.index(ad[0].upper()))
        if up_datetime.weekday() < week.index(ad[0].upper()):
            fecha_evento = up_datetime + datetime.timedelta(days=week.index(ad[0].upper()) - up_datetime.weekday())
        elif up_datetime.weekday() > week.index(ad[0].upper()):
            fecha_evento = up_datetime + datetime.timedelta(days=week.index(ad[0].upper()) + 7 - up_datetime.weekday())
        else:
            fecha_evento = up_datetime
        #logger(fecha_evento)

        # idiomas del dia
        idiomas_eng = dict(re.findall('(HD\d+)\s([^\s]+)', ad[1]))

        # eventos del dia
        hora_ant = datetime.time(0,0)
        for e in re.findall('(\d{1,2}:\d{2}.*?php)', ad[1]):
            hora, titulo, url = re.findall('(\d+:\d+)\s*([^|]+)\|\s(.*?)\.php', e)[0]

            if 'pt/sporttv' in url or '/bra/br' in url:
                idioma = 'Portugués'
            else:
                idioma = url.split('/')[-1].upper()
                idioma = idioma_esp.get(idiomas_eng[idioma],'')

            hora_evento = datetime.datetime.strptime(hora, '%H:%M').time()
            if hora_evento < hora_ant:
                fecha_evento = fecha_evento + datetime.timedelta(days=1)
            hora_ant = hora_evento
            dt_evento = datetime.datetime.combine(fecha_evento, hora_evento)
            fecha_hora_CEST = dt_evento + datetime.timedelta(hours=1)
            fecha_hora_local = date_to_local(datetime.datetime.strftime(fecha_hora_CEST, '%d/%m/%Y'),
                                       datetime.datetime.strftime(fecha_hora_CEST, '%H:%M'), 'CEST')

            guide.append({
                'fecha': fecha_hora_local.date(),
                'hora': fecha_hora_local.time(),
                'title': titulo.strip().replace(' x ', ' vs ').replace(' @ ', ' vs. '),
                'url': url + '.php',
                'idioma': idioma})

    return guide


def get_agenda(item):
    itemlist = []

    fechas = list()
    le = dict()
    for evento in read_guide():
        id = '%s-%s-%s' %(evento['fecha'], evento['hora'], evento['title'])
        if id not in le:
            evento['url'] = [evento['url']]
            evento['idioma'] = [evento['idioma']]
            le[id]= evento
        else:
            le[id]['url'].append(evento['url'])
            le[id]['idioma'].append(evento['idioma'])


    for evento in sorted(le.values(), key=lambda x: (x['fecha'], x['hora'])):
        if evento['fecha'] not in fechas:
            fechas.append(evento['fecha'])
            label = evento['fecha'].strftime('%d/%m/%Y')
            itemlist.append(item.clone(
                label='[B][COLOR gold]%s[/COLOR][/B]' % label,
                icon=os.path.join(image_path, 'logo.gif'),
                action=None
            ))

        idiomas = evento['idioma'][0] if len(evento['idioma']) == 1 else ', '.join(set(evento['idioma']))
        new_item = item.clone(
            label= '%s %s (%s)' %(evento['hora'].strftime('%H:%M'), evento['title'], idiomas),
            title= evento['title']
            )

        if len(evento['url']) == 1:
            new_item.isPlayable=True
            new_item.action= 'play'
            new_item.url= evento['url'][0]
        else:
            new_item.isPlayable = False
            new_item.action = 'list_channels_play'
            new_item.url = evento['url']
            new_item.idiomas = evento['idioma']

        itemlist.append(new_item)

    return itemlist


def list_channels_play(item):
    itemlist = []

    for n,url in enumerate(item.url):
        itemlist.append(item.clone(
            label = 'Canal %s (%s)' %((n+1), item.idiomas[n]),
            isPlayable = True,
            action = 'play',
            url = url
        ))

    return itemlist


def play(item):
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

'''
============================================================

               | LAST UPDATE : 18-10-19 |
		   		   
INFO: PLEASE USE DOMAIN LISTED BELOW ALWAYS!
INFO: PLEASE USE DOMAIN LISTED BELOW ALWAYS!
INFO: PLEASE USE DOMAIN LISTED BELOW ALWAYS!

ANY INFO CONTACT: 4723346971@protonmail.com
ANY INFO CONTACT: 4723346971@protonmail.com
ANY INFO CONTACT: 4723346971@protonmail.com

24/7 CHANNELS https://sportzonline.co/247.txt
24/7 CHANNELS https://sportzonline.co/247.txt
24/7 CHANNELS https://sportzonline.co/247.txt

============================================================

THURSDAY
HD1 ENGLISH
HD2 ENGLISH
HD5 ENGLISH

BR2 BRAZILIAN

00:30   NFL: Kansas @ Denver | https://sportzonline.co/channels/hd/hd1.php
01:00   Moto GP: Japanese GP - FP1 & FP2 | https://sportzonline.co/channels/hd/hd5.php
01:00   Moto GP: Japanese GP - FP1 & FP2 | https://sportzonline.co/channels/pt/sporttv5.php
01:30   Cuiabá x Guarani | https://sportzonline.co/channels/bra/br2.php
02:30   NBA: Dallas Mavericks @ LA Clippers | https://sportzonline.co/channels/hd/hd2.php

FRIDAY
HD1 ENGLISH
HD2 ENGLISH
HD3 GERMAN
HD4 FRENCH
HD5 ENGLISH
HD6 SPANISH
HD7 ITALIAN
HD8 TURKISH/ENGLISH

BR2 BRAZILIAN
BR3 BRAZILIAN

08:20   2019 RL World Cup 9s | https://sportzonline.co/channels/hd/hd1.php
09:30	Melbourne Victory x Western Sydney Wanderers | https://sportzonline.co/channels/pt/sporttv1.php
11:00   ICC World T20 Qualifier | https://sportzonline.co/channels/hd/hd1.php 
11:00   European Tour: French Open - 2nd Day | https://sportzonline.co/channels/pt/sporttv4.php
13:00   ATP 250: Atwerp | https://sportzonline.co/channels/pt/sporttv3.php
17:30	Erzgebirge Aue x Nürnberg | https://sportzonline.co/channels/hd/hd3.php
18:30	Galatasaray x Sivasspor | https://sportzonline.co/channels/hd/hd8.php
18:30	Galatasaray x Sivasspor | https://sportzonline.co/channels/pt/sporttv2.php
19:30	Eintracht Frankfurt x Bayer Leverkusen | https://sportzonline.co/channels/hd/hd5.php
19:30	Eintracht Frankfurt x Bayer Leverkusen | https://sportzonline.co/channels/hd/hd3.php
19:45	Nice x PSG | https://sportzonline.co/channels/hd/hd2.php
19:45	Nice x PSG | https://sportzonline.co/channels/hd/hd4.php
19:45	Cardiff City x Sheffield Wednesday | https://sportzonline.co/channels/hd/hd1.php
20:00	Granada x Osasuna | https://sportzonline.co/channels/hd/hd6.php
20:00	Cittadella x Cosenza | https://sportzonline.co/channels/hd/hd7.php
20:30	Cova Piedade x Benfica | https://sportzonline.co/channels/pt/sporttv1.php
23:15   Criciúma x CRB | https://sportzonline.co/channels/bra/br2.php
00:00   NHL: Pittsburgh @ Dallas | https://sportzonline.co/channels/pt/sporttv3.php
00:00   UFC: Prelims | https://sportzonline.co/channels/hd/hd2.php
00:00   UFC: Prelims | https://sportzonline.co/channels/bra/br3.php
01:00   Moto GP: Japanese GP - FP3 & Qualifying | https://sportzonline.co/channels/hd/hd5.php
01:00   Moto GP: Japanese GP - FP3 & Qualifying | https://sportzonline.co/channels/pt/sporttv5.php
01:00	Puebla x Atlas | https://sportzonline.co/channels/hd/hd1.php
01:30   Vitória x Londrina | https://sportzonline.co/channels/bra/br2.php
02:00   UFC: Reyes vs Weidman | https://sportzonline.co/channels/hd/hd2.php
02:00   UFC: Reyes vs Weidman | https://sportzonline.co/channels/pt/sporttv1.php
02:00   UFC: Reyes vs Weidman | https://sportzonline.co/channels/bra/br3.php
02:30   NBA: Los Angeles Lakers @ Golden State Warriors | https://sportzonline.co/channels/hd/hd8.php
03:00	Veracruz x Tigres UANL | https://sportzonline.co/channels/hd/hd1.php

SATURDAY
HD1 ENGLISH
HD2 ENGLISH
HD3 GERMAN
HD4 FRENCH
HD5 ENGLISH
HD6 SPANISH
HD7 ITALIAN
HD8 DUTCH

08:15   Rugby World Cup: England x Australia | https://sportzonline.co/channels/pt/sporttv1.php
11:15   Rugby World Cup: New Zealand x Ireland | https://sportzonline.co/channels/pt/sporttv1.php
11:30   European Tour: French Open - 3rd Day | https://sportzonline.co/channels/pt/sporttv4.php
12:00	St. Pauli x Darmstadt 98 | https://sportzonline.co/channels/hd/hd3.php
12:00	Eibar x Barcelona | https://sportzonline.co/channels/hd/hd5.php
12:00	Eibar x Barcelona | https://sportzonline.co/channels/hd/hd6.php
12:30	Everton x West Ham United | https://sportzonline.co/channels/hd/hd1.php
12:30	Everton x West Ham United | https://sportzonline.co/channels/pt/sporttv2.php
12:35	Beijing Guoan x Shanghai SIPG | https://sportzonline.co/channels/pt/sporttv5.php
14:00	Lazio x Atalanta | https://sportzonline.co/channels/hd/hd7.php
14:00	Lazio x Atalanta | https://sportzonline.co/channels/pt/sporttv3.php
14:00	Le Havre x Lorient | https://sportzonline.co/channels/hd/hd4.php
14:30	Augsburg x Bayern München | https://sportzonline.co/channels/hd/hd8.php
14:30	Augsburg x Bayern München | https://sportzonline.co/channels/hd/hd3.php
15:00	Wolverhampton Wanderers x Southampton | https://sportzonline.co/channels/pt/sporttv2.php
15:00	Chelsea x Newcastle United | https://sportzonline.co/channels/hd/hd2.php
15:00	Tottenham Hotspur x Watford | https://sportzonline.co/channels/hd/hd1.php
15:00	Atlético Madrid x Valencia | https://sportzonline.co/channels/hd/hd5.php
15:00	Atlético Madrid x Valencia | https://sportzonline.co/channels/hd/hd6.php
16:00   ATP 250: Atwerp | https://sportzonline.co/channels/pt/sporttv5.php
16:30	Olympique Lyonnais x Dijon | https://sportzonline.co/channels/hd/hd4.php
17:00	Napoli x Hellas Verona | https://sportzonline.co/channels/hd/hd7.php
17:00	Napoli x Hellas Verona | https://sportzonline.co/channels/pt/sporttv3.php
17:30	Getafe x Leganés | https://sportzonline.co/channels/hd/hd5.php
17:30	Getafe x Leganés | https://sportzonline.co/channels/hd/hd6.php
17:30	Borussia Dortmund x Borussia M'gladbach | https://sportzonline.co/channels/hd/hd3.php
17:30	Crystal Palace x Manchester City | https://sportzonline.co/channels/hd/hd1.php
17:30	Crystal Palace x Manchester City | https://sportzonline.co/channels/pt/sporttv2.php
17:30	RKC Waalwijk x Ajax | https://sportzonline.co/channels/hd/hd8.php
17:30	RKC Waalwijk x Ajax | https://sportzonline.co/channels/pt/sporttv4.php
18:00	Ankaragücü x Beşiktaş | https://sportzonline.co/channels/pt/sporttv5.php
18:45	Coimbrões x Porto | https://sportzonline.co/channels/pt/sporttv1.php
19:00	Toulouse x Lille | https://sportzonline.co/channels/hd/hd4.php
19:45	Juventus x Bologna | https://sportzonline.co/channels/hd/hd7.php
19:45	Juventus x Bologna | https://sportzonline.co/channels/pt/sporttv3.php
19:45	Utrecht x PSV | https://sportzonline.co/channels/hd/hd8.php
19:45	Utrecht x PSV | https://sportzonline.co/channels/pt/sporttv4.php
20:00	Mallorca x Real Madrid | https://sportzonline.co/channels/hd/hd5.php
20:00	Mallorca x Real Madrid | https://sportzonline.co/channels/hd/hd6.php
20:45	Leça x Sporting Braga | https://sportzonline.co/channels/pt/sporttv5.php
00:00   Toronto FC x DC United | https://sportzonline.co/channels/pt/sporttv1.php
03:15   Moto 3: Japanese GP - Race | https://sportzonline.co/channels/hd/hd5.php
05:00   Moto 2: Japanese GP - Race | https://sportzonline.co/channels/hd/hd5.php
06:30   Moto GP: Japanese GP - Race | https://sportzonline.co/channels/hd/hd5.php

SUNDAY
HD1 ENGLISH
HD2 ENGLISH
HD3 GERMAN
HD4 FRENCH
HD5 ENGLISH
HD6 SPANISH
HD7 ITALIAN
HD8 DUTCH

08:15   Rugby World Cup: Wales vs France | https://sportzonline.co/channels/pt/sporttv1.php
11:00	Deportivo Alavés x Celta de Vigo | https://sportzonline.co/channels/hd/hd6.php
11:15   Rugby World Cup: Japan vs South Africa | https://sportzonline.co/channels/pt/sporttv1.php
11:30	Sassuolo x Internazionale | https://sportzonline.co/channels/hd/hd7.php
11:30	Sassuolo x Internazionale |  https://sportzonline.co/channels/pt/sporttv2.php
11:30   European Tour: French Open - 4th Day | https://sportzonline.co/channels/pt/sporttv4.php
12:00	Accrington Stanley x Ipswich Town | https://sportzonline.co/channels/hd/hd1.php
12:15	Hearts x Rangers | https://sportzonline.co/channels/hd/hd2.php
12:30	Stuttgart x Holstein Kiel | https://sportzonline.co/channels/hd/hd3.php
13:30	Groningen x Sparta Rotterdam | https://sportzonline.co/channels/hd/hd8.php
14:00	Bordeaux x Saint-Étienne | https://sportzonline.co/channels/hd/hd4.php
14:00	Sampdoria x Roma | https://sportzonline.co/channels/hd/hd5.php
14:00	Sampdoria x Roma | https://sportzonline.co/channels/hd/hd7.php
14:00	Sampdoria x Roma | https://sportzonline.co/channels/pt/sporttv1.php
14:00   Udinese x Torino | https://sportzonline.co/channels/pt/sporttv2.php
14:00	Wigan Athletic x Nottingham Forest | https://sportzonline.co/channels/hd/hd1.php
14:30	Köln x Paderborn | https://sportzonline.co/channels/hd/hd3.php
15:00	Espanyol x Villarreal | https://sportzonline.co/channels/hd/hd6.php
15:00   ATP 250: Atwerp - Final | https://sportzonline.co/channels/pt/sporttv5.php
15:45	Feyenoord x Heracle | https://sportzonline.co/channels/hd/hd8.php
16:00	Monaco x Rennes | https://sportzonline.co/channels/hd/hd4.php
16:30	Manchester United x Liverpool | https://sportzonline.co/channels/hd/hd1.php
16:30	Manchester United x Liverpool |  https://sportzonline.co/channels/pt/sporttv1.php
17:00	Hoffenheim x Schalke 04 | https://sportzonline.co/channels/hd/hd3.php
17:00   NFL: Oakland Raiders @ Green Bay Packers | https://sportzonline.co/channels/hd/hd2.php
17:00	Parma x Genoa | https://sportzonline.co/channels/hd/hd5.php
17:00	Parma x Genoa | https://sportzonline.co/channels/hd/hd7.php
17:00	Parma x Genoa | https://sportzonline.co/channels/pt/sporttv2.php
17:00   Denizlispor x Fernerbahçe | https://sportzonline.co/channels/pt/sporttv3.php
17:30	Athletic Club x Real Valladolid | https://sportzonline.co/channels/hd/hd6.php
19:20   NASCAR: Hollywood Casino 400 - Kansas Speedway | https://sportzonline.co/channels/pt/sporttv5.php
19:45	Milan x Lecce | https://sportzonline.co/channels/hd/hd5.php
19:45	Milan x Lecce | https://sportzonline.co/channels/hd/hd7.php
19:45	Milan x Lecce | https://sportzonline.co/channels/pt/sporttv1.php
20:00	Sevilla x Levante | https://sportzonline.co/channels/hd/hd6.php
20:00	Olympique Marseille x Strasbourg | https://sportzonline.co/channels/hd/hd2.php
20:00	Olympique Marseille x Strasbourg | https://sportzonline.co/channels/hd/hd4.php
20:00	Philadelphia Union x New York RB | https://sportzonline.co/channels/hd/hd5.php
21:05   NFL: Baltimore Ravens @ Seattle Seahawks | https://sportzonline.co/channels/hd/hd2.php
01:00   Minnesota United x LA Galaxy | https://sportzonline.co/channels/pt/sporttv1.php
01:10   NFL: Philadelphia Eagles @ Dallas Cowboys | https://sportzonline.co/channels/hd/hd2.php

MONDAY
HD1 ENGLISH
HD2 ENGLISH
HD3 GERMAN
HD4 FRENCH
HD5 ENGLISH
HD7 ITALIAN
HD8 TURKISH

11:00   ICC World T20 Qualifier | https://sportzonline.co/channels/hd/hd1.php
13:00   ATP 500: Wien | https://sportzonline.co/channels/pt/sporttv5.php
18:00	Konyaspor x Yeni Malatyaspor | https://sportzonline.co/channels/hd/hd8.php
19:30	Arminia Bielefeld x Hamburger SV | https://sportzonline.co/channels/hd/hd5.php
19:30	Arminia Bielefeld x Hamburger SV | https://sportzonline.co/channels/hd/hd3.php
19:45	Lens x Auxerre | https://sportzonline.co/channels/hd/hd4.php
19:45	Brescia x Fiorentina | https://sportzonline.co/channels/hd/hd2.php
19:45	Brescia x Fiorentina | https://sportzonline.co/channels/hd/hd7.php
19:45	Brescia x Fiorentina | https://sportzonline.co/channels/pt/sporttv3.php
20:00	Sheffield United x Arsenal | https://sportzonline.co/channels/hd/hd1.php
20:00	Sheffield United x Arsenal | https://sportzonline.co/channels/pt/sporttv1.php
01:00   NFL: New England Patriots @ New York Giants | https://sportzonline.co/channels/hd/hd1.php
'''