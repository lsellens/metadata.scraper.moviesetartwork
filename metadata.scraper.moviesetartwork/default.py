import xbmc
import xbmcaddon
import xbmcgui

__addon__ = xbmcaddon.Addon(id='metadata.scraper.moviesetartwork')
__addonhome__ = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__addonid__ = __addon__.getAddonInfo('id')
__icon__ = __addon__.getAddonInfo('icon')

if __name__ == '__main__':
    if (xbmcgui.Window(10000).getProperty(__addonid__ + '.running') != "True"):
        # Open settings dialog
        __addon__.openSettings()
    else:
        xbmc.executebuiltin('XBMC.Notification(Movie Art Scraper, Script is still running. Please wait., 10000, {0})'.format(__icon__))

