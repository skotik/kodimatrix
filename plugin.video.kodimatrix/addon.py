# encoding: utf-8
from xbmcswift2 import Plugin, CLI_MODE, xbmcgui
import re, urllib2, urllib

plugin = Plugin()

if CLI_MODE:
	import codecs, sys
	outf = codecs.getwriter('cp866')(sys.stdout, errors='replace')
	sys.stdout = outf


STRINGS = {
    'search': 33005,
	'prev'  : 33001,
	'next'  : 33002,
	'prompt'  : 33003,
	'agent_only'  : 33004,
}

BadType='exe pdf 7z rar mp3 iso other ac3 wav doc txt'
plugin.
#/import parser
@plugin.cached(TTL=10)
def ParsePage(page):
	links = []
	opener = urllib2.build_opener()
	s_url='http://matrixportal.ru/cat/films/default.htm?page='+page+'&sort=2'
	resp=opener.open(s_url, None, 30)
	s_resp=resp.read()
	s_resp=s_resp.decode('cp1251','replace')
	mPubs=re.findall(ur'<td class="pub".*?>(.*?)</td>', s_resp, re.DOTALL)
	fIconInTree=plugin.get_setting('IconInTree', bool)
	fThumInTree=plugin.get_setting('ThumInTree', bool)
	for cPub in mPubs:
		info={}
		info_icon=None
		info_thum=None
		cPubHTML=cPub
		label_format=''
		cType=''
		m_title=re.search(ur'<div class="title">(.*?)(?:<div class="sub-title">(.*?)){0,1}</div>',cPubHTML,re.S)
		if m_title is not None:
			info['title']=m_title.group(1)
			info['originaltitle']=m_title.group(2)
			m_season=re.search(ur'(.*?) \((\d+) сезон\)',info['title'],re.S)
			if m_season is not None:
				info['season']=int(m_season.group(2))
				info['tvshowtitle']=m_season.group(1)

		m_genre=re.search(ur'<div class="block">Жанр: (.*?)</div>',cPubHTML,re.S)
		if m_genre is not None:
			info['genre']=m_genre.group(1)
		m_plotoutline=re.search(ur'<div>Последняя:.*?<div class="block">(.*?)</div>',cPubHTML,re.S)
		if m_plotoutline is not None:
			info['plotoutline']=m_plotoutline.group(1)
		m_year=re.search(ur'<div class="subtitle">(\d+).*?</div>',cPubHTML,re.S)
		if m_year is not None:
			info['year']=int(m_year.group(1))
		m_rating=re.search(ur'<span class="user-rating">([\d\.]+).*?</span>',cPubHTML,re.S)
		if m_rating is not None:
			info['rating']=float(m_rating.group(1))

		m_link=re.search(ur'<a href="/pub/(\d+)/\?" title="(.*?)" class="title">', cPubHTML, re.S)
		if m_link is not None:
			if fIconInTree:
				info_icon='http://matrixportal.ru/covers/'+m_link.group(1)+'_3.jpg'
			if fThumInTree:
				info_thum='http://matrixportal.ru/covers/'+m_link.group(1)+'_2.jpg'
			links.append({
				'icon'      : info_icon,
				'thumbnail' : info_thum,
				'label'     : m_link.group(2), 
				'path'      : plugin.url_for('show_videos', id=m_link.group(1))
			})		

#	pattern=ur'<a href="/pub/(\d+)/\?" title="(.*?)" class="title">'
#	m=re.findall(pattern, s_resp, re.S)
#	for link in m:
#		links.append({'label':link[1], 'path':plugin.url_for('show_videos', id=link[0])})
	return links

@plugin.cached(TTL=10)
def ParseSearchPage(page,query):
	links = []
	opener = urllib2.build_opener()
#	query = query.decode('utf_8').encode('cp1251')
	fTypeInTree=plugin.get_setting('TypeInTree', bool)
	s_url='http://matrixportal.ru/search/default.htm?page='+page+'&sort=2&q='+urllib.quote_plus(query)
	resp=opener.open(s_url, None, 30)
	s_resp=resp.read()
	s_resp=s_resp.decode('cp1251','replace')
	mPubs=re.findall(ur'<td class="pub".*?>(.*?)</td>', s_resp, re.DOTALL)
	for cPub in mPubs:
		fVideo=True
		cPubHTML=cPub
		label_format=''
		cType=''
		mType=re.search(ur'<div class="afisha">.*?src="/images/ct/(.+?)\.png".*?</div>', cPubHTML, re.DOTALL )
		if mType is not None:
			cType=mType.group(1)
			if cType in BadType:
				fVideo=False

		mType=re.search(ur'<div class="afisha">.*?src="/images/view-video-online.png".*?</div>', cPubHTML, re.DOTALL )
		if mType is not None:
			fVideo=False

		if fVideo:
			label_format = ' ('+cType+')' if fTypeInTree else '' 
			pattern=ur'<a href="/pub/(\d+)/\?" title="(.*?)" class="title">'
			m=re.findall(pattern, cPubHTML, re.S)
			for link in m:
				links.append({'label':link[1]+label_format, 'path':plugin.url_for('show_videos', id=link[0])})
	
	m=re.search('<form method="get" class="pager" xmlns="">',s_resp, re.S)
	if m is not None:
		m=re.search('var page = 1;.*?itemsCount = (\d+);.*?itemsOnPage = (\d+);.*?page = (\d+);',s_resp, re.S)
		sp_itemsCount=int(m.group(1))
		sp_itemsOnPage=int(m.group(2))
		sp_page=int(m.group(3))
		if sp_page > 1:
			links.insert(0, {
				'label': _('prev'),
				'path': plugin.url_for('search', query=query, page=str(sp_page - 1))
			})
		if sp_page*sp_itemsOnPage < sp_itemsCount:
			links.append( {
				'label': _('next'),
				'path': plugin.url_for('search', query=query, page=str(sp_page + 1))
			})

#	links.insert(0, {
#			'label': _('search'),
#			'path': plugin.url_for('search', query='', page='1')
#		})

	return links


def multiparse(outreg,inreg,text):
	result = []
	m_out=re.search(outreg,text,re.S)
	if m_out is not None:
		m_in=re.findall(inreg,m_out.group(1),re.S)
		for sFind in m_in:
			result.append(sFind)
	return result


@plugin.cached(TTL=10)
def ParseVideo(vid):
	links = []
	info = {}
	opener = urllib2.build_opener()
	s_url='http://matrixportal.ru/pub/'+vid+'/default.htm'
	resp=opener.open(s_url, None, 30)
	s_resp=resp.read()
	s_resp=s_resp.decode('cp1251','replace')
	fTitleInTree=plugin.get_setting('TitleInTree', bool);
	fTitleInLink=plugin.get_setting('TitleInLink', bool);
	label_title=''
	path_title=''
	s_title=''
#	if (fTitleInTree | fTitleInLink):
	m_title=re.search(ur'<h2 class="cat-name" xmlns="">(.*?)</h2>',s_resp,re.S)
	if m_title is not None:
		s_title=m_title.group(1)
		lTitle=s_title.split(' / ',1)
		info['title']=lTitle[0]
		if len(lTitle)==2:
			info['originaltitle']=lTitle[1]
		m_season=re.search(ur'(.*?) \((\d+) сезон\)',s_title,re.S)
		if m_season is not None:
			info['season']=int(m_season.group(2))
			info['tvshowtitle']=m_season.group(1)
	m_plot=re.search(ur'title="Рейтинг" /></td></tr></table></td></tr></table><br xmlns="" />(.*?)<br xmlns="" />',s_resp,re.S)
	if m_plot is not None:
		info['plot']=m_plot.group(1).replace('<br xmlns="" xmlns:matrix="urn:matrix-scripts" />','[CR]')

	if (fTitleInTree):
		label_title=' / '+s_title
	if (fTitleInLink):
		path_title=s_title+'_'

	m_year=re.search(ur'<b>Год</b></td><td>(\d+)</td>',s_resp,re.S)
	if m_year is not None:
		info['year']=m_year.group(1)
	info['director']=' '.join(multiparse(ur'<td><b>Режиссер</b></td><td>(.*?)</td>',ur'<a.*?>(.*?)</a>',s_resp))
	info['cast']=multiparse(ur'<td><b>Актёры</b></td><td>(.*?)</td>',ur'<a.*?><nobr>(.*?)</nobr></a>',s_resp)
	info['genre']=' '.join(multiparse(ur'<td><b>Жанр</b></td><td>(.*?)</td>',ur'<a.*?>(.*?)</a>',s_resp))
	info['artist']=info['cast']
#	print repr(info['cast'])
	pattern=ur'<a href="/files/(\d+)/d" title="Скачать">(.*?)</a>'
	
	m=re.findall(pattern, s_resp, re.S)


	for link in m:
		if (link[1][0]!='<'):
			m_episode=re.search(ur'^(\d+) серия',link[1],re.S)
			if m_episode is not None:
				info['episode']=int(m_episode.group(1))
			info['count']=int(link[0])
			links.append({
				'label' :link[1]+label_title, 
				'label2':s_title,
				'path': plugin.url_for('playvideo', vid=str(link[0])),
				'info': info,
				'is_playable': True})
	return links


#@plugin.route('/playvideo/<vid>/<filename>')
@plugin.cached_route('/playvideo/<vid>',TTL=10)
def playvideo(vid):
	s_url='http://matrixportal.ru/clientdownload.htm?fileid='+vid
	opener = urllib2.build_opener()
	resp=opener.open(s_url, None, 30)
	s_resp=resp.read()
	s_resp=s_resp.decode('cp1251','replace')
	mBrowser=re.search(ur'<a class="download-button" id="button_2" href="/files/\d+/web/(.*?)"><script>.*?</script>загрузить файл через браузер</a>',s_resp,re.S)
	if mBrowser is None:
		if CLI_MODE:
			return []
		else:
			xbmcgui.Dialog().ok('KodiMatrix',_('agent_only'))
			plugin.set_resolved_url()
	else:
		if CLI_MODE:
			return []
		else:
			plugin.set_resolved_url('http://matrixportal.ru/files/'+vid+'/web/'+mBrowser.group(1))


@plugin.route('/clearcache')
def clearcache():
	plugin.clear_function_cache();
#	plugin.sync()



@plugin.route('/', name='show_matrix_firstpage', options={'page': '1'})
@plugin.route('/page/<page>')
def index(page):
	items = []
	items = list(ParsePage(page))
	page = int(page)

	items.append( {
		'label': _('next'),
		'path': plugin.url_for('index', page=str(page + 1))
	})

	if page > 1:
		items.insert(0, {
			'label': _('prev'),
			'path': plugin.url_for('index', page=str(page - 1))
		})
	if True:
		items.insert(0, {
			'label': _('search'),
			'path': plugin.url_for('search', query='', page='1')
		})

	return plugin.finish(items, update_listing=True)
	pass

@plugin.route('/video/<id>')
def show_videos(id):
	items = list(ParseVideo(id))
#	return plugin.finish(items)
	return items
	pass

@plugin.route('/search/<page>/', name='show_search', options={'query': '', 'page': '1'})
@plugin.route('/search/<page>/<query>')
def search(page,query):
	items = []
	if len(query)<4:
		query = plugin.keyboard(heading=_('prompt'))
		if query is not None and len(query)>1:
			query=query.decode('utf_8').encode('cp1251')
		else:
			return None
		if CLI_MODE: 
			query = query.decode('cp866','replace')#.encode('cp1251')
		page = '1'
#	else:
#		print 'repr '+repr(query)
#		query=query.encode('latin')
	items = list(ParseSearchPage(page,query))

#	items.insert(0, {
#		'label': '..',
#		'path': plugin.url_for('index', page='1')
#	})


	return plugin.finish(items, update_listing=True)
	pass


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id]).encode('utf-8')
    else:
        log('String is missing: %s' % string_id)
        return string_id

def translit(name):
	slovar = {
	  u'а':'a' ,u'б':'b' ,u'в':'v' ,u'г':'g'  ,u'д':'d',u'е':'e',u'ё':'e',
      u'ж':'zh',u'з':'z' ,u'и':'i' ,u'й':'i'  ,u'к':'k',u'л':'l',u'м':'m',u'н':'n',
      u'о':'o' ,u'п':'p' ,u'р':'r' ,u'с':'s'  ,u'т':'t',u'у':'u',u'ф':'f',u'х':'h',
      u'ц':'c' ,u'ч':'cz',u'ш':'sh',u'щ':'scz',u'ъ':'' ,u'ы':'y',u'ь':'' ,u'э':'e',
      u'ю':'u' ,u'я':'ja',u'А':'a' ,u'Б':'b'  ,u'В':'v',u'Г':'g',u'Д':'d',u'Е':'e', u'Ё':'e',
      u'Ж':'zh',u'З':'z' ,u'И':'i' ,u'Й':'i'  ,u'К':'k',u'Л':'l',u'М':'m',u'Н':'n',
      u'О':'o' ,u'П':'p' ,u'Р':'r' ,u'С':'s'  ,u'Т':'t',u'У':'u',u'Ф':'f',u'х':'h',
      u'Ц':'c' ,u'Ч':'cz',u'Ш':'sh',u'Щ':'scz',u'Ъ':'' ,u'Ы':'y',u'Ь':'' ,u'Э':'e',
      u'Ю':'u' ,u'Я':'ja',u',':''  ,u'?':''   ,u' ':'_',u'~':'' ,u'!':'' ,u'@':''   ,u'#':'',
      u'$':''  ,u'%':''  ,u'^':''  ,u'&':''   ,u'*':'' ,u'(':'' ,u')':'' ,u'-':''   ,u'=':'', u'+':'',
      u':':''  ,u';':''  ,u'<':''  ,u'>':''   ,u'\'':'',u'"':'' ,u'\\':' ',u'/':''  ,u'№':'',
      u'[':''  ,u']':''  ,u'{':''  ,u'}':''}
#	print repr(name)
	for key in slovar:
		name = name.replace(key, slovar[key])
	return name




if __name__ == '__main__':
    plugin.run()

