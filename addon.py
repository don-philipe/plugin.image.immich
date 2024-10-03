import json
import sys
import xbmcaddon
import xbmcgui
import xbmcplugin
from urllib import parse, request
from threading import Thread

from resources.lib.proxy import start as start_proxy

my_addon = xbmcaddon.Addon()
server_url = my_addon.getSetting('server_url')
api_key = my_addon.getSetting('api_key')
proxy_thread = Thread(target=start_proxy, args=(api_key, server_url))


def build_url(query: str) -> str:
    """
    Build URL from base url and given query parameter.
    :param query: query part of the URL to produce
    :return: a complete URL with given query parameter part
    """
    base_url = sys.argv[0]
    return base_url + '?' + parse.urlencode(query)


def get(url: str, api_key: str):
    """
    Run a get request agains the immich server.
    :param url: the actual url
    :param api_key: the api key to use for request
    :return: a response object
    """
    req = request.Request(url)
    req.add_header('x-api-key', api_key)
    return request.urlopen(req)


def get_albums(handle):
    """
    Retrieve list of all albums from immich server and build xbmc directory items from result list.
    :param handle: the addon handle
    """
    url = server_url + '/api/albums'
    res = get(url, api_key)
    for album in json.loads(res.read()):
        li = xbmcgui.ListItem(album['albumName'])
        li_url = build_url({'mode': 'show_album_pics', 'album_id': album['id']})
        xbmcplugin.addDirectoryItem(handle=handle, url=li_url, listitem=li, isFolder=True,
                                    totalItems=album['assetCount'])
    xbmcplugin.endOfDirectory(handle)


def get_album_pics(handle, uuid: str):
    """
    Get all pictures of an album and set them as content of a directory ("getAlbumInfo" endpoint).
    For picture retrieval a proxy is used to download the actual files. This function checks if that proxy is running.
    If it's not, then function is starting it.
    :param handle: the addon handle
    :param uuid: the album UUID
    """
    url = server_url + '/api/albums/' + uuid
    req = request.Request(url)
    req.add_header('x-api-key', api_key)
    res = request.urlopen(req)

    if not proxy_thread.is_alive():
        proxy_thread.start()

    for asset in json.loads(res.read())['assets']:
        li = xbmcgui.ListItem(asset['id'])
        pic_name = asset['originalFileName']
        if 'exifInfo' in asset.keys() and 'description' in asset['exifInfo'].keys():
            pic_name = asset['exifInfo']['description']
        li.setInfo(type='pictures', infoLabels={'Title': pic_name, 'size': asset['exifInfo']['fileSizeInByte']})
        li.setProperty('IsPlayable', 'true')
        li.setProperty('MimeType', asset['originalMimeType'])
        li.setMimeType(asset['originalMimeType'])
        li_url = 'http://localhost:8079/' + asset['id']
        xbmcplugin.addDirectoryItem(handle=handle, url=li_url, listitem=li)
    xbmcplugin.endOfDirectory(handle)


def get_tags(handle):
    """
    Get all tags
    :param handle: the addon handle
    """
    url = server_url + '/api/tags'
    res = get(url, api_key)
    for tag in json.loads(res.read()):
        li = xbmcgui.ListItem(tag['name'])
        li_url = build_url({'mode': 'show_tags_pics', 'tag_id': tag['id']})
        xbmcplugin.addDirectoryItem(handle=handle, url=li_url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(handle)


addon_handle = int(sys.argv[1])
xbmcplugin.setContent(addon_handle, 'images')
args = parse.parse_qs(sys.argv[2][1:])
mode = args.get('mode')

if mode is None:
    albums = xbmcgui.ListItem('Albums')
    all_albums_url = build_url({'mode': 'show_albums'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=all_albums_url, listitem=albums, isFolder=True)
    tags = xbmcgui.ListItem('Tags')
    all_tags_url = build_url({'mode': 'show_tags'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=all_tags_url, listitem=tags, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)
elif mode[0] == 'show_albums':
    get_albums(addon_handle)
elif mode[0] == 'show_album_pics':
    get_album_pics(addon_handle, args.get('album_id')[0])
elif mode[0] == 'show_tags':
    get_tags(addon_handle)
