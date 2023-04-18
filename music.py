import urllib
from SpotifyAdapter import SpotifyConverter
import discord
import asyncio
from discord.ext import commands
from pytube import Playlist
import yt_dlp as youtube_dl
import aiohttp
import math
import typing as t
from MusicGuildInformation import GuildInformation
from SpotifyAdapter import SpotifyConverter
from YoutubeAdapter import YoutubeConverter
from YTDLSource import YTDLSource
from settings import *
class music(commands.Cog):
    def __init__(self,client):
        self.songs_per_page = 5
        self.client = client
        self.guilds = {}
        self.youtube_converter = YoutubeConverter()
        self.spotify_converter = SpotifyConverter()
    @commands.Cog.listener()
    async def on_voice_state_update(self,member, before, after):
        voice_state = member.guild.voice_client
        if voice_state is None:
            return
        if (len(voice_state.channel.members)) == 1:
            await voice_state.disconnect()
    def end_song(self,info):
        info.done = True
    async def play_next(self,ctx):
        musicInfo = self.guilds[ctx.guild.id]
        if(ctx.voice_client is not None):
            vc = ctx.voice_client
            if len(self.guilds[ctx.guild.id].queue) >= 1:
                if (ctx.voice_client is not None):
                    if (not ("http" in musicInfo.queue[0] or "https" in musicInfo.queue[0])):
                        q = urllib.parse.quote(musicInfo.queue[0])
                        musicInfo.queue[0] = self.youtube_converter.get_url_from_name(q)
                    try:
                        YTDLSource.ytdl.cache.remove()
                        source = await YTDLSource.from_url(musicInfo.queue[0], loop=self.client.loop)
                        if (musicInfo.names[0] == ''):
                            musicInfo.names[0] = self.youtube_converter.get_title_from_url(musicInfo.queue[0])
                        if (musicInfo.message is not None and musicInfo.done):
                            await musicInfo.message.delete()
                        musicInfo.message = await ctx.send("Playing: " + musicInfo.names[0])
                        musicInfo.done = False
                        vc.play(source, after=lambda e: self.end_song(musicInfo))
                        while not (musicInfo.done):
                            await asyncio.sleep(1)
                        if (musicInfo.looping):
                          musicInfo.queue.insert(musicInfo.loop_songs, musicInfo.queue[0])
                          musicInfo.names.insert(musicInfo.loop_songs, musicInfo.names[0])
                    except youtube_dl.utils.DownloadError or youtube_dl.utils.ExtractorError as e:
                        print(e)
                        await ctx.send("Looks like the video is age-restricted or unavailable for your region")
                    finally:
                      if (ctx.guild.id in self.guilds and len(self.guilds[ctx.guild.id].queue) > 0):
                        del musicInfo.queue[0]
                        del musicInfo.names[0]
                    await self.play_next(ctx)
            else:
                asyncio.run_coroutine_threadsafe(ctx.send("Finished All Songs!"), self.client.loop)
                vc.stop()
    @commands.command()
    async def join(self,ctx):
        YTDLSource.ytdl.cache.remove()
        if not ctx.author.voice:
            await ctx.send("You are not in a voice channel")
        else:
            self.guilds[ctx.guild.id] = GuildInformation()
            print(self.guilds)
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                print("?")
                await voice_channel.connect()
                print("???")
            else:
                await ctx.voice_client.move_to(voice_channel)
    @commands.command(aliases=["d"])
    async def disconnect(self, ctx):
      del self.guilds[ctx.guild.id]
      if ctx.voice_client is not None:
          await ctx.voice_client.disconnect()
    @commands.command(aliases=["p"])
    async def play(self,ctx,url,reverse=False):
        if (ctx.voice_client is None):
            await self.join(ctx)
        musicInfo = self.guilds[ctx.guild.id]
        current_converter = self.spotify_converter if "spotify" in url else self.youtube_converter
        if("playlist" in url):
          await ctx.send("Adding playlist to Queue!")
          p,names = current_converter.GetPlaylistInfo(url,reverse)
          await ctx.send("Playlist successfully added!")
        else:
          p,names = current_converter.GetTrackInfo(url)
          await ctx.send("Added "+names[0]+" To Queue")
        musicInfo.queue += p
        musicInfo.names += names
        if(len(musicInfo.queue) == len(p)):
          await self.play_next(ctx)
    @commands.command()
    async def loop(self, ctx,songs=1):
        musicInfo = self.guilds[ctx.guild.id]
        if not ctx.voice_client:
          return
        if len(self.guilds[ctx.guild.id].queue) == 0:
          await ctx.send("No songs in queue!")
          return
        musicInfo.looping = True
        if(songs == -1 or songs > len(musicInfo.queue)):
              musicInfo.loop_songs = len(musicInfo.queue)
              await ctx.send("Looping all songs in queue!")
        else:
            musicInfo.loop_songs = songs
            if(songs == 1):
                await ctx.send("Looping current song!")
            else:
                await ctx.send(f"Looping current and next {songs-1} songs!")
    @commands.command()
    async def unloop(self, ctx):
        musicInfo = self.guilds[ctx.guild.id]
        if ctx.voice_client:
            musicInfo.looping = False
            await ctx.send("Cancelling Loop")
    @commands.command()
    async def clear(self, ctx):
        musicInfo = self.guilds[ctx.guild.id]
        if ctx.voice_client is not None:
            musicInfo.names = [musicInfo.names[0]]
            musicInfo.queue = [musicInfo.queue[0]]
            await ctx.send("Queue cleared.")
    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client is not None:
            if ctx.voice_client.is_playing():
                await ctx.send("Song Paused")
                ctx.voice_client.pause()
    @commands.command()
    async def skip(self, ctx,skip_amount:int=1):
        musicInfo = self.guilds[ctx.guild.id]
        if not ctx.voice_client:
          return
        musicInfo.queue = [musicInfo.queue[0]]+musicInfo.queue[skip_amount-1:]
        musicInfo.names = [musicInfo.names[0]]+musicInfo.names[skip_amount-1:]
        if(ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            await ctx.send("Song Skipped")
            ctx.voice_client.stop()
    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client is not None:
            if ctx.voice_client.is_paused():
                await ctx.send("Resuming Song")
                ctx.voice_client.resume()
    @commands.command(aliases=["sv"])
    async def set_volume(self,ctx,vol:float):
        if(vol > 100 or vol < 1):
            await ctx.send("Baka!")
            return
        volume = vol/100
        try:
            ctx.voice_client.source = discord.PCMVolumeTransformer(self.client.source,volume)
        except:
            await ctx.send("Error 404!Braincell not found!")
    def get_songs_in_page(self, page_no, guild_id):
      offset = (page_no - 1) * self.songs_per_page
      up_offset = (page_no) * self.songs_per_page
      if (up_offset > len(self.guilds[guild_id].names) - 1):
        song_names = self.guilds[guild_id].names[offset:]
      else:
        song_names = self.guilds[guild_id].names[offset:up_offset]
      for i in range(len(song_names)):
        if (song_names[i] == ''):
          name = self.youtube_converter.get_title_from_url(self.guilds[guild_id].queue[offset + i])
          self.guilds[guild_id].names[offset + i] = name
          song_names[i] = name
        song_names[i] += "\n"
      return song_names
    @commands.command()
    async def queue(self, ctx):
        if(len(self.guilds[ctx.guild.id].queue)  == 0):
            await ctx.send("Queue is empty")
            return
        pages = math.ceil(len(self.guilds[ctx.guild.id].queue)/self.songs_per_page)
        cur_page = 1
        message = await ctx.send("Loading page!")
        await message.edit(content=f"Page {cur_page}/{pages}:\n{''.join(self.get_songs_in_page(cur_page,ctx.guild.id))}")
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
                    await message.edit(content=f"Page {cur_page}/{pages}:\n{''.join(self.get_songs_in_page(cur_page,ctx.guild.id))}")
                    try:
                        await message.remove_reaction(reaction, user)
                    except:
                        pass
                elif str(reaction.emoji) == "◀️" and cur_page > 1:
                    cur_page -= 1
                    await message.edit(content="Loading previous page!")
                    await message.edit(content=f"Page {cur_page}/{pages}:\n{''.join(self.get_songs_in_page(cur_page,ctx.guild.id))}")
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
    async def lyrics(self,ctx,*,name:t.Optional[str]):
        name = self.guilds[ctx.guild.id].names[0] if name == None else name
        name = name.replace("MV","")
        async with ctx.typing():
            async with aiohttp.request("GET",LYRICS_URL+name,headers={}) as r:
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
                            title = data["title"] if count == 0  else "",
                            description = lyric_split,
                            colour = ctx.author.color,
                        )
                        if(count == 0):
                            embed.set_thumbnail(url=data["thumbnail"]["genius"])
                            embed.set_author(name=data["author"])
                        count += 1
                        await ctx.send(embed=embed)
async def setup(client):
    client.add_cog(music(client))