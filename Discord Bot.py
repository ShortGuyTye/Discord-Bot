import discord
import os
import Phonetics
import yt_dlp
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from obsws_python import ReqClient
import asyncio
import sys
import tempfile
import uuid
import json
import urllib.parse
import urllib.request

# ----------------- Setup ----------------
load_dotenv()
phonetics = Phonetics.wordDict(phonetics={})
soundList = Phonetics.soundDict(soundList={})
is_on = False
queues = {}

AUDIO_DIR = os.path.join(tempfile.gettempdir(), "discord_bot_audio")
os.makedirs(AUDIO_DIR, exist_ok=True)
loading = set()  # guilds that are currently downloading a track

# clear out leftovers from any previous run
for f in os.listdir(AUDIO_DIR):
    try:
        os.remove(os.path.join(AUDIO_DIR, f))
    except OSError:
        pass

DOWNLOAD_OPTS = {
    "format": "bestaudio[ext=webm]/bestaudio",
    "outtmpl": os.path.join(AUDIO_DIR, "%(id)s.%(ext)s"),
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- Helper Functions ------------------
def download_audio(page_url):
    opts = dict(DOWNLOAD_OPTS)
    # unique filename, so the same video queued twice can't collide
    opts["outtmpl"] = os.path.join(AUDIO_DIR, f"{uuid.uuid4().hex}.%(ext)s")
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(page_url, download=True)
        return ydl.prepare_filename(info), info.get("title", "Unknown")

def start_prefetch(item):
    """Begin downloading a queued item in the background (once)."""
    if "task" not in item:
        loop = asyncio.get_running_loop()
        item["task"] = loop.run_in_executor(None, download_audio, item["page_url"])

def discard_item(item):
    """Throw away a queued item, deleting its file if it was already downloaded."""
    task = item.get("task")
    if not task:
        return

    def cleanup(fut):
        if fut.cancelled() or fut.exception():
            return
        try:
            os.remove(fut.result()[0])
        except OSError:
            pass

    task.add_done_callback(cleanup)

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

async def play_next(guild_id, text_channel):
    queue = get_queue(guild_id)
    guild = bot.get_guild(guild_id)
    vc = guild.voice_client if guild else None
    if not vc or not queue or guild_id in loading or vc.is_playing():
        return

    item = queue.pop(0)
    loading.add(guild_id)
    path = None
    try:
        start_prefetch(item)  # no-op if it's already downloading
        path, title = await item["task"]
    except Exception as e:
        await text_channel.send(f"Couldn't load that track: {e}")
    finally:
        loading.discard(guild_id)

    if path is None:
        await play_next(guild_id, text_channel)  # try the next track
        return

    vc = guild.voice_client  # may have changed during the download
    if not vc:
        try:
            os.remove(path)
        except OSError:
            pass
        return

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(path, options="-vn", stderr=sys.stderr)
    )

    def after_play(error):
        try:
            os.remove(path)
        except OSError:
            pass
        if error:
            print(f"Player error: {error}")
        asyncio.run_coroutine_threadsafe(play_next(guild_id, text_channel), bot.loop)

    vc.play(source, after=after_play)
    await text_channel.send(f"Now playing: **{title}**")

    # start downloading the next track while this one plays
    if queue:
        start_prefetch(queue[0])

async def ytdlp_extract(url, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False))

def fix_url(url):
    if "youtube.com/watch" in url:
        video_id = url.split("v=")[1].split("&")[0]
        return f"https://youtu.be/{video_id}"
    return url

def fetch_title(url):
    """Look up a video's title through YouTube's oEmbed endpoint. Falls back to the link."""
    try:
        api = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(url, safe="")
        with urllib.request.urlopen(api, timeout=5) as r:
            return json.load(r).get("title") or url
    except Exception:
        return url

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
    vc = interaction.guild.voice_client
    if not vc.is_playing():
        await play_next(interaction.guild.id, interaction.channel)

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
    url = fix_url(url)
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message("Not connected to a voice channel", ephemeral=True)
        return
    await interaction.response.send_message("Loading…")

    if "/playlist" in url:
        opts = {"extract_flat": "in_playlist", "skip_download": True,
                "quiet": True, "no_warnings": True}
        try:
            info = await ytdlp_extract(url, opts)
        except Exception as e:
            await interaction.followup.send(f"Failed to load playlist: {e}")
            return
        entries = [e for e in (info or {}).get("entries", []) if e and e.get("url")]
        items = [{"page_url": e["url"], "title": e.get("title") or "Unknown"} for e in entries]
    else:
        loop = asyncio.get_running_loop()
        title = await loop.run_in_executor(None, fetch_title, url)
        items = [{"page_url": url, "title": title}]

    if not items:
        await interaction.followup.send("No playable videos found.")
        return

    queue = get_queue(interaction.guild.id)
    busy = vc.is_playing() or interaction.guild.id in loading
    queue.extend(items)

    if busy:
        start_prefetch(queue[0])
        if len(items) == 1:
            await interaction.channel.send(f"Queued: **{items[0]['title']}**")
        else:
            await interaction.channel.send(f"Queued **{len(items)}** tracks")
    await play_next(interaction.guild.id, interaction.channel)

@bot.tree.command(name="stop", description="Stops current track and clears the queue")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_playing():
        await interaction.response.send_message("No track is playing", ephemeral=True)
        return
    for item in get_queue(interaction.guild.id):
        discard_item(item)
    queues[interaction.guild.id] = []
    vc.stop()
    await interaction.response.send_message("Stopped playback and cleared the queue")

@bot.tree.command(name="skip", description="Skips the current track")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_playing():
        await interaction.response.send_message("No track is playing", ephemeral=True)
        return
    vc.stop()
    await interaction.response.send_message("Skipped current track")

@bot.tree.command(name="queue", description="Shows current queue")
async def queue(interaction: discord.Interaction):
    queue = get_queue(interaction.guild.id)

    if not queue:
        await interaction.response.send_message("Queue is empty")
        return

    lines = []
    for i, item in enumerate(queue, start=1):
        title = item.get("title", "Unknown")
        lines.append(f"{i}. {title}")
    text = "\n".join(lines)
    await interaction.response.send_message(text[:2000])

    for i in range(2000, len(text), 2000):
        await interaction.followup.send(text[i:i+2000])

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

# ------------------ OBS Commands ----------------
@bot.tree.command(name="explode", description="Blows him up like crazy")
async def explode(interaction: discord.Interaction):
    obs = ReqClient(
        host=os.getenv("IP"),
        port=4455,
        password=os.getenv("OBS_PASSWORD")
    )
    obs.trigger_media_input_action(
        name="Explosion",
        action="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
    )
    await interaction.response.send_message("Boom Shakalaka")

@bot.tree.command(name="fnaf", description="Scares them up like crazy")
async def fnaf(interaction: discord.Interaction):
    obs = ReqClient(
        host=os.getenv("IP"),
        port=4455,
        password=os.getenv("OBS_PASSWORD")
    )
    obs.trigger_media_input_action(
        name="FNAF",
        action="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
    )
    await interaction.response.send_message("Gotem")

@bot.tree.command(name="joehendry", description="Joes him up like crazy")
async def joehendry(interaction: discord.Interaction):
    obs = ReqClient(
        host=os.getenv("IP"),
        port=4455,
        password=os.getenv("OBS_PASSWORD")
    )
    obs.trigger_media_input_action(
        name="Joe Hendry",
        action="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
    )
    await interaction.response.send_message("**CLAP CLAP**")

@bot.tree.command(name="aang", description="Proves him right like crazy")
async def aang(interaction: discord.Interaction):
    obs = ReqClient(
        host=os.getenv("IP"),
        port=4455,
        password=os.getenv("OBS_PASSWORD")
    )
    obs.trigger_media_input_action(
        name="Aang",
        action="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
    )
    await interaction.response.send_message("He's Right")

@bot.tree.command(name="rotd", description="___ like crazy")
async def rotd(interaction: discord.Interaction):
    obs = ReqClient(
        host=os.getenv("IP"),
        port=4455,
        password=os.getenv("OBS_PASSWORD")
    )
    obs.trigger_media_input_action(
        name="ROTD",
        action="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
    )
    await interaction.response.send_message("Are you sure?")

@bot.tree.command(name="wall", description="Shuts him up like crazy")
async def wall(interaction: discord.Interaction):
    obs = ReqClient(
        host=os.getenv("IP"),
        port=4455,
        password=os.getenv("OBS_PASSWORD")
    )
    obs.trigger_media_input_action(
        name="Wall",
        action="OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
    )
    obs.set_source_filter_enabled("Mic/Aux", "Wall", True)

    await interaction.response.send_message("SHUT UP MOOOOM, SILENCE FROM YOU")

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