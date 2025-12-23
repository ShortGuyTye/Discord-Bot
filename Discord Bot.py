import discord
import os
import Phonetics
import yt_dlp
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from obsws_python import ReqClient
import asyncio

# ----------------- Setup ----------------
load_dotenv()
phonetics = Phonetics.wordDict(phonetics={})
soundList = Phonetics.soundDict(soundList={})
is_on = False
queues = {}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- Helper Functions ------------------
def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

async def play_next(guild_id, text_channel):
    queue = get_queue(guild_id)
    vc = bot.get_guild(guild_id).voice_client
    if not vc or not queue:
        return

    info = queue.pop(0)
    audio_url = info["url"]
    title = info.get("title", "Unknown")
    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(
            audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )
    )

    def after_play(error):
        asyncio.run_coroutine_threadsafe(play_next(guild_id, text_channel), bot.loop)

    vc.play(source, after=after_play)
    await text_channel.send(f"Now playing: **{title}**")

# ---------------- Voice Commands ----------------
@bot.tree.command(name="join", description="Join a voice chat")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("You're not in a voice channel", ephemeral=True)
        return
    if interaction.guild.voice_client:
        await interaction.response.send_message("I'm already in a voice channel", ephemeral=True)
        return
    channel = interaction.user.voice.channel
    await channel.connect()
    await interaction.response.send_message(f"Joined {channel.name}")

@bot.tree.command(name="leave", description="Leave the voice chat")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message("I'm not in a voice channel", ephemeral=True)
        return
    await vc.disconnect()
    await interaction.response.send_message("Left voice chat")

# ---------------- Music Commands ----------------
@bot.tree.command(name="play", description="Play audio from YouTube")
@app_commands.describe(url="YouTube URL or playlist")
async def play(interaction: discord.Interaction, url: str):
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message("Not connected to a voice channel", ephemeral=True)
        return
    await interaction.response.send_message("Loading…")

    ydl_opts = {
        "format": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best",
        "quiet": True,
        "ignoreerrors": True,
        "nocheckcertificate": True,
        "source_address": "0.0.0.0",
        "extract_flat": False,
        "skip_download": True,
        "noplaylist": False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        await interaction.followup.send(f"Failed to load audio: {e}")
        return

    entries = info["entries"] if "entries" in info else [info]
    entries = [e for e in entries if e]

    if not entries:
        await interaction.followup.send("No playable videos found.")
        return

    queue = get_queue(interaction.guild.id)
    queue.extend(entries)

    if not vc.is_playing():
        await play_next(interaction.guild.id, interaction.channel)


@bot.tree.command(name="stop", description="Stops current track and clears the queue")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_playing():
        await interaction.response.send_message("No track is playing", ephemeral=True)
        return
    vc.stop()
    queues[interaction.guild.id] = []
    await interaction.response.send_message("Stopped playback and cleared the queue")

@bot.tree.command(name="skip", description="Skips the current track")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_playing():
        await interaction.response.send_message("No track is playing", ephemeral=True)
        return
    vc.stop()
    await interaction.response.send_message("Skipped current track")

# ---------------- Phonetics Commands -----------------
@bot.tree.command(name="activate", description="activate")
async def activate(interaction: discord.Interaction):
    global is_on
    is_on = True
    await interaction.response.send_message("Bwahaha you fool")

@bot.tree.command(name="deactivate", description="deactivate")
async def deactivate(interaction: discord.Interaction):
    global is_on
    is_on = False
    await interaction.response.send_message("WHAT? NO! HOW DID YOU FIND MY ONLY WEAKNESS??")

# ------------------ Explode Command ----------------
@bot.tree.command(name="explode", description="Blows him up like crazy")
async def explode(interaction: discord.Interaction):
    obs = ReqClient(
        host="localhost",
        port=4455,
        password="sJXOTyMBZgMZMrFD"
    )
    obs.trigger_media_input_action(
        name="Explosion",
        action="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
    )
    await interaction.response.send_message("Boom Shakalaka")

# ----------------- Bot Events ----------------
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if is_on:
        await message.reply(Phonetics.phonetic(message.content, phonetics, soundList))
    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online")

bot.run(os.getenv("TOKEN"))
