import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import urllib
import json

# get settings and paths
__addon__ = xbmcaddon.Addon(id='metadata.scraper.moviesetartwork')
__addonhome__ = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__addonid__ = __addon__.getAddonInfo('id')
__icon__ = __addon__.getAddonInfo('icon')
image_dir = xbmc.translatePath(__addonhome__ + 'movie_set_artwork/')
poster_size = (__addon__.getSetting('poster_size'))
backdrop_size = (__addon__.getSetting('backdrop_size'))
overwrite = (__addon__.getSetting('overwrite').lower() == 'true')
api_key = '337431b553474aa71c9274d439a58d49'
tmdb_url = 'https://api.themoviedb.org/3/'
tmdb_config = json.load(urllib.urlopen('{0}configuration?api_key={1}'.format(tmdb_url, api_key)))
done = {}
# Ugly hack so script can't be run while running
xbmcgui.Window(10000).setProperty(__addonid__ + '.running', 'True')


def jsonrpc(method, *args):
    values = {"jsonrpc": "2.0", "id": "1", "method": method}
    if args:
        values["params"] = args
    json_cmd = json.dumps(values, sort_keys=True, separators=(',', ':'))
    json_cmd = json_cmd.replace('[', '')
    json_cmd = json_cmd.replace(']', '')
    return json_cmd


def searchset(setname):
    data = json.load(urllib.urlopen(
        '{0}search/collection?api_key={2}&language=en-US&query={1}&page=1'.format(tmdb_url, setname, api_key)))
    for name in data['results']:
        if name['name'] == setname:
            cleansetname = setname.replace(' ', '.').replace('/', '.')
            poster = name['poster_path']
            backdrop = name['backdrop_path']
            try:
                if overwrite or not xbmcvfs.exists(image_dir + cleansetname + '.poster.jpg'):
                    urllib.urlretrieve(tmdb_config['images']['secure_base_url'] + poster_size + '/' + poster,
                                       image_dir + cleansetname + '.poster.jpg')
                    xbmc.log('Movie Art Scraper: Downloaded poster for {}.'.format(setname), level=xbmc.LOGDEBUG)
            except Exception, e:
                xbmc.log('Movie Art Scraper: Error downloading poster for {}.'.format(setname), level=xbmc.LOGERROR)
                xbmc.log(str(e), level=xbmc.LOGERROR)
                pass
            try:
                if overwrite or not xbmcvfs.exists(image_dir + cleansetname + '.fanart.jpg'):
                    urllib.urlretrieve(tmdb_config['images']['secure_base_url'] + backdrop_size + '/' + backdrop,
                                       image_dir + cleansetname + '.fanart.jpg')
                    xbmc.log('Movie Art Scraper: Downloaded fanart for {}.'.format(setname), level=xbmc.LOGDEBUG)
            except Exception, e:
                xbmc.log('Movie Art Scraper: Error downloading fanart for {}.'.format(setname), level=xbmc.LOGERROR)
                xbmc.log(str(e), level=xbmc.LOGERROR)
                pass
            break


def replaceart(setid, setname, art_type):
    parameters = {'setid': setid, 'art': {art_type: image_dir + setname + '.' + art_type + '.jpg'}}
    response = json.loads(xbmc.executeJSONRPC(jsonrpc('VideoLibrary.SetMovieSetDetails', parameters)))
    if response['result'] == 'OK':
        xbmc.log('Movie Art Scraper: Set {0} for {1} to {2}{1}.{0}.jpg'.format(art_type, setname, image_dir),
                 level=xbmc.LOGDEBUG)
    else:
        xbmc.log('Movie Art Scraper: Error Setting {0} for {1} to {2}{1}.{0}.jpg'.format(art_type, setname, image_dir),
                 level=xbmc.LOGERROR)


def readsets(mincount):
    # collect set info from local system using json and run search for artwork
    moviesets = json.loads(xbmc.executeJSONRPC(jsonrpc('VideoLibrary.GetMovieSets')))
    if 'result' in moviesets and 'sets' in moviesets['result']:
        nsets = moviesets['result']['limits']['total']
        xbmc.log('Movie Art Scraper: Found {} sets.'.format(nsets), level=xbmc.LOGDEBUG)
        xbmc.executebuiltin(
            'XBMC.Notification(Movie Art Scraper, {1} sets found. Scraping now..., 5000, {0})'.format(__icon__, nsets))
        for name in moviesets['result']['sets']:
            parameters = {'setid': name['setid']}
            setdetails = json.loads(xbmc.executeJSONRPC(jsonrpc('VideoLibrary.GetMovieSetdetails', parameters)))
            if len(setdetails['result']['setdetails']['movies']) >= mincount:
                done[name['label']] = name['setid']
        for name in done:
            cleanname = name.replace(' ', '.').replace('/', '.')
            if overwrite or (not xbmcvfs.exists(image_dir + cleanname + '.poster.jpg') or not xbmcvfs.exists(
                            image_dir + cleanname + '.fanart.jpg')):
                searchset(name)
                xbmc.sleep(250)
        xbmc.log('Movie Art Scraper: Finished scraping artwork for {} sets.'.format(len(done)), level=xbmc.LOGDEBUG)
        xbmc.executebuiltin('XBMC.Notification(Movie Art Scraper, Done scraping set artwork for {1} sets., 10000, {0})'
                            .format(__icon__, len(done)))
        for name in done:
            cleanname = name.replace(' ', '.').replace('/', '.')
            if xbmcvfs.exists(image_dir + cleanname + '.poster.jpg'):
                replaceart(done[name], cleanname, 'poster')
            if xbmcvfs.exists(image_dir + cleanname + '.fanart.jpg'):
                replaceart(done[name], cleanname, 'fanart')
        xbmc.log('Movie Art Scraper: Finished setting artwork.', level=xbmc.LOGDEBUG)
        xbmc.executebuiltin(
            'XBMC.Notification(Movie Art Scraper, Finished setting artwork., 10000, {0})'.format(__icon__))
    else:
        xbmc.log('Movie Art Scraper: No sets found.', level=xbmc.LOGERROR)
        xbmc.executebuiltin('XBMC.Notification(Movie Art Scraper, No sets found, 10000, {0})'.format(__icon__))


parameters = {'setting': 'videolibrary.groupmoviesets'}
groupmoviesets = json.loads(xbmc.executeJSONRPC(jsonrpc('Settings.GetSettingValue', parameters)))
parameters = {'setting': 'videolibrary.groupsingleitemsets'}
groupsingleitemsets = json.loads(xbmc.executeJSONRPC(jsonrpc('Settings.GetSettingValue', parameters)))

# check if sets are enabled in kodi if not then exit
if not groupmoviesets['result']['value']:
    xbmc.log('Movie Art Scraper: Movie sets are not enabled. Please enable and rerun.', level=xbmc.LOGERROR)
    xbmc.executebuiltin(
        'XBMC.Notification(Movie Art Scraper, Movies sets are not enabled., 10000, {0})'.format(__icon__))
    xbmcgui.Window(10000).clearProperty(__addonid__ + '.running')
    exit(1)

# make dir to store artwork in if it doesn't exist already
if not xbmcvfs.exists(image_dir):
    xbmcvfs.mkdirs(image_dir)

# check if single item sets are enabled if not then only get artwork if 2 or more exist in a set
if not groupsingleitemsets['result']['value']:
    xbmc.log('Movie Art Scraper: Single item sets are not enabled.', level=xbmc.LOGDEBUG)
    readsets(2)
else:
    xbmc.log('Movie Art Scraper: Single item sets are enabled.', level=xbmc.LOGDEBUG)
    readsets(1)

xbmcgui.Window(10000).clearProperty(__addonid__ + '.running')
exit(0)
