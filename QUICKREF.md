# Quick Reference Card

## 🚀 Installation (30 seconds)
```bash
# Windows
setup.bat

# Linux/Mac
./setup.sh
```

## ⚙️ Configuration (2 minutes)
```env
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_GUILD_ID=your_server_id
QB_LOGS_CATEGORY_ID=your_category_id
FIVEM_RESOURCES_PATH=C:/path/to/resources
```

## 🎮 Usage
```bash
# Start bot
python fivem_webhook_manager.py

# In Discord
/scan-webhooks
```

## 📋 What It Does
1. Scans QB-Core resources
2. Creates log channels
3. Generates webhooks
4. Updates config files
5. Creates backups

## 📁 Output Locations
- `webhook_output/` - Mappings & guides
- `webhook_backups/` - Original files

## 🔧 Commands
- `/scan-webhooks` - Run full scan
- `/webhook-status` - Check status

## ⚡ Quick Tips
- Always backup before running
- Check console for progress
- Restart FiveM after completion
- Test webhooks in-game

## 🆘 Common Issues
**Bot won't start?**
- Check .env file exists
- Verify bot token

**No channels created?**
- Check category ID
- Verify bot permissions

**Files not updated?**
- Check FiveM path
- Verify write permissions

## 📖 Full Docs
See README.md for complete documentation
