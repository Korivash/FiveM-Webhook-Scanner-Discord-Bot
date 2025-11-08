# FiveM Webhook Manager

A Discord bot that automatically manages Discord webhooks for FiveM QB-Core servers. Scans your QB-Core resources, creates organized log channels, generates new webhooks, and updates all configuration files automatically.

## Features

- 🔍 **Automatic Resource Scanning** - Finds all Discord webhooks across your QB-Core resources
- 🔨 **Channel Creation** - Creates dedicated log channels for each resource in a Discord category
- 🔗 **Webhook Generation** - Generates new webhooks and maps them to old ones
- 📝 **File Updates** - Automatically updates all configuration files with new webhook URLs
- 💾 **Backup System** - Creates backups before modifying any files
- 📊 **Detailed Reports** - Generates mapping files and guides for reference

## Requirements

- Python 3.8+
- Discord Bot with appropriate permissions
- FiveM server with QB-Core framework

## Installation

### Windows

1. Clone or download this repository
2. Run the setup script:
```bash
setup.bat
```

### Linux/Mac

1. Clone or download this repository
2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Installation

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" tab and create a bot
4. Enable these permissions:
   - Manage Channels
   - Manage Webhooks
   - Send Messages
5. Copy the bot token

### 2. Set Up Discord Server

1. Create a category called "QB-Core Logs" (or any name)
2. Right-click the category → Copy ID (Enable Developer Mode in Discord settings if needed)
3. Copy your server/guild ID

### 3. Configure Environment

Create a `.env` file or set these environment variables:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here
QB_LOGS_CATEGORY_ID=your_category_id_here
FIVEM_RESOURCES_PATH=C:/path/to/fivem/resources
```

## Usage

### Starting the Bot

Run the main script:

```bash
python fivem_webhook_manager.py
```

The bot will start and display its status in the console.

### Using Discord Commands

Once the bot is online, use these slash commands in Discord:

#### `/scan-webhooks`
Scans all QB-Core resources and performs the complete webhook setup:
1. Scans files for existing webhooks
2. Creates log channels for each resource
3. Generates new webhooks
4. Updates all configuration files
5. Creates backups and reports

#### `/webhook-status`
Shows the current bot status and configuration

## How It Works

### Scanning Process

The bot scans these file types:
- `.lua`, `.js`, `.ts` - Code files
- `.json`, `.cfg` - Configuration files
- `.txt`, `.md`, `.env` - Documentation and config
- `.xml`, `.yml`, `.yaml`, `.ini` - Various config formats

It skips common folders like `node_modules`, `.git`, and `cache`.

### Channel Organization

For each QB-Core resource with webhooks, the bot creates:
- A dedicated text channel named `resource-name-logs`
- One or more webhooks within that channel
- Proper categorization under your QB-Core Logs category

### File Updates

The bot automatically:
- Backs up original files to `webhook_backups/timestamp/`
- Replaces old webhook URLs with new ones
- Preserves file formatting and structure
- Tracks all changes in mapping files

### Output Files

After completion, check these directories:

**`webhook_output/`**
- `webhook_mappings.json` - JSON mapping of old to new webhooks
- `webhook_guide.txt` - Human-readable reference guide

**`webhook_backups/timestamp/`**
- Copies of all modified files before changes

## File Structure

```
fivem_webhook_manager/
├── fivem_webhook_manager.py    # Main bot script
├── qb_webhook_bot.py            # Alternative bot version
├── requirements.txt             # Python dependencies
├── setup.bat                    # Windows setup script
├── setup.sh                     # Linux/Mac setup script
├── .env                         # Configuration (create this)
├── webhook_output/              # Generated reports
└── webhook_backups/             # File backups
```

## Troubleshooting

### Bot won't start
- Verify all environment variables are set correctly
- Check that the bot token is valid
- Ensure Python 3.8+ is installed

### Missing permissions
- Make sure the bot has "Manage Channels" and "Manage Webhooks" permissions
- Verify the bot can access the target category

### Channels not created
- Confirm the `QB_LOGS_CATEGORY_ID` is correct
- Check that the bot has joined your server
- Verify the category exists and is accessible

### Files not updated
- Ensure the `FIVEM_RESOURCES_PATH` points to the correct directory
- Check file permissions (bot needs read/write access)
- Look for error messages in the console

## Configuration Options

### Rate Limiting

Adjust these values in the `Config` class if needed:

```python
rate_limit_delay: float = 1.5          # General API delay
channel_creation_delay: float = 1.5     # Delay between channel creation
webhook_creation_delay: float = 1.0     # Delay between webhook creation
```

### File Scanning

Customize scanned file types and excluded folders:

```python
file_extensions = ['.lua', '.js', '.ts', ...]
skip_folders = ['node_modules', '.git', ...]
```

## Safety Features

- **Automatic Backups** - All modified files are backed up before changes
- **Validation** - Configuration is validated before operations begin
- **Error Handling** - Graceful error handling with detailed logging
- **Non-Destructive** - Never deletes channels or webhooks, only creates new ones

## Best Practices

1. **Test First** - Run on a test server before production
2. **Backup Manually** - Keep your own backup of important files
3. **Review Changes** - Check the generated mappings before restarting your server
4. **Monitor Logs** - Watch the console for any warnings or errors
5. **Restart Server** - After updates complete, restart your FiveM server to apply changes

## Support

For issues or questions:
1. Check the console output for error messages
2. Review the generated webhook guide in `webhook_output/`
3. Verify all environment variables are correct
4. Check file permissions and paths

## License

This project is provided as-is for use with FiveM QB-Core servers.

## Credits

Created for automating Discord webhook management in QB-Core FiveM servers.
