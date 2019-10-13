# -*- coding: utf-8 -*-

import urllib, urllib2
import re

from libs.tools import *



def main(item):
    itemlist = []

    data = urllib2.urlopen(urllib2.Request(item.url)).read()
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    logger (data)