#!/usr/bin/env python
# -*- coding: utf-8 -*-
from resources.lib.modules.addon import Addon
from resources.lib.modules import control,client,webutils,convert
import re,sys,os,urlparse,xbmcgui,xbmcplugin

addon = Addon('plugin.video.1x2', sys.argv)
addon_handle = int(sys.argv[1])

if not os.path.exists(control.dataPath):
    os.mkdir(control.dataPath)

AddonPath = addon.get_path()
IconPath = os.path.join(AddonPath, "resources/media/")
fanart = os.path.join(AddonPath + "/fanart.jpg")

# Proxy



def icon_path(filename):
    if 'http://' in filename:
        return filename
    return os.path.join(IconPath, filename)

class info():
    def __init__(self,ico=None):
        self.mode = '1x2'
        self.name = '1x2'
        if ico==None:
            self.icon = icon_path('logo.png')
        else:
            self.icon = icon_path(ico + '.png')
        self.categorized = False
        self.paginated = False
        self.multilink = True

class mylang():
    def __init__(self):
        zh = addon.get_string(30000)[0:8]
        self.spa = (zh == "Zona hor")

class main():
    def __init__(self):
        self.base = 'http://www.arenavision.us'
        self.headers = { "Cookie" : "beget=begetok; has_js=1;" }
        self.rslt = ''

    def links(self,url,tit):
        links = re.findall('(\d+.+?)\[(.+?)\]',url)
        links=self.__prepare_links(links,tit)
        return links

    def channels(self):
        result = client.request('http://www.arenavision.us/guide', headers=self.headers)
        result = result.replace('<tr></tr>','')
        result = result.replace('<tr></tr>','')
        result = result.replace('<br />\n',' ')
        result = result.replace('</tr><tr><td class="auto-style27" colspan="6">','')
        result = result.replace('<div id="1000233144"></div>','')
        result = result.replace('<script type="9b247a083b3ba8670323e9c1-text/javascript">','')
        result = result.replace('<!--//--><![CDATA[// ><!--','')
        result = result.replace('window.smrtSB=window.smrtSB||{sections:[]},window.smrtSB.sections.push({s:1000233144,w:728,h:90,c:3, blank: false,cross: true}),window.smrtSB.s||(window.smrtSB.s=document.createElement("script"),window.smrtSB.s.src="//imgpfx.arenavision.co.in/js/"+btoa(37*Math.round((899999*Math.random()+1e5)/37))+".js",window.smrtSB.s.async=!0,document.head.appendChild(window.smrtSB.s))','')
        result = result.replace('\t','')
        result = result.replace('</tr><td class="auto-style3"','</tr><tr><td class="auto-style3"')
        result = result.replace('\n<tr><td class="auto-style3"','</tr><tr><td class="auto-style3"')
        result = result.replace('\n</tr><td class="auto-style3" colspan="6"','</tr><tr><td class="auto-style3" colspan="6"')
        result = result.replace('</tr><tr><td class="auto-style4" colspan="6">','')
        result = result.replace('<tr><td class="auto-style14" colspan="6">Last update:','')
        result = result.replace('<span class="auto-style15"> 29/04/2019 07:30 CEST</span> UTC +1 (Paris, Madrid, Brusells)</td>','')
        result = result.replace('</tr><tr class="auto-style19"><td class="auto-style20" style="width: 129px">','</tr><tr><td class="auto-style27" style="width: 129px">')
        result = result.replace('</tr><tr><td class="auto-style27" style="width: 129px">','</tr><tr><td class="auto-style27" style="width: 129px">')
        result = result.replace('</tr><tr class="auto-style19"><td style="width: 129px" class="auto-style20">','</tr><tr><td class="auto-style27" style="width: 129px">')
        result = result.replace('</tr><tr><td class="auto-style10" colspan="6">Last update:<span class="auto-style15"> <span class="auto-style13">07/05/2019 15:00 CEST</span></span> UTC +1 (Paris, Madrid, Brusells)</td>','')




        table = client.parseDOM(result,'table',attrs={'style':'width: 100%'})[0]
        rows = client.parseDOM(table,'tr')

#       zx=''
#       for rw in rows:
#           zx+=rw
#           zx+='\n\n---------------------\n\n'
#       f = open('C:/Users/Teco/AppData/Roaming/Kodi/addons/plugin.video.1x2/zRow.txt','w+')
#       f.write(zx.encode('utf-8'))
#       f.close()

        events = self.__prepare_events(rows)
        return events


    @staticmethod
    def convert_time(time,date):
        li = time.split(':')
        li2 = date.split('/')
        hour,minute = li[0],li[1]
        day,month,year = li2[0],li2[1],li2[2]
        import datetime
        # --- Para intentar arreglar los errores de fecha de arenavisión
        hoy = datetime.date.today()
        if hoy.month != month:
            fech = datetime.date(int(year), int(month), int(day))
            diff = fech - hoy
            if abs(diff.days) > 10:
                month = hoy.month
        # ---
        from resources.lib.modules import pytzimp
        d = pytzimp.timezone(str(pytzimp.timezone('Europe/Ljubljana'))).localize(datetime.datetime(int(year), int(month), int(day), hour=int(hour), minute=int(minute)))
        timezona = control.setting('timezone_new')
        my_location = pytzimp.timezone(pytzimp.all_timezones[int(timezona)])
        convertido = d.astimezone(my_location)
        fm2 = "%H:%M"
        if mylang().spa:
            fmt = "%A, %d de %B de %Y"
            fch = convertido.strftime(fmt)
            hor = convertido.strftime(fm2)
            dict_py = os.path.join(addon.get_path().decode('utf-8'), 'dict_py')
            datos = open(dict_py).read()
            src = re.findall("eng:'(.*?)',spa:'(.*?)'",datos)
            for eng,spa in src:
                fch = fch.replace(eng,spa)
        else:
            fmt = "%A, %B %d, %Y"
            fch = convertido.strftime(fmt)
            hor = convertido.strftime(fm2)
        return hor,fch

    def __prepare_events(self,events):
        new = []
        events.pop(0)
        date_old = ''
        time = ''
        sport = ''
        competition = ''
        for event in events:
            items = client.parseDOM(event,'td')
            i = 0
            for item in items:
                if i==0:
                    date = item
                elif i==1:
                    time = item.replace('CEST','').strip()
                elif i==2:
                    sport = item
                elif i==3:
                    competition = item
                elif i==4:
                    event = webutils.remove_tags(item)
                elif i==5:
                    url = item
                i += 1

            try:
            #if time != '' and date !='' and 'Last update' not in date:
                time, date = self.convert_time(time,date)
            except:
                pass

            sport = '(%s - %s)'%(sport,competition)
            event = re.sub('\s+',' ',event)
            title = '[COLOR lime]%s[/COLOR]  [B]%s[/B]'%(time,convert.unescape(event))
            gra1 = addon.get_setting('gra1')
            gra2 = addon.get_setting('gra2')
            if gra1 in title:
                title = title.replace(gra1,gra2)
            data_py = os.path.join(addon.get_path().decode('utf-8'), 'data_py')
            f = open(data_py,'r')
            datos = f.read()
            f.close()
            src = re.findall("bus:'(.*?)',ico:'(.*?)',set:'(.*?)'",datos)

          # f = open('C:/Users/Teco/AppData/Roaming/Kodi/addons/plugin.video.1x2/ztab.txt','w+')
          # f.write(str(len(src)))
          # f.close()

            hay = False
            first = ''
            for bus,ico,stn in src:
                if first == '':
                    first = stn
                if addon.get_setting(stn)=='true':
                    hay = True
                    break
            if not hay:
                addon.set_setting(first,'true')
            for bus,ico,stn in src:
                if bus in sport and addon.get_setting(stn)=='true':
                    if date != date_old:
                        date_old = date
                        new.append(('x','[COLOR gold]%s[/COLOR]'%date, info().icon))
                    if mylang().spa:
                        if gra2 in title:
                            title = title.replace('[B]','[B][COLOR tomato]')
                            title = title.replace('[/B]','[/COLOR][/B]')
                            ico='GRANADA'
                        if title.find('SPAIN')!=-1:
                            title = title.replace('SPAIN','[COLOR red]ES[COLOR gold]PA[/COLOR]ÑA[/COLOR]'.decode('utf-8'))
                    title = title.encode('utf-8')
                    new.append((url,title,info(ico).icon))
                    break
        return new

    def __prepare_links(self,links,tit):
        new=[]
        spc=[]
        ace=[]
        tit = re.sub('\[.+?\]','',tit)
        tit = '[COLOR white]' + tit[7:].replace('-',' [B][COLOR red]vs[/B][/COLOR] ') + '[/COLOR]'
        ace.append(('x',tit,''))
        for link in links:
            lang = link[1]
            urls = link[0].split('-')
            for u in urls:
                title = '[COLOR red][B]Canal %s[/B][/COLOR] [%s]'%(u.replace(' ',''),lang)
                url = 'http://arenavision.cc/' + u.replace ('1','01').replace('2','02').replace('3','03').replace('4','04').replace('5','05').replace('6','06').replace('7','07').replace('8','08').replace('9','09').replace('010','10').replace('101','11').replace('102','12').replace('103','13').replace('104','14').replace('105','15').replace('106','16').replace('107','17').replace('108','18').replace('109','19').replace('020','20').replace('201','21').replace('202','22').replace('203','23').replace('204','24').replace('205','25').replace('206','26').replace('207','27').replace('208','28').replace('209','29').replace('030','30').replace('301','31').replace('302','32').replace('303','33').replace('304','34').replace('305','35').replace('306','36').replace('307','37').replace('308','38').replace('309','39').replace('040','40').replace('401','41').replace('402','42')
                if title.find('AV')==-1:
                    new.append((url,title,tit))
                else:
                    spc.append((url,title,tit))
        if new!=[]:
            ace.append(('x','[COLOR gold]1x2[/COLOR]',''))
        new = ace + new
        if spc!=[]:
            new.append(('x','[COLOR gold]1x2[/COLOR]',''))
        if spc!=[]:
            new = new + spc
        return new

    def resolve(self,url):
        data = client.request(url, headers=self.headers)
        url = re.findall('{format:"json",id:"([^"]+)"}', data, re.DOTALL)
        url = url[0]
        return 'plugin://program.plexus/?mode=1&url=acestream://%s&name=Video' %url

    def doit(self):
        for event in self.channels():
            addon.add_item({'mode': 'get_p2p_event', 'url': event[0],'site':info().mode , 'title':event[1], 'img': event[2]}, {'title': event[1]}, img=event[2], fanart=fanart,is_folder=True)

args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)

if mode is None:
    principal = main()
    principal.doit()
    addon.end_of_directory()

elif mode[0]=='get_p2p_event':
    url = args['url'][0]
    if url != 'x':
        title = args['title'][0]
        site = args['site'][0]
        img = args['img'][0]
        info = info()
        source = main()
        events = source.links(url,title)
        for event in events:
            addon.add_video_item({'mode':'play_p2p', 'url':event[0],'title':title,'title2':event[2],'img':img,'site':site}, {'title': event[1]}, img=img, fanart=fanart)
        addon.end_of_directory()

elif mode[0] == 'play_p2p':
    url = args['url'][0]
    title = args['title'][0]
    tit = args['title2'][0]
    img = args['img'][0]
    site = args['site'][0]
    source = main()
    resolved = source.resolve(url)
    li = xbmcgui.ListItem(title, path=resolved)
    li.setThumbnailImage(img)
    li.setLabel(title)
    li.setInfo('video', {'title': tit})
    handle = int(sys.argv[1])
    if handle > -1:
        xbmcplugin.endOfDirectory(handle, True, False, False)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
    li.setInfo('video', {'title': title})