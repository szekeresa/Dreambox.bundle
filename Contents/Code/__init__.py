ART = 'art-default.jpg'
ICON = 'icon-default.png'
ZAP_TO_URL = 'http://%s:%s/web/zap?sRef=%s'
STREAM_URL = 'http://%s:%s/%s'
EPG_URL = 'http://%s:%s/web/epgnow?bRef=%s'

####################################################################################################
def Start():

	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = 'Dreambox'
	DirectoryObject.thumb = R(ICON)

####################################################################################################
@handler('/video/dreambox', 'Dreambox', art=ART, thumb=ICON)
def MainMenu():

        oc = ObjectContainer(view_group='List', no_cache=True)

        if Prefs['host'] and Prefs['port_web'] and Prefs['port_video']:
                url = 'http://{}:{}/web/getservices'.format(Prefs['host'], Prefs['port_web'] )
                try:
                        urlHtml = HTML.ElementFromURL(url)
                except:
                        Log("Couldn't connect to Dreambox.") 
                        return None     
                ServiceReference = urlHtml.xpath("//e2servicereference/text()")
                ServiceName = urlHtml.xpath("//e2servicename/text()")
                for item in xrange(len(ServiceReference)):
					oc.add(DirectoryObject(key = Callback(BouquetsMenu, sender = ServiceName[item], index=ServiceReference[item], name=ServiceName[item]),title = ServiceName[item]))
        oc.add(PrefsObject(title='Preferences', thumb=R('icon-prefs.png')))      
        return oc


@route("/video/dreambox/BouquetsMenu/{name}")
def BouquetsMenu(sender, index, name):
	
	#Getting Channels and EPG
	url = EPG_URL % (Prefs['host'], Prefs['port_web'], String.Quote(index))
	Log(url)
	try:
		urlHtml = HTML.ElementFromURL(url)
	except:
		Log("Couldn't get channels and EPG.") 
	events = urlHtml.xpath("//e2event")
	ChannelReference = list()
	ChannelName = list()
	epgdescription = list()
	epgduration = list()
	# Should be able to get now and next here
	# I'll refactor this out
	for event in events:
		tempChannelReference = ''
		tempChannelName = ''
		if len(event.xpath("./e2eventservicereference/text()"))>0:
			tempChannelReference = event.xpath("./e2eventservicereference/text()")[0]
		if len(event.xpath("./e2eventservicename/text()"))>0:
			tempChannelName = event.xpath("./e2eventservicename/text()")[0]
		if Prefs['epg']:
			temptitle = ''
			tempdescription = ''
			tempdescriptionext = ''
			tempcurrenttime = ''
			tempstart = ''
			tempduration = ''
			if len(event.xpath("./e2eventtitle/text()"))>0:
				temptitle = event.xpath("./e2eventtitle/text()")[0]
			if len(event.xpath("./e2eventdescription/text()"))>0:
				tempdescription = event.xpath("./e2eventdescription/text()")[0]
			if len(event.xpath("./e2eventdescriptionextended/text()"))>0:
				tempdescriptionext = event.xpath("./e2eventdescriptionextended/text()")[0]
			if len(event.xpath("./e2eventcurrenttime/text()"))>0:
				tempcurrenttime = event.xpath("./e2eventcurrenttime/text()")[0]
			if len(event.xpath("./e2eventstart/text()"))>0:
				tempstart = event.xpath("./e2eventstart/text()")[0]
			if len(event.xpath("./e2eventduration/text()"))>0:
				tempduration = event.xpath("./e2eventduration/text()")[0]
			if temptitle == 'None':
				temptitle = ''
			if tempstart == 'None':
				tempstart = ''
			if tempdescription == 'None':
				tempdescription = ''
			if tempdescriptionext == 'None':
				tempdescriptionext = ''
			if tempduration == 'None':
				tempduration = ''
			if not temptitle == '':
				tempChannelName = tempChannelName+' ('+temptitle+')'
			if not tempstart == '':
				tempChannelName = tempChannelName+' +'+str((int(tempcurrenttime)-int(tempstart))//60)
			if not tempdescriptionext == '':
				tempdescription = tempdescription + '\n\n' + tempdescriptionext
			epgdescription.append(tempdescription)
			if not tempduration == '':
				epgduration.append(tempduration)
			else:
				epgduration.append('0')	
		else:
			epgdescription.append('')
			epgduration.append('0')
		ChannelReference.append(tempChannelReference)
		ChannelName.append(tempChannelName)
	Log('ChannelReference='+str(len(ChannelReference)))
	Log('ChannelName='+str(len(ChannelName)))
	Log('epgdescription='+str(len(epgdescription)))
	Log('epgduration='+str(len(epgduration)))
		
	oc = ObjectContainer(title2=name, view_group='List', no_cache=True)

	for item in xrange(len(ChannelReference)):
		oc.add(TvStationMenu(sender=ChannelName[item], channel=ChannelReference[item], epgdescription=epgdescription[item], epgduration=epgduration[item]))

	return oc

##11111##################################################################################################
@route("/video/dreambox/TvStationMenu")
def TvStationMenu(sender, channel, epgdescription, epgduration, thumb=R(ICON), include_oc=False):
    browsers = ('Chrome', 'Internet Explorer', 'Opera', 'Safari', 'iOS')
    video_codec = 'h264'
    audio_codec = 'mp3'
    container = 'mp4'
    if Prefs['picon']:
		piconfile = channel.replace(':', '_')
		piconfile = piconfile.rstrip('_')
		piconfile = piconfile + '.png'
		if piconfile:
			Log('Piconfile: '+sender+ ' - ' + piconfile)
			thumb=R(piconfile)
    # Set default container for MP4 to work on Samsung.. and others???
	# Just filters against browser name (Better way to do this ? Check the caps of the connected device?)
    if (Client.Platform  in browsers ):
        container = 'mpegts'
    video = VideoClipObject(
		key = Callback(TvStationMenu, sender=sender, channel=channel, epgdescription=epgdescription, epgduration=epgduration, thumb=thumb, include_oc=True),
		rating_key = channel,
		title = sender,
		summary = epgdescription,
		duration = int(epgduration)*1000,
		thumb = thumb,
		items = [
			MediaObject(
				container = container,
				video_codec = video_codec,
				audio_codec = audio_codec,
				audio_channels = 2,
				parts = [PartObject(key=Callback(PlayVideo, channel=channel))]
			)
		]
	)
    if include_oc:
        oc = ObjectContainer()
        oc.add(video)
        return oc
    return video


####################################################################################################
@route("video/dreambox/PlayVideo/{channel}")
def PlayVideo(channel):


        
	channel = channel.strip('.m3u8')
	Log('channel variable='+channel)
	if Prefs['zap']:
		#Zap to channel
		url = ZAP_TO_URL % (Prefs['host'], Prefs['port_web'], String.Quote(channel))
		try:
			urlHtml = HTTP.Request(url, cacheTime=0, sleep=2.0).content
			Log('url HTML = {}'.format(urlHtml))
		except:
			Log("Couldn't zap to channel.")
	stream = STREAM_URL % (Prefs['host'], Prefs['port_video'], channel)
	Log('stream is {}'.format(stream))
	return Redirect(stream)
