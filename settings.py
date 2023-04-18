from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
load_dotenv()
cid = os.environ.get('spotify_cid')
secret = os.environ.get('spotify_secret')
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
max_word = 2000
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'cachedir': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                    "options": "-vn"}
LYRICS_URL = "https://some-random-api.ml/lyrics?title="
agents = {"d":["Jett","Phoenix","Raze","Reyna","Yoru","Neon"],
          "s":["Chamber","Cypher","Killjoy","Sage"],
          "c":["Astra","Brimstone","Omen","Viper","Harbor"],
          "i":["Sova","Breach","Skye","KAY/0","Fade","Gekko"]}
duelists = agents["d"]
non_duelists = agents["i"]+agents["s"]+agents["c"]
token = os.environ.get('discord_token')