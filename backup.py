from collections import deque
import discord
import asyncio
import spotipy
from discord.ext import commands
import requests
import json
from pytube import Playlist
import yt_dlp as youtube_dl
import aiohttp
import math
import typing as t
import urllib.request
import re
from settings import *

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def GetSpotifyPlayListInfo(url):
  offset = 0
  queues = []
  names = []
  while True:
    a = sp.playlist_tracks(url, offset=offset)["items"]
    for i in range(len(a)):
      track_info = a[i]["track"]
      name, queue = GetSpotifyTrackInfo(track_info)
      names.append(name)
      queues.append(queue)
    if (len(a) < 100):
      break
    else:
      offset += 100
  return queues, names


def GetSpotifyTrackInfo(url):
  track_info = sp.track(url)
  name = track_info["name"]
  artists = "+".join([track_info["artists"][i]["name"] for i in range(len(track_info["artists"]))])
  queue = name + "+" + artists
  for filtered_word in words_to_filter:
    queue = queue.replace(filtered_word, "")
  return [queue], [name]


class YTDLSource(discord.PCMVolumeTransformer):
  ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

  def __init__(self, source, *, data, volume=0.5):
    super().__init__(source, volume)
    self.data = data
    self.title = data.get('title')
    self.url = data.get('url')

  @classmethod
  async def from_url(cls, url, *, loop=None, stream=True):
    loop = loop or asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: cls.ytdl.extract_info(url, download=not stream))
    if 'entries' in data:
      data = data['entries'][0]
    filename = data['url'] if stream else cls.ytdl.prepare_filename(data)
    # return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
    return discord.FFmpegOpusAudio(filename, **ffmpeg_options)


class music(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.initalize()
    self.songs_per_page = 5

  def initalize(self):
    self.names = {}
    self.queue = {}
    self.looping = False
    self.loop_songs = 0
    self.message = None
    self.done = True

  @commands.Cog.listener()
  async def on_voice_state_update(self, member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
      return
    if (len(voice_state.channel.members)) == 1:
      await voice_state.disconnect()

  def get_title_from_url(self, video_link):
    params = {"format": "json", "url": video_link}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string
    with urllib.request.urlopen(url) as response:
      response_text = response.read()
      data = json.loads(response_text.decode())
      return data["title"]

  def get_songs_in_page(self, page_no):
    offset = (page_no - 1) * self.songs_per_page
    up_offset = (page_no) * self.songs_per_page
    if (up_offset > len(self.names) - 1):
      song_names = self.names[offset:]
    else:
      song_names = self.names[offset:up_offset]
    for i in range(len(song_names)):
      if (song_names[i] == ''):
        name = self.get_title_from_url(self.queue[offset + i])
        self.names[offset + i] = name
        song_names[i] = name
      song_names[i] += "\n"
    return song_names

  def get_url_from_name(self, title):
    title = title.replace(" ", "+")
    html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={title}")
    video_id = re.search(r"watch\?v=(\S{11})", html.read().decode()).groups()[0]
    return "https://www.youtube.com/watch?v=" + video_id

  def end_song(self):
    self.done = True

  async def play_next(self, ctx):
    if (ctx.voice_client is not None):
      vc = ctx.voice_client
      if len(self.queue) >= 1:
        if (ctx.voice_client is not None):
          if (not ("http" in self.queue[0] or "https" in self.queue[0])):
            q = urllib.parse.quote(self.queue[0])
            self.queue[0] = self.get_url_from_name(q)
          while 1:
            try:
              YTDLSource.ytdl.cache.remove()
              source = await YTDLSource.from_url(self.queue[0], loop=self.client.loop)
              if (self.names[0] == ''):
                self.names[0] = self.get_title_from_url(self.queue[0])
              if (self.message is not None and self.done):
                await self.message.delete()
              self.message = await ctx.send("Playing: " + self.names[0])
              self.done = False
              vc.play(source, after=lambda e: self.end_song())
              while not (self.done):
                await asyncio.sleep(1)
              if (self.looping):
                self.queue.insert(self.loop_songs, self.queue[0])
                self.names.insert(self.loop_songs, self.names[0])
              if (len(self.queue) > 0):
                del self.queue[0]
                del self.names[0]
              break
            except youtube_dl.utils.DownloadError or youtube_dl.utils.ExtractorError as e:
              print(e)
              await ctx.send("Looks like the video is age-restricted or unavailable for your region")
              break
          await self.play_next(ctx)
      else:
        asyncio.run_coroutine_threadsafe(ctx.send("Finished All Songs!"), self.client.loop)
        vc.stop()

  @commands.command()
  async def join(self, ctx):
    YTDLSource.ytdl.cache.remove()
    self.names[ctx.guild.id] = []
    self.queue[ctx.guild.id] = []
    if not ctx.author.voice:
      await ctx.send("You are not in a voice channel")
    else:
      self.initalize()
      voice_channel = ctx.author.voice.channel
      if ctx.voice_client is None:
        await voice_channel.connect()
      else:
        await ctx.voice_client.move_to(voice_channel)

  @commands.command(aliases=["d"])
  async def disconnect(self, ctx):
    del self.names[ctx.guild.id]
    del self.queue[ctx.guild.id]
    if ctx.voice_client is not None:
      await ctx.voice_client.disconnect()

  @commands.command(aliases=["p"])
  async def play(self, ctx, *, url):
    if (ctx.voice_client is None):
      await self.join(ctx)
    if ("playlist" in url):
      await ctx.send("Adding playlist to Queue!")
      if ("spotify" in url):
        p, names = GetSpotifyPlayListInfo(url)
      else:
        p = Playlist(url)
        names = ['' for _ in range(len(p))]
      await ctx.send("Playlist successfully added!")
    else:
      if ("https" in url or "http" in url):
        if ("spotify" in url):
          p, names = GetSpotifyTrackInfo(url)
        else:
          p, names = [url], [self.get_title_from_url(url)]
      else:
        await ctx.send("Searching for " + url)
        url = urllib.parse.quote(url)
        p = [self.get_url_from_name(url)]
        names = [self.get_title_from_url(p[0])]
      await ctx.send("Added " + names[0] + " To Queue")
    self.queue += p
    self.names += names
    if (len(self.queue) == len(p)):
      await self.play_next(ctx)

  @commands.command()
  async def loop(self, ctx, songs=1):
    if not ctx.voice_client:
      return
    if len(self.queue) == 0:
      await ctx.send("No songs in queue!")
      return
    self.looping = True
    if (songs == -1 or songs > len(self.queue)):
      self.loop_songs = len(self.queue)
      await ctx.send("Looping all songs in queue!")
    else:
      self.loop_songs = songs
      if (songs == 1):
        await ctx.send("Looping current song!")
      else:
        await ctx.send(f"Looping current and next {songs - 1} songs!")

  @commands.command()
  async def unloop(self, ctx):
    if ctx.voice_client:
      self.looping = False
      await ctx.send("Cancelling Loop")

  @commands.command()
  async def clear(self, ctx):
    if ctx.voice_client is not None:
      self.names[ctx.guild.id] = [self.names[ctx.guild.id][0]]
      self.queue = [self.queue[ctx.guild.id][0]]
      await ctx.send("Queue cleared.")

  @commands.command()
  async def pause(self, ctx):
    if ctx.voice_client is not None:
      if ctx.voice_client.is_playing():
        await ctx.send("Song Paused")
        ctx.voice_client.pause()

  @commands.command()
  async def skip(self, ctx, skip_amount: int = 1):
    if not ctx.voice_client:
      return
    self.queue[ctx.guild.id] = self.queue[ctx.guild.id][0] + self.queue[ctx.guild.id][skip_amount - 1:]
    self.names[ctx.guild.id] = self.names[ctx.guild.id][0] + self.names[ctx.guild.id][skip_amount - 1:]
    if (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
      await ctx.send("Song Skipped")
      ctx.voice_client.stop()

  @commands.command()
  async def resume(self, ctx):
    if ctx.voice_client is not None:
      if ctx.voice_client.is_paused():
        await ctx.send("Resuming Song")
        ctx.voice_client.resume()

  @commands.command(aliases=["sv"])
  async def set_volume(self, ctx, vol: float):
    if (vol > 100 or vol < 1):
      await ctx.send("Baka!")
      return
    volume = vol / 100
    try:
      ctx.voice_client.source = discord.PCMVolumeTransformer(self.client.source, volume)
    except:
      await ctx.send("Error 404!Braincell not found!")

  @commands.command()
  async def queue(self, ctx):
    if (len(self.queue) == 0):
      await ctx.send("Queue is empty")
      return
    pages = math.ceil(len(self.queue) / self.songs_per_page)
    cur_page = 1
    message = await ctx.send("Loading page!")
    await message.edit(content=f"Page {cur_page}/{pages}:\n{''.join(self.get_songs_in_page(cur_page))}")
    # getting the message object for editing and reacting
    await message.add_reaction("◀️")
    await message.add_reaction("▶️")

    def check(reaction, user):
      return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message == message
      # This makes sure nobody except the command sender can interact with the "menu"

    while True:
      try:
        reaction, user = await self.client.wait_for("reaction_add", timeout=60, check=check)
        # waiting for a reaction to be added - times out after x seconds, 60 in this
        # example
        if str(reaction.emoji) == "▶️" and cur_page != pages:
          cur_page += 1
          await message.edit(content="Loading next page!")
          await message.edit(content=f"Page {cur_page}/{pages}:\n{''.join(self.get_songs_in_page(cur_page))}")
          try:
            await message.remove_reaction(reaction, user)
          except:
            pass
        elif str(reaction.emoji) == "◀️" and cur_page > 1:
          cur_page -= 1
          await message.edit(content="Loading previous page!")
          await message.edit(content=f"Page {cur_page}/{pages}:\n{''.join(self.get_songs_in_page(cur_page))}")
          try:
            await message.remove_reaction(reaction, user)
          except:
            pass
        else:
          try:
            await message.remove_reaction(reaction, user)
          except:
            pass
      except asyncio.TimeoutError:
        await message.delete()
        break

  @commands.command()
  async def lyrics(self, ctx, *, name: t.Optional[str]):
    name = self.names[0] if name == None else name
    name = name.replace("MV", "")
    async with ctx.typing():
      async with aiohttp.request("GET", LYRICS_URL + name, headers={}) as r:
        if not 200 <= r.status <= 299:
          await ctx.send("No lyrics found...")
        else:
          data = await r.json()
          lyrics_splits = []
          lyrics_data = data["lyrics"]
          while len(lyrics_data) > max_word:
            lyrics_splits.append(lyrics_data[:max_word])
            lyrics_data = lyrics_data[max_word:]
          lyrics_splits.append(lyrics_data[:])
          count = 0
          for lyric_split in lyrics_splits:
            embed = discord.Embed(
              title=data["title"] if count == 0 else "",
              description=lyric_split,
              colour=ctx.author.color,
            )
            if (count == 0):
              embed.set_thumbnail(url=data["thumbnail"]["genius"])
              embed.set_author(name=data["author"])
            count += 1
            await ctx.send(embed=embed)


async def setup(client):
  client.add_cog(music(client))