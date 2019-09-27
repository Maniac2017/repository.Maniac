# -*- coding: utf-8 -*-

from libs.tools import *

def mainmenu(item):
    itemlist = list()

    itemlist.append(item.clone(
        #label='[COLOR FFB0C4DE]%s[/COLOR] [COLOR FFFAFAD2](En mantenimiento)[/COLOR]' % 'Canales ArenaVision',
        label= 'Canales ArenaVision',
        action='list_all_channels',
        #isFolder=False, # Para mantenimiento
        icon=os.path.join(image_path, 'arenavisionlogo1.png'),
        plot='Canales oficiales de Arenavision. Puedes escoger diferentes dominios desde el menu de ajustes.'
    ))

    itemlist.append(item.clone(
        label='Agenda de ArenaVision',
        action='get_agenda',
        agenda='arenavision',
        icon=os.path.join(image_path, 'arenavisionlogo1.png'),
        plot='Muestra la Agenda oficial de Arenavision.'
    ))

    itemlist.append(item.clone(
        label='Agenda Alternativa',
        action= 'get_agenda',
        agenda='alternativa',
        icon=os.path.join(image_path, 'live.png'),
        plot='Muestra una Agenda Alternativa para canales de Arenavision.'
    ))


    if get_EAS(item):
        itemlist.append(item.clone(
            label='Eventos Acestream Spanish',
            action='get_EAS',
            icon=os.path.join(image_path, 'acespa.png'),
            plot='Basada en el grupo de Telegram: https://t.me/acestream_spanish'
        ))

    itemlist.append(item.clone(
        label='Acestream ID',
        action='get_id',
        isPlayable=True,
        icon=os.path.join(image_path, 'id.png'),
        plot='Reproduce un video acestream introduciendo su ID manualmente.'
    ))

    return itemlist


def get_agenda(item):
    itemlist = list()

    guide = read_guide(item)

    if guide:
        if get_setting('get_categorias'):
            itemlist = show_categorias(item, guide)
        else:
            itemlist = show_agenda(item, guide)

    if not itemlist:
        xbmcgui.Dialog().ok('1x2',
                            'Ups!  Parece que en estos momentos no hay eventos programados.',
                            'Intentelo mas tarde, por favor.')

    return itemlist


def read_guide(item):
    guide = []

    if item.agenda == 'arenavision':
        guide = read_guide_arenavision()
    elif item.agenda == 'alternativa':
        guide = read_guide_alternativa()

    return guide


def download_arenavision(tipo='guide'):
    data = None
    url = get_setting('arena_url')

    response = httptools.downloadpage(url)

    respose_url = response.url[:-1] if response.url.endswith('/') else response.url
    if url != respose_url:
        url = respose_url
        set_setting('arena_url', url)

    data = response.data
    if not data:
        xbmcgui.Dialog().ok('1x2',
                            'Ups!  Parece que la página %s no funciona.' % url,
                            'Intentelo cambiando el dominio dentro de Ajustes.')

    elif tipo == 'guide':
        url_guide = re.findall('<a href="([^"]+)">EVENTS GUIDE', response.data)
        if url_guide:
            data = httptools.downloadpage(url + url_guide[0]).data
        else:
            data = None

    return data


def read_guide_arenavision():
    guide = []

    data = download_arenavision()
    if data:
        data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)

        patron = '<tr><td class="auto-style3">(\d+/\d+/\d+)</td><td class="auto-style3">(\d+:\d+) CEST</td><td class="auto-style3">(.*?)</td><td class="auto-style3">(.*?)</td><td class="auto-style3">(.*?)</td><td class="auto-style3">(.*?)</td></tr>'
        for fecha, hora, tipo, competicion, titulo, canales in re.findall(patron, data):
            channels = list()
            try:
                for canal_idioma in canales.split('<br />'):
                    canales, idioma = re.findall('(.*?)(\w{3})', canal_idioma, re.DOTALL)[0]
                    for num in re.findall('(\d+)', canales, re.DOTALL):
                        channels.append({'num': num, 'idioma': idioma})
            except:
                pass

            evento = Evento(fecha=fecha, hora=hora, formatTime='CEST', sport=tipo,
                   competition=competicion, title=titulo, channels=channels)

            if evento and (not evento.isFinished() or not get_setting('arena_hide')):
                guide.append(evento)

    return guide


def read_guide_alternativa():
    guide = []
    url = 'https://friendpaste.com/6wl4zDOlqmLJIEubSRSabr/raw'

    try:
        data = httptools.downloadpage(url, headers={'Accept': 'application/json'}).data
        data = load_json(base64.b64decode(data))

        for e in data:
            canales = list()
            idiomas = e.get('idiomas')

            for i, canal in enumerate(e.get('canales', [])):
                canales.append({'num': canal, 'idioma': idiomas[i]})

            evento = Evento(fecha=e['fecha'].replace('\\', ''), hora=e['hora'], formatTime='CEST', sport=e['deporte'],
                            competition=e['competicion'], title=e['titulo'], channels=canales)

            if evento and (not evento.isFinished() or not get_setting('arena_hide')):
                guide.append(evento)

    except:
        pass

    return guide


def show_categorias(item, guide):
    itemlist = []

    # Agrupar por deporte
    deporte_evento = dict()
    for e in guide:
        if e.sport.label not in deporte_evento:
            deporte_evento[e.sport.label] = [e]
        else:
            deporte_evento[e.sport.label].append(e)

    for deporte_label in sorted(deporte_evento.keys()):
        # Añadimos item deporte
        itemlist.append(item.clone(
            label= '%s (%s)' %(deporte_label, len(deporte_evento[deporte_label])),
            action='show_agenda',
            icon = deporte_evento[deporte_label][0].sport.icon,
            sport=deporte_label
        ))

        # Agrupar por competicion
        competiciones = dict()
        for e in deporte_evento[deporte_label]:
            if e.competition.label not in competiciones:
                competiciones[e.competition.label] = [e]
            else:
                competiciones[e.competition.label].append(e)

        # Añadimos item competicion
        for k in sorted(competiciones.keys()):
            evento = competiciones[k][0]
            itemlist.append(item.clone(
                label='    - %s (%s)' % (evento.competition.label, len(competiciones[k])),
                action='show_agenda',
                icon=evento.competition.icon if evento.competition.icon else evento.sport.icon,
                sport=deporte_label,
                competition=evento.competition.label
            ))

    if itemlist:
        itemlist.insert(0, item.clone(label='Ver todos los eventos', action='show_agenda'))
    else:
        itemlist = show_agenda(item,guide)

    return itemlist


def show_agenda(item, guide=None):
    itemlist = []

    if not guide:
        guide = read_guide(item)

    fechas = []
    for evento in guide:
        if item.sport and (item.sport != evento.sport.label or
                           (item.competition and item.competition != evento.competition.label)):
            continue

        if evento.fecha not in fechas:
            fechas.append(evento.fecha)
            label = '%s' % evento.fecha
            icon = os.path.join(image_path, 'logo.gif')

            if item.sport:
                label += '   %s' % evento.sport.label
                icon = evento.sport.icon
                if item.competition:
                    label += ' - %s' % evento.competition.label
                    icon = evento.competition.icon

            itemlist.append(item.clone(
                label= '[B][COLOR gold]%s[/COLOR][/B]' % label,
                icon= icon,
                action= None
            ))

        # fijar label
        label = "[COLOR red]%s[/COLOR]" % evento.hora
        if not item.competition:
            if not item.sport:
                label += ' (%s - %s)' % (evento.sport.label, evento.competition.label)
            else:
                label += ' (%s)' % evento.competition.label

        new_item = item.clone(
            title= evento.title,
            label= '%s %s' % (label, evento.title),
            icon= evento.get_icon(),
            action= ''

        )

        if evento.channels:
            new_item.channels = evento.channels
            new_item.action = 'list_channels'
            new_item.label +=  ' [%s]' % evento.idiomas
            new_item.label = new_item.label.replace('[COLOR red]','[COLOR lime]')

        itemlist.append(new_item)

    return itemlist


def list_channels(item):
    itemlist = list()

    data = download_arenavision('canales')
    url_canal = {'{:0>2}'.format(canal): url for url, canal in re.findall('<a href="([^"]+)">ArenaVision (\d+)</a>', data)}

    for c in item.channels:
        num = '{:0>2}'.format(c['num'])
        url = (get_setting('arena_url') + url_canal.get(num)) if url_canal.get(num) else None
        if url:
            itemlist.append(item.clone(
                label= 'Canal [COLOR red]%s[/COLOR] [COLOR lime][%s][/COLOR]' % (num, c['idioma']),
                action= 'play',
                isPlayable=True,
                url= url
            ))

    #return play(itemlist[0]) if len(itemlist) == 1 else itemlist
    return itemlist


def list_all_channels(item):
    itemlist = list()

    data = download_arenavision('canales')
    if data:
        url_canal = {'{:0>2}'.format(canal): url for url, canal in re.findall('<a href="([^"]+)">ArenaVision (\d+)</a>', data)}

        for n in range(1,49):
            n = '{:0>2}'.format(n)
            url = (get_setting('arena_url') + url_canal.get(n)) if url_canal.get(n) else None
            if url:
                itemlist.append(item.clone(
                    label= 'Canal [COLOR red]%s[/COLOR]' % n,
                    action= 'play',
                    isPlayable=True,
                    url= url))

    return itemlist


def get_EAS(item):
    itemlist = list()

    try:
        url = 'https://pastebin.com/raw/FrRi1dtc'

        for evento in load_json(httptools.downloadpage(url).data.replace("'", '"')):
            if datetime.datetime.fromtimestamp(time.time()) < date_to_local(evento['fecha'],evento['hora'],'CEST'):
                itemlist.append(item.clone(
                    label = evento['label'],
                    action = 'play',
                    isPlayable= True,
                    tipo_url = [[evento['tipo'], evento['url']]]
                ))
    except:
        pass

    return itemlist


def get_id(item):
    id = xbmcgui.Dialog().input('1x2 Introduzca la ID del video acestream')

    if id:
        id = re.findall('(^[a-z|0-9]{40}$)', id.replace('acestream://','').strip())
        if id:
            return {'action': 'play',
                   'url': id[0],
                   'titulo': item.label,
                   'VideoPlayer': 'plexus'}
        else:
            xbmcgui.Dialog().ok('1x2',
                                'Ups!  Parece que la ID introducida no es valida.')

    return None


def play(item):
    ret = None

    if not item.tipo_url:
        data = httptools.downloadpage(item.url).data
        item.tipo_url = re.findall('(id:|url=)"([^"]+)',data)
        item.label = 'Arenavision' + item.label

    if item.tipo_url:
        ret = {'action': 'play',
               'url': item.tipo_url[0][1],
               'titulo': item.label}

        if 'id' in item.tipo_url[0][0]:
            ret['VideoPlayer'] = 'plexus'

        elif 'url' in item.tipo_url[0][0]:
            ret['VideoPlayer'] = 'directo'

        return ret

    xbmcgui.Dialog().ok('1x2',
                        'Ups!  Parece que en estos momentos no hay nada que ver en este canal.',
                        'Intentelo mas tarde o pruebe en otro canal, por favor.')
    return None
