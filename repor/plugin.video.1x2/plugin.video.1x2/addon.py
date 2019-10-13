# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from libs.tools import *


def mainmenu(item):
    itemlist = list()

    itemlist.append(item.clone(
        label='Acestreams',
        channel='acestreams',
        action='mainmenu',
        icon=os.path.join(image_path, 'acestre.png')
    ))

    itemlist.append(item.clone(
        #label='S365',
        label='[COLOR FFB0C4DE]%s[/COLOR] [COLOR FFFAFAD2](En mantenimiento)[/COLOR]' % 'S365',
        channel='s365',
        #action='mainmenu',
        action='mantenimiento',
        isFolder=False, # Para mantenimiento
        icon=os.path.join(image_path, 'mantenimiento.png')
    ))


    itemlist.append(item.clone(
        label='Canales 24',
        channel='canales24',
        action='list_all_channels',
        icon=os.path.join(image_path, 'sports_icon.png')
    ))


    itemlist.append(item.clone(
        label='SportsTube',
        channel='pastube',
        action='main',
        url='https://pastebin.com/raw/bR2UkLvN',
        icon=os.path.join(image_path, 'pastu.png')
    ))


    itemlist.append(item.clone(
        label='Buscar Actualizaciones',
        action='forceUpdate',
        icon=os.path.join(image_path, 'update.png'),
        plot="Version actual: %s\nHaz click para buscar nuevas actualizaciones." % xbmcaddon.Addon().getAddonInfo('version')
    ))


    itemlist.append(item.clone(
        label='Ajustes',
        action='open_settings',
        plot='Menu de configuración'
    ))

    # test
    if os.path.isfile(os.path.join(runtime_path, 'test.py')):
        itemlist.append(item.clone(
            label='Test',
            channel='test',
            action='mainmenu',
        ))


    return itemlist


def run(item):
    logger('run item: %s' % item, 'info')
    itemlist = list()
    channel = None

    if not item.action:
        logger("Item sin acción")
        return

    if item.channel and os.path.isfile(os.path.join(runtime_path, item.channel + '.py')):
        try:
            if item.channel in sys.modules:
                reload(sys.modules[item.channel])
            channel = __import__(item.channel, None, None, [item.channel])
        except:
            channel = None

    if hasattr(channel, item.action):
        result = getattr(channel, item.action)(item)
        if isinstance(result,list):
            itemlist = result
        elif isinstance(result, dict):
            if result['action'] == 'refresh':
                xbmc.executebuiltin("Container.Refresh")

            elif result['action'] == 'play':
                play(result)
                return
    else:
        if item.action == 'play':
            play({'VideoPlayer':'directo',
                  'url': item.url,
                  'titulo': item.title or item.label})
            return

        elif item.action == 'mainmenu':
            itemlist = mainmenu(item)

        elif item.action == 'open_settings':
            xbmcaddon.Addon(id=sys.argv[0][9:-1]).openSettings()

        elif item.action == 'forceUpdate':
                xbmc.executebuiltin('UpdateAddonRepos()')
                xbmc.executebuiltin('UpdateLocalAddons()')
                xbmcgui.Dialog().notification('1x2', "Salga del addon para aplicar la actualizacion.")

        elif item.action == 'mantenimiento':
            xbmcgui.Dialog().ok('1x2 En mantenimiento',
                                'Ups!  Esta sección no esta operativa.',
                                'Estamos trabajando para encontrar una solución.',
                                'Disculpen las molestias.')

    if itemlist:
        for item in itemlist:
            #logger(item)
            listitem = xbmcgui.ListItem(item.label or item.title)
            listitem.setInfo('video', {'title': item.label or item.title, 'mediatype': 'video'})
            if item.plot:
                listitem.setInfo('video', {'plot': item.plot})
            for n,v in item.getart():
                listitem.setArt({n: v})

            if item.isPlayable:
                listitem.setProperty('IsPlayable', 'true')
                isFolder = False

            elif isinstance(item.isFolder, bool):
                isFolder = item.isFolder

            elif not item.action:
                isFolder = False

            else:
                isFolder = True

            xbmcplugin.addDirectoryItem(
                handle=int(sys.argv[1]),
                url='%s?%s' % (sys.argv[0], item.tourl()),
                listitem=listitem,
                isFolder= isFolder,
                totalItems=len(itemlist)
            )

        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)


def play(video_item):
    logger(video_item)

    if video_item['VideoPlayer'].lower() == 'directo':
        listitem = xbmcgui.ListItem()
        listitem.setInfo('video', {'title': video_item['titulo']})
        listitem.setProperty('IsPlayable', 'true')
        listitem.setPath(video_item['url'])
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
        return

    elif video_item['VideoPlayer'] == 'plexus':
        url = 'plugin://program.plexus/?mode=1&url=acestream://%s&name=%s' % \
              (video_item['url'], video_item['titulo'])

        if video_item.get('iconImage'):
            url += '&iconimage=' + video_item.get('iconImage')

    elif video_item['VideoPlayer'] == 'f4mtester':
        url = 'plugin://plugin.video.f4mTester/?streamtype=HLSRETRY&url=%s&name=%s' % \
              (urllib.quote_plus(video_item['url']), urllib.quote_plus(video_item['titulo']))

        if video_item.get('callbackpath'):
            url += '&callbackpath=%s&callbackparam=%s' %(video_item['callbackpath'],video_item.get('callbackparam', ''))

        if video_item.get('iconImage'):
            url += '&iconImage=' + video_item.get('iconImage')

    elif video_item['VideoPlayer'] == 'youtube':
        url = 'plugin://plugin.video.youtube/%s' % video_item['url']


    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=False)
    xbmc.executebuiltin('Dialog.Close(all,true)')
    if url:
        xbmc.executebuiltin('RunPlugin(' + url + ')')






if __name__ == '__main__':
    if sys.argv[2]:
        item = Item().fromurl(sys.argv[2])
    else:
        # Comprobar F4Proxy
        F4mProxy_path = xbmc.translatePath(xbmcaddon.Addon('script.video.F4mProxy').getAddonInfo('Path'))
        F4mProxy_path = os.path.join(F4mProxy_path, 'lib', 'HLSDownloaderRetry.py')
        if os.path.isfile(F4mProxy_path):
            import hashlib
            hash = hashlib.md5(open(F4mProxy_path, 'rb').read()).hexdigest()

            if hash != '1d3f071bce0b59079bb86c9d3cc8b7b4':
                logger(hash)
                if xbmcgui.Dialog().yesno('1x2',
                                          'Para poder disfrutar de todo el contenido de sport365',
                                          ' es necesario instalar un MOD en F4mProxy',
                                          '¿Desea que lo instalemos ahora?'):
                    try:
                        import shutil
                        shutil.copy(os.path.join(runtime_path, 'resources', 'HLSDownloaderRetry.py'),F4mProxy_path)
                        msg = 'MOD F4mProxy instalado correctamente.'
                        icon = xbmcgui.NOTIFICATION_INFO
                    except:
                        msg = 'No se ha podido copiar el MOD F4mProxy'
                        icon =   xbmcgui.NOTIFICATION_ERROR

                    xbmcgui.Dialog().notification('1x2', msg, icon)

        else:
            xbmcgui.Dialog().ok('1x2',
                                'Ups! Para poder utilizar el canal sport365 es necesario tener instalado F4mTester.')

        item = Item(action='mainmenu', icon=os.path.join(image_path, 'red_config.png'))

    run(item)



