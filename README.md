# Discord Bot

A multifunctional Discord bot built with Python that combines phonetic message conversion, music playback, and OBS Studio integration.

Originally developed to convert messages sent in a Discord server into their phonetic counterparts using consistent pronunciation and spelling, the bot was later expanded with voice channel music playback and custom OBS Studio controls.

## Features

### Phonetic Message Conversion
- Converts messages sent in a Discord server into their phonetic counterparts.
- Uses the Carnegie Mellon University Pronouncing Dictionary (CMU Dictionary) for consistent pronunciation.
- Can be enabled and disabled using slash commands.

Dictionary source: [Carnegie Mellon University Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict)

### Music Playback
- Joins and leaves Discord voice channels.
- Plays audio from YouTube videos.
- Supports YouTube playlists.
- Maintains a separate music queue for each server.
- Downloads upcoming tracks in the background to reduce playback delays.
- Supports skipping tracks and stopping playback.

### OBS Studio Integration
- Connects to OBS Studio through OBS WebSocket.
- Triggers configured media sources and restarts their playback.
- Enables and disables OBS source filters.

## Requirements

- Python 3
- [FFmpeg](https://www.gyan.dev/ffmpeg/builds/)
- [OBS Studio](https://obsproject.com/) (for OBS integration)
- A Discord bot application and token

## Installation

Install the required Python packages:

```bash
pip install -U discord.py
pip install yt-dlp
pip install python-dotenv
pip install PyNaCl
pip install obsws-python
```

### FFmpeg Setup

1. Download a FFmpeg build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
2. Extract the downloaded folder.
3. Locate the `bin` directory.
4. Add the `bin` directory to your Windows System Environment Variables under `PATH`.
5. Restart your terminal so the changes take effect.

FFmpeg is required for audio processing and music playback.

## Configuration

Create a `.env` file in the project's root directory.

Add the following environment variables:

```env
TOKEN=your_discord_bot_token
IP=your_obs_websocket_ip
OBS_PASSWORD=your_obs_websocket_password
```

- `TOKEN`: Your Discord bot token.
- `IP`: The IP address of the computer running OBS Studio.
- `OBS_PASSWORD`: Your OBS WebSocket password.

The OBS connection uses port `4455` by default.

**Important:** Keep your `.env` file private. Never upload your Discord token or OBS password to GitHub.

## Discord Setup

When creating your bot through the [Discord Developer Portal](https://discord.com/developers/applications):

1. Create a Discord application and add a bot.
2. Copy the bot token into your `.env` file.
3. Enable the **Message Content Intent** under Privileged Gateway Intents.
4. Ensure the bot has permission to view channels, send messages, use application commands, and connect to and speak in voice channels.
5. Invite the bot to your server with the appropriate permissions.

The bot uses Discord slash commands, which are synchronized when it starts.

## Commands

### Voice and Music Commands

| Command | Description |
|---|---|
| `/join` | Joins your current voice channel. |
| `/leave` | Disconnects from the voice channel. |
| `/play <url>` | Plays a YouTube video or queues a playlist. |
| `/skip` | Skips the currently playing track. |
| `/stop` | Stops playback and clears the music queue. |
| `/queue` | Displays the upcoming tracks. |

### Phonetic Commands

| Command | Description |
|---|---|
| `/activate` | Enables phonetic message conversion. |
| `/deactivate` | Disables phonetic message conversion. |

When activated, the bot replies to messages with their phonetic equivalents.

### OBS Commands

These commands require OBS Studio to be running with WebSocket enabled and the corresponding media sources and filters configured.

| Command | Description |
|---|---|
| `/explode` | Restarts the Explosion media source. |
| `/fnaf` | Restarts the FNAF media source. |
| `/joehendry` | Restarts the Joe Hendry media source. |
| `/aang` | Restarts the Aang media source. |
| `/rotd` | Restarts the ROTD media source. |
| `/wall` | Restarts the Wall media source and enables the Wall filter on Mic/Aux. |

## Running the Bot

Once dependencies and environment variables are configured, start the bot with:

```bash
python "Discord Bot.py"
```

The bot will connect to Discord, synchronize its slash commands, and begin listening for messages and commands.

## Technologies Used

- **Python** – Main programming language.
- **discord.py** – Discord API integration and bot functionality.
- **yt-dlp** – YouTube audio extraction and downloading.
- **FFmpeg** – Audio processing and playback.
- **PyNaCl** – Voice encryption support for Discord.
- **python-dotenv** – Environment variable management.
- **obsws-python** – OBS Studio WebSocket integration.
- **CMU Pronouncing Dictionary** – Phonetic pronunciation data.

## Notes

- OBS commands require the corresponding media inputs and filters to exist in OBS Studio.
- Music playback requires FFmpeg to be accessible through the system PATH.
- YouTube extraction may occasionally require updates to `yt-dlp` as YouTube changes its services.