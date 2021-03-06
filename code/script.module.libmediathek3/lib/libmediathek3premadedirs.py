import urllib
import urllib2
import socket
import xbmc
import xbmcaddon
import xbmcvfs
import re
from datetime import date, timedelta

from libmediathek3utils import getTranslation as getTranslation


weekdayDict = { '0': getTranslation(31013),#Sonntag
				'1': getTranslation(31014),#Montag
				'2': getTranslation(31015),#Dienstag
				'3': getTranslation(31016),#Mittwoch
				'4': getTranslation(31017),#Donnerstag
				'5': getTranslation(31018),#Freitag
				'6': getTranslation(31019),#Samstag
			  }
	
def populateDirAZ(mode,ignore=[]):
	l = []
	if not '#' in ignore:
		d = {}
		d['mode'] = mode
		d['name'] = "#"
		d['_type'] = 'dir'
		l.append(d)
	letters = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
	for letter in letters:
		if not letter in ignore:
			d = {}
			d['mode'] = mode
			letter = letter.upper()
			d['name'] = letter
			d['_type'] = 'dir'
			l.append(d)
	return l
	
def populateDirDate(mode,channel=False,dateChooser=False):
	l = []
	
	d = {}
	day = date.today()
	d['mode'] = mode
	d['_type'] = 'dir'
	if channel: d['channel'] = channel
	d['_name'] = day.strftime('%d. %b | ') +  getTranslation(31020)
	d['datum'] = '0'
	d['yyyymmdd'] = day.strftime('%Y-%m-%d')
	l.append(d)
	
	d = {}
	day = day - timedelta(1)
	d['mode'] = mode
	d['_type'] = 'dir'
	if channel: d['channel'] = channel
	d['_name'] = day.strftime('%d. %b | ') +  getTranslation(31021)
	d['datum']  = '1'
	d['yyyymmdd'] = day.strftime('%Y-%m-%d')
	l.append(d)
	
	i = 2
	while i <= 6:
		d = {}
		day = day - timedelta(1)
		d['_name'] = day.strftime('%d. %b | ') + weekdayDict[day.strftime("%w")]
		d['datum']  = str(i)
		d['mode'] = mode
		d['_type'] = 'dir'
		if channel: d['channel'] = channel
		d['yyyymmdd'] = day.strftime('%Y-%m-%d')
		l.append(d)
		i += 1

	if dateChooser:
		d = {}
		d['mode'] = mode
		d['_type'] = 'dir'
		if channel: d['channel'] = channel
		d['name'] = getTranslation(31022)
		l.append(d)
		
	return l
	
