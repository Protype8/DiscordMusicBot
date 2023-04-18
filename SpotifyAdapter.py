import spotipy
from settings import client_credentials_manager
class SpotifyConverter():
  sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
  words_to_filter = ["『", "』", "。"]
  def GetPlaylistInfo(self,url,reverse=False):
    offset = 0
    queues = []
    names = []
    while True:
      a = self.sp.playlist_tracks(url, offset=offset)["items"]
      for i in range(len(a)):
        track_info = a[i]["track"]
        name, queue = self.GetTrackInfo(track_info)
        names.append(name)
        queues.append(queue)
      if (len(a) < 100):
        break
      else:
        offset += 100
    return queues, names if not reverse else queues[::-1],names[::-1]
  def GetTrackInfo(self,url):
    track_info = self.sp.track(url)
    name = track_info["name"]
    artists = "+".join([track_info["artists"][i]["name"] for i in range(len(track_info["artists"]))])
    queue = name + "+" + artists
    for filtered_word in self.words_to_filter:
      queue = queue.replace(filtered_word, "")
    return [queue], [name]