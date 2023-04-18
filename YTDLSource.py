import discord
import asyncio
import yt_dlp as youtube_dl
from settings import *
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