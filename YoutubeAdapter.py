import requests
import json
import re
import urllib.request
from pytube import Playlist
class YoutubeConverter():
  def get_title_from_url(self, video_link):
    params = {"format": "json", "url": video_link}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string
    with urllib.request.urlopen(url) as response:
      response_text = response.read()
      data = json.loads(response_text.decode())
      return data["title"]
  def get_url_from_name(self, title):
    title = title.replace(" ", "+")
    html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={title}")
    video_id = re.search(r"watch\?v=(\S{11})", html.read().decode()).groups()[0]
    return "https://www.youtube.com/watch?v=" + video_id
  def GetPlaylistInfo(self,url,reverse=False):
    p = [url for url in Playlist(url).video_urls]
    if reverse:p = p[::-1]
    names = ['' for _ in range(len(p))]
    return p,names
  def GetTrackInfo(self,url):
    if("https" in url or "http" in url):
      p,names = [url],[self.get_title_from_url(url)]
    else:
      url = urllib.parse.quote(url)
      p = [self.get_url_from_name(url)]
      names = [self.get_title_from_url(p[0])]
    return p,names