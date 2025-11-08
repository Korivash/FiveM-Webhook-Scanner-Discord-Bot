# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies
```bash
# Windows
setup.bat

# Linux/Mac
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your values:
```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here
QB_LOGS_CATEGORY_ID=your_category_id_here
FIVEM_RESOURCES_PATH=C:/path/to/fivem/resources
```

### 3. Get Your Discord IDs

**Bot Token:**
1. Visit https://discord.com/developers/applications
2. Create new application → Bot → Copy token

**Guild ID:**
1. Enable Developer Mode in Discord settings
2. Right-click your server → Copy ID

**Category ID:**
1. Create a category called "QB-Core Logs"
2. Right-click category → Copy ID

### 4. Start the Bot
```bash
python fivem_webhook_manager.py
```

### 5. Run the Command
In Discord, type: `/scan-webhooks`

## That's It!

The bot will:
- Scan all your QB-Core resources
- Create organized log channels
- Generate new webhooks
- Update all your config files
- Create backups of everything

After it completes, restart your FiveM server and you're done!

## Need Help?

Check the full README.md for detailed troubleshooting and configuration options.
