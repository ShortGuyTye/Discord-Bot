import discord
import os
import Phonetics
import yt_dlp
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv() # load all the variables from the env file
phonetics = Phonetics.wordDict(phonetics = {})
soundList = Phonetics.soundDict(soundList = {})
is_on = False

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

@bot.slash_command(name="join", description="join a voice chat")
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.respond(f"Joined {channel.name}!")
    else:
        await ctx.respond("You're not in voice chat")

@bot.slash_command(name="leave", description="leave a voice chat")
async def leave(ctx):
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.respond("Left voice chat")
    else:
        await ctx.respond("Not in voice chat")

@bot.slash_command(name="play", description="Play audio from YouTube")
async def play(ctx, url):
    vc = ctx.guild.voice_client
    if not vc:
        await ctx.respond("Not connected to a voice channel")
    else:
        await ctx.respond("Loading")

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']

    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio_url,
    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
))
    vc.play(source)
    await ctx.send(f"Now playing: {info.get('title', 'Unknown')}")

@bot.slash_command(name="stop", description="Stops current track")
async def stop(ctx):
    vc = ctx.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.respond("Track stopped")
    else:
        await ctx.respond("No track is playing")

@bot.slash_command(name="activate", description="activate")
async def activate(ctx):
    global is_on 
    is_on = True
    await ctx.respond("Bwahaha you fool")

@bot.slash_command(name="deactivate", description="deactivate")
async def deactivate(ctx):
    global is_on 
    is_on = False
    await ctx.respond("WHAT? NO! HOW DID YOU FIND MY ONLY WEAKNESS??")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    elif (is_on):
        await message.reply(content=Phonetics.phonetic(message.content, phonetics, soundList))

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    await bot.sync_commands()

bot.run(os.getenv('TOKEN'))