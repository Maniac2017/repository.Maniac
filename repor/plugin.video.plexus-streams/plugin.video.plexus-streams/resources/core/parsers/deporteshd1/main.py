# -*- coding: utf-8 -*-

"""
This plugin is 3rd party and not part of plexus-streams addon

DHD1

"""
import sys,os,requests
current_dir = os.path.dirname(os.path.realpath(__file__))
basename = os.path.basename(current_dir)
core_dir =  current_dir.replace(basename,'').replace('parsers','')
sys.path.append(core_dir)
from utils.webutils import *
from utils.pluginxbmc import *
from utils.directoryhandle import *
import acestream as ace

parserName = "DeportesHD1"
base_url = "http://deporteshd1.blogspot.com/"

def module_tree(name,url,iconimage,mode,parser,parserfunction):
    if not parserfunction: deporteshd1_menu()
    elif parserfunction == "resolve_and_play": deporteshd1_streams(name,url)


def deporteshd1_menu():
    try:
        source = get_page_source(base_url)
    except:
        xbmcgui.Dialog().ok(translate(40000),translate(40128))
        return

    category = re.findall("<li data-role='dropdown'><a href='#'>(ACE[^<]*)</a><ul>(.+?)</ul>", source, re.MULTILINE | re.DOTALL)
    for categoryName, categoryLinks in category:

        linksMatch = re.findall("<li><a href='(.+?)'>(.+?)</a></li>", categoryLinks)
        if linksMatch:
            addLink("[B][COLOR orange]{0}[/COLOR][/B]".format(categoryName), '', os.path.join(current_dir,'icon.png'))
            for linkUrl, linkName in linksMatch:
                addDir("[B]{0}[/B]".format(linkName), linkUrl, 401, os.path.join(current_dir,"icon.png"), 1, False, parser=parserName, parserfunction="resolve_and_play")


def deporteshd1_streams(name, url):
    try:
        source = get_page_source(url)
    except: source="";xbmcgui.Dialog().ok(translate(40000),translate(40128))

    if source:
        aceHash = re.search('<a href="acestream://(.+?)">', source.replace('\n', ''))
        if aceHash:
            ace.acestreams(name, os.path.join(current_dir,'icon.png'), aceHash.group(1))
