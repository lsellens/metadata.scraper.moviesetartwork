import xbmc
import xbmcaddon
import xbmcgui
import urllib.request
import urllib.parse
import json

# get settings and paths
__addon__ = xbmcaddon.Addon(id='metadata.scraper.moviesetartwork')
__addonid__ = __addon__.getAddonInfo('id')
__icon__ = __addon__.getAddonInfo('icon')
poster_size = (__addon__.getSetting('poster_size'))
fanart_size = (__addon__.getSetting('fanart_size'))
api_key = '337431b553474aa71c9274d439a58d49'
tmdb_url = 'https://api.themoviedb.org/3/'
tmdb_config = json.load(urllib.request.urlopen('{0}configuration?api_key={1}'.format(tmdb_url, api_key)))
done = {}
# Ugly hack so script can't be run while running
xbmcgui.Window(10000).setProperty(__addonid__ + '.running', 'True')


def jsonrpc(method, *args):
    values = {"jsonrpc": "2.0", "id": "1", "method": method}
    if args:
        values["params"] = args
    json_cmd = json.dumps(values, sort_keys=True, separators=(',', ':'))
    json_cmd = json_cmd.replace('[{', '{')
    json_cmd = json_cmd.replace('}]', '}')
    return json_cmd


def searchset(setid, setname):
    encoded_setname = urllib.parse.quote(setname)
    xbmc.log('Searching for artwork for set: {}'.format(setname), level=xbmc.LOGDEBUG)
    headers = urllib.request.urlopen(
        '{0}search/collection?api_key={2}&language=en-US&query={1}&page=1'.format(tmdb_url, encoded_setname, api_key))
    data = json.load(headers)
    xbmc.log('Received data from TMDB API: {}'.format(data), level=xbmc.LOGDEBUG)
    if not data['results']:
        xbmc.log('No results found for set: {}'.format(setname), level=xbmc.LOGERROR)
        return
    for name in data['results']:
        if name['name'] == setname:
            try:
                parameters = {'setid': setid, 'properties': ['art']}
                xbmc.log('Attempting to get current artwork for set: {}'.format(setname), level=xbmc.LOGDEBUG)
                response = json.loads(xbmc.executeJSONRPC(jsonrpc('VideoLibrary.GetMovieSetDetails', parameters)))
                if 'art' in response['result']['setdetails']:
                    art = response['result']['setdetails']['art']
                    if 'poster' in art:
                        current_poster = urllib.parse.unquote(art['poster']).lstrip('image://')
                    else:
                        current_poster = ''
                    if 'fanart' in art:
                        current_fanart = urllib.parse.unquote(art['fanart']).lstrip('image://')
                    else:
                        current_fanart = ''
                else:
                    current_poster = ''
                    current_fanart = ''
                xbmc.log('Received response from GetMovieSetDetails: {}'.format(response), level=xbmc.LOGDEBUG)
                
                if name['poster_path']:
                    remote_poster = tmdb_config['images']['secure_base_url'] + poster_size + name['poster_path'] + '/'
                else:
                    remote_poster = ''
                
                if name['backdrop_path']:
                    remote_fanart = tmdb_config['images']['secure_base_url'] + fanart_size + name['backdrop_path'] + '/'
                else:
                    remote_fanart = ''

                if current_poster != remote_poster or current_fanart != remote_fanart:
                    if remote_poster and remote_fanart:
                        parameters = {'setid': setid, 'art': {
                            'poster': tmdb_config['images']['secure_base_url'] + poster_size + name['poster_path'],
                            'fanart': tmdb_config['images']['secure_base_url'] + fanart_size + name['backdrop_path']}}
                    elif remote_poster and not remote_fanart:
                        parameters = {'setid': setid, 'art': {
                            'poster': tmdb_config['images']['secure_base_url'] + poster_size + name['poster_path']}}
                    elif remote_fanart and not remote_poster:
                        parameters = {'setid': setid, 'art': {
                            'fanart': tmdb_config['images']['secure_base_url'] + fanart_size + name['backdrop_path']}}
                    else:
                        break
                    xbmc.log('Sending JSON request to set artwork: {}'.format(json.dumps(parameters)), level=xbmc.LOGDEBUG)
                    response = json.loads(xbmc.executeJSONRPC(jsonrpc('VideoLibrary.SetMovieSetDetails', parameters)))
                    if response['result'] == 'OK':
                        xbmc.log('Movie Art Scraper: Set artwork for {0}.'.format(setname), level=xbmc.LOGDEBUG)
            except Exception as e:
                xbmc.log('Movie Art Scraper: Error setting artwork for {0}.'.format(setname), level=xbmc.LOGERROR)
                xbmc.log(str(e), level=xbmc.LOGERROR)
                pass
            break



def readsets(mincount):
    # collect set info from local system using json and run search for artwork
    moviesets = json.loads(xbmc.executeJSONRPC(jsonrpc('VideoLibrary.GetMovieSets')))
    if 'result' in moviesets and 'sets' in moviesets['result']:
        nsets = moviesets['result']['limits']['total']
        xbmc.log('Movie Art Scraper: Found {} sets.'.format(nsets), level=xbmc.LOGDEBUG)
        xbmc.executebuiltin(
            'Notification(Movie Art Scraper, {1} sets found. Scraping now..., 5000, {0})'.format(__icon__, nsets))
        for name in moviesets['result']['sets']:
            parameters = {'setid': name['setid']}
            setdetails = json.loads(xbmc.executeJSONRPC(jsonrpc('VideoLibrary.GetMovieSetDetails', parameters)))
            if len(setdetails['result']['setdetails']['movies']) >= mincount:
                done[name['label']] = name['setid']
        for name in done:
            searchset(done[name], name)
        xbmc.log('Movie Art Scraper: Finished scraping artwork for {} sets.'.format(len(done)), level=xbmc.LOGDEBUG)
        xbmc.executebuiltin('Notification(Movie Art Scraper, Done scraping set artwork for {1} sets., 10000, {0})'
                            .format(__icon__, len(done)))
    else:
        xbmc.log('Movie Art Scraper: No sets found.', level=xbmc.LOGERROR)
        xbmc.executebuiltin('Notification(Movie Art Scraper, No sets found, 10000, {0})'.format(__icon__))

try:
    parameters = {'setting': 'videolibrary.groupmoviesets'}
    groupmoviesets = json.loads(xbmc.executeJSONRPC(jsonrpc('Settings.GetSettingValue', parameters)))
    parameters = {'setting': 'videolibrary.groupsingleitemsets'}
    groupsingleitemsets = json.loads(xbmc.executeJSONRPC(jsonrpc('Settings.GetSettingValue', parameters)))
    
    # check if sets are enabled in kodi if not then exit
    if not groupmoviesets['result']['value']:
        xbmc.log('Movie Art Scraper: Movie sets are not enabled. Please enable and rerun.', level=xbmc.LOGERROR)
        xbmc.executebuiltin(
            'Notification(Movie Art Scraper, Movies sets are not enabled., 10000, {0})'.format(__icon__))
        xbmcgui.Window(10000).clearProperty(__addonid__ + '.running')
        exit(1)
    
    # check if single item sets are enabled if not then only get artwork if 2 or more exist in a set
    if not groupsingleitemsets['result']['value']:
        xbmc.log('Movie Art Scraper: Single item sets are not enabled.', level=xbmc.LOGDEBUG)
        readsets(2)
    else:
        xbmc.log('Movie Art Scraper: Single item sets are enabled.', level=xbmc.LOGDEBUG)
        readsets(1)
    
    xbmcgui.Window(10000).clearProperty(__addonid__ + '.running')
    exit(0)
except Exception as e:
    xbmc.log('Movie Art Scraper: An unexpected error occurred: {}'.format(str(e)), level=xbmc.LOGERROR)
    xbmcgui.Window(10000).clearProperty(__addonid__ + '.running')
    raise
