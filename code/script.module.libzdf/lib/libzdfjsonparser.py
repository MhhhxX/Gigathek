# -*- coding: utf-8 -*-
import json
import libmediathek3 as libMediathek
import libzdftokengrabber

base = 'https://api.zdf.de'
playerId = 'ngplayer_2_3'
log = libMediathek.log

#headerMenu   = {'Api-Auth': 'Bearer '+tokenMenu}
#headerPlayer = {'Api-Auth': 'Bearer '+tokenPlayer}

def getU(url,Menu=False):
	try:
		header = getHeader(Menu)
		response = libMediathek.getUrl(url,header)
	except:
		(tokenMenu, tokenPlayer) = libzdftokengrabber.grepToken()
		header = getHeader(Menu, tokenMenu, tokenPlayer)
		response = libMediathek.getUrl(url,header)
	return response
	
def getHeader(Menu, tokenMenu = None, tokenPlayer = None):
	if Menu:
		header = { 'Api-Auth': 'Bearer ' + (tokenMenu if tokenMenu else libMediathek.f_open(libMediathek.pathUserdata('tokenMenu'))) }
	else:
		header = { 'Api-Auth': 'Bearer ' + (tokenPlayer if tokenPlayer else libMediathek.f_open(libMediathek.pathUserdata('tokenPlayer'))) }
	return header

def parsePage(url):
	if url.startswith('https://api.zdf.de/search/documents'):
		#response = libMediathek.getUrl(url,headerMenu)
		response = getU(url,True)
	else:
		#response = libMediathek.getUrl(url,headerMenu)
		response = getU(url,True)
	
	j = json.loads(response)
	libMediathek.log(response)
	if   j['profile'] == 'http://zdf.de/rels/search/result':
		return _parseSearch(j)
	elif j['profile'] == 'http://zdf.de/rels/search/result-page':
		return _parseSearchPage(j)
	elif j['profile'] == 'http://zdf.de/rels/content/page-index':
		return _parsePageIndex(j)
	elif j['profile'] == 'http://zdf.de/rels/content/page-index-teaser':
		return _parseTeaser(j)
	elif j['profile'] == 'http://zdf.de/rels/cmdm/resultpage-broadcasts':
		return _parseBroadcast(j)
	else:
		log('Unknown profile: ' + j['profile'])

def getAZ(url='https://api.zdf.de/content/documents/sendungen-100.json?profile=default'):
	#response = libMediathek.getUrl("https://api.zdf.de/content/documents/sendungen-100.json?profile=default",headerMenu)
	#response = getU("https://api.zdf.de/content/documents/sendungen-100.json?profile=default",True)
	response = getU(url,True)
	j = json.loads(response)
	letters = {}
	l = []
	for brand in j['brand']:
		if 'title' in brand:
			#l = []
			if 'teaser' in brand:
				for teaser in brand['teaser']:
					target = teaser['http://zdf.de/rels/target']
					d = _grepItem(target)
					if d:
						l.append(d)
	return l
	
def _parseSearch(j):
	l = []
	for module in j['module']:
		for result in module['filterRef']['resultsWithVideo']['http://zdf.de/rels/search/results']:
			target = result['http://zdf.de/rels/target']
			d = _grepItem(target)
			if d:
				d['_views'] = str(result['viewCount'])
				l.append(d)
	return l
			
def _parseSearchPage(j):
	l = []
	for result in j['http://zdf.de/rels/search/results']:
		target = result['http://zdf.de/rels/target']
		d = _grepItem(target)
		if d:
			l.append(d)
	return l
	
def _parsePageIndex(j):
	l = []
	for result in j['module'][0]['filterRef']['resultsWithVideo']['http://zdf.de/rels/search/results']:
		target = result['http://zdf.de/rels/target']
		d = _grepItem(target)
		if d:
			d['_views'] = str(result['viewCount'])
			l.append(d)
	return l
	
def _parseBroadcast(j):
	l = []
	for broadcast in j['http://zdf.de/rels/cmdm/broadcasts']:
		if 'http://zdf.de/rels/content/video-page-teaser' in broadcast:
			target = broadcast['http://zdf.de/rels/content/video-page-teaser']
			d = _grepItem(target)
			if d:
				#d['airedISO8601'] = broadcast['airtimeBegin']
				if broadcast['effectiveAirtimeBegin'] != None:#TODO: find alternative for videos without this field
					d['_airedISO8601'] = broadcast['effectiveAirtimeBegin']
				else:
					libMediathek.log('ommiting date: '+str(broadcast))
					libMediathek.log(str(broadcast['livestream']))
				d['_type'] = 'date'
				l.append(d)
	return l
def _grepItem(target):
	if target['profile'] == 'http://zdf.de/rels/not-found':
		return False
	if not ('contentType' in target): 
		return False
	d = {}
	d['_name'] = target['teaserHeadline']
	d['_plot'] = target['teasertext']
	d['_thumb'] = _chooseImage(target['teaserImageRef'])
	#d['url'] = base + target['http://zdf.de/rels/brand']['http://zdf.de/rels/target']['canonical']
	if target['contentType'] == 'brand' or target['contentType'] == 'category':
		try:
			#d['url'] = base + target['canonical']
			d['url'] = base + target['http://zdf.de/rels/search/page-video-counter-with-video']['self'].replace('&limit=0','&limit=100')
			d['_type'] = 'dir'
			d['mode'] = 'libZdfListPage'
		except: d = False
	elif target['contentType'] == 'clip':
		try:
			d['url'] = base + target['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd-template'].replace('{playerId}',playerId)
			if 'duration' in target['mainVideoContent']['http://zdf.de/rels/target']:
				d['_duration'] = str(target['mainVideoContent']['http://zdf.de/rels/target']['duration'])
			d['_type'] = 'clip'
			#d['_type'] = 'video'
			d['mode'] = 'libZdfPlay'
		except: d = False
	elif target['contentType'] == 'episode':# or target['contentType'] == 'clip':
		try:
			if not target['hasVideo']:
				return False
			#if target['mainVideoContent']['http://zdf.de/rels/target']['showCaption']:
			#	d['suburl'] = base + target['mainVideoContent']['http://zdf.de/rels/target']['captionUrl']
			if 'mainVideoContent' in target:
				content = target['mainVideoContent']['http://zdf.de/rels/target']
			elif 'mainContent' in target:
				content = target['mainContent'][0]['videoContent'][0]['http://zdf.de/rels/target']
				
			d['url'] = base + content['http://zdf.de/rels/streams/ptmd-template'].replace('{playerId}',playerId)
			if 'duration' in content:
				d['_duration'] = str(content['duration'])
			d['_type'] = 'video'
			d['mode'] = 'libZdfPlay'
		except: d = False
	else:
		log('Unknown target type: ' + target['contentType'])
		d = False
	return d
def _chooseImage(teaserImageRef,isVideo=False):
	if not isVideo:
		if 'layouts' in teaserImageRef:
			if '384xauto' in teaserImageRef['layouts']:
				return teaserImageRef['layouts']['384xauto']
			elif '1920x1080' in teaserImageRef['layouts']:
				return teaserImageRef['layouts']['1920x1080']
		
	return ''
	
def getVideoUrlById(id):
	url = base + '/content/documents/' + id + '.json?profile=player'
	response = getU(url,True)
	j = json.loads(response)
	#libMediathek.log(response)
	url = base + j['mainVideoContent']['http://zdf.de/rels/target']['http://zdf.de/rels/streams/ptmd-template'].replace('{playerId}',playerId)
	return getVideoUrl(url)
	
def getVideoUrl(url):
	d = {}
	d['media'] = []
	#response = libMediathek.getUrl(url,headerPlayer)
	response = getU(url,False)
	#libMediathek.log(response)
	j = json.loads(response)
	for caption in j.get('captions',[]):
		if caption['format'] == 'ebu-tt-d-basic-de':
			d['subtitle'] = [{'url':caption['uri'], 'type':'ttml', 'lang':'de', 'colour':True}]
		#elif caption['format'] == 'webvtt':
		#	d['subtitle'] = [{'url':caption['uri'], 'type':'webvtt', 'lang':'de', 'colour':False}]
	for item in j['priorityList']:
		if item['formitaeten'][0]['type'] == 'h264_aac_ts_http_m3u8_http':
			for quality in item['formitaeten'][0]['qualities']:
				if quality['quality'] == 'auto':
					d['media'].append({'url':quality['audio']['tracks'][0]['uri'], 'type': 'video', 'stream':'HLS'})
	return d