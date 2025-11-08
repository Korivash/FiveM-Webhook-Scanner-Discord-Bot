#!/usr/bin/env python3
"""
QB-Core Webhook Bot v9.0
Discord bot with slash command to manage QB-Core webhooks

Commands:
  /scan-webhooks - Scans QB-Core resources, creates channels/webhooks, updates files

No server wipe, no role management - ONLY webhook automation
"""

import os
import re
import json
import asyncio
import aiohttp
import discord
from discord import app_commands
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict
from datetime import datetime
import sys

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================
# ============================================

class Config:
    """Configuration"""
    bot_token: str = os.getenv("DISCORD_BOT_TOKEN", "")
    guild_id: str = os.getenv("DISCORD_GUILD_ID", "")
    qb_logs_category_id: str = os.getenv("QB_LOGS_CATEGORY_ID", "")
    fivem_path: str = os.getenv("FIVEM_RESOURCES_PATH", "")
    
    file_extensions = ['.lua', '.js', '.ts', '.json', '.cfg', '.txt', '.md', '.env', '.xml', '.yml', '.yaml', '.ini']
    skip_folders = ['node_modules', '.git', '__pycache__', 'cache', 'logs', '.idea', '.vscode', 'dist', 'build', 'target']
    webhook_patterns = [
        r'https://discord\.com/api/webhooks/\d+/[\w-]+',
        r'https://discordapp\.com/api/webhooks/\d+/[\w-]+',
    ]
    
    rate_limit_delay: float = 1.5
    channel_creation_delay: float = 1.5
    webhook_creation_delay: float = 1.0
    
    create_backups: bool = True
    backup_dir: str = "webhook_backups"
    output_dir: str = "webhook_output"
    
    def validate(self):
        """Validate configuration"""
        errors = []
        if not self.bot_token:
            errors.append("DISCORD_BOT_TOKEN required")
        if not self.guild_id:
            errors.append("DISCORD_GUILD_ID required")
        if not self.qb_logs_category_id:
            errors.append("QB_LOGS_CATEGORY_ID required (create category in Discord, copy ID)")
        if not self.fivem_path:
            errors.append("FIVEM_RESOURCES_PATH required")
        elif not Path(self.fivem_path).exists():
            errors.append(f"FiveM path does not exist: {self.fivem_path}")
        return len(errors) == 0, errors

config = Config()

# ============================================
# ============================================

class QBCoreScanner:
    """Scan QB-Core resources for webhooks"""
    
    def __init__(self):
        self.base_path = Path(config.fivem_path).resolve()
        self.webhook_pattern = re.compile('|'.join(config.webhook_patterns))
        self.webhooks_by_resource: Dict[str, Set[str]] = defaultdict(set)
        self.file_occurrences: Dict[str, List[tuple]] = defaultdict(list)
    
    async def scan(self, progress_callback=None) -> Dict[str, Set[str]]:
        """Scan and return webhooks grouped by resource"""
        files = list(self._get_files())
        
        if progress_callback:
            await progress_callback(message=f"📁 Found {len(files)} files to scan...")
        
        for idx, file_path in enumerate(files):
            self._scan_file(file_path)
            
            if progress_callback and idx % 500 == 0:
                await progress_callback(message=f"⏳ Scanned {idx}/{len(files)} files...")
        
        if progress_callback:
            total_webhooks = sum(len(urls) for urls in self.webhooks_by_resource.values())
            await progress_callback(message=f"✅ Found {len(self.webhooks_by_resource)} resources with {total_webhooks} webhooks")
        
        return self.webhooks_by_resource
    
    def _get_files(self):
        """Get all files to scan"""
        for root, dirs, files in os.walk(self.base_path, topdown=True):
            dirs[:] = [d for d in dirs if not any(skip in d.lower() for skip in config.skip_folders)]
            
            for file in files:
                if any(file.endswith(ext) for ext in config.file_extensions):
                    yield Path(root) / file
    
    def _scan_file(self, file_path: Path):
        """Scan a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for match in self.webhook_pattern.finditer(content):
                webhook_url = match.group(0)
                resource_name = self._get_resource_name(file_path)
                self.webhooks_by_resource[resource_name].add(webhook_url)
                self.file_occurrences[webhook_url].append((str(file_path), resource_name))
        except:
            pass
    
    def _get_resource_name(self, file_path: Path) -> str:
        """Extract QB-Core resource name"""
        try:
            relative = file_path.relative_to(self.base_path)
            parts = relative.parts
            
            if 'resources' in parts:
                idx = parts.index('resources')
                if idx + 1 < len(parts):
                    return parts[idx + 1].strip('[]')
            
            if len(parts) > 0:
                return parts[0].strip('[]')
            
            return 'unknown'
        except:
            return 'unknown'

# ============================================
# ============================================

class WebhookCreator:
    """Creates QB-Core log channels with webhooks"""
    
    def __init__(self, guild: discord.Guild, category_id: str):
        self.guild = guild
        self.category_id = int(category_id)
        self.webhook_mappings: Dict[str, str] = {}
        self.created_channels = []
    
    async def create_all(self, webhooks_by_resource: Dict[str, Set[str]], progress_callback=None):
        """Create QB-Core log channels and webhooks"""
        
        total_resources = len(webhooks_by_resource)
        
        if progress_callback:
            await progress_callback(message=f"🔨 Creating {total_resources} log channels...")
        
        for idx, (resource_name, old_webhooks) in enumerate(sorted(webhooks_by_resource.items())):
            channel_name = self._sanitize_name(f"{resource_name}-logs")
            
            category = self.guild.get_channel(self.category_id)
            if not category:
                if progress_callback:
                    await progress_callback(message=f"❌ Category not found! Check QB_LOGS_CATEGORY_ID")
                return False
            
            existing_channel = discord.utils.get(self.guild.text_channels, name=channel_name)
            if existing_channel and existing_channel.category_id == self.category_id:
                channel = existing_channel
                if progress_callback:
                    await progress_callback(message=f"♻️ Reusing
            else:
                channel = await self.guild.create_text_channel(
                    name=channel_name,
                    category=category
                )
                if progress_callback:
                    await progress_callback(message=f"✅ Created
                await asyncio.sleep(config.channel_creation_delay)
            
            self.created_channels.append({
                'name': channel_name,
                'id': channel.id,
                'resource': resource_name
            })
            
            webhooks_created = 0
            for webhook_idx, old_url in enumerate(sorted(old_webhooks), 1):
                webhook_name = f"{resource_name}"
                if len(old_webhooks) > 1:
                    webhook_name = f"{resource_name}-{webhook_idx}"
                
                webhook = await channel.create_webhook(name=webhook_name)
                self.webhook_mappings[old_url] = webhook.url
                webhooks_created += 1
                await asyncio.sleep(config.webhook_creation_delay)
            
            if progress_callback:
                await progress_callback(message=f"  └─ Created {webhooks_created} webhook(s) in
        
        return True
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize for Discord channel names"""
        name = name.lower()
        name = re.sub(r'[\s_]+', '-', name)
        name = re.sub(r'[^a-z0-9\-]', '', name)
        name = re.sub(r'-+', '-', name)
        name = name.strip('-')
        return name[:100] or 'channel'

# ============================================
# ============================================

class FileUpdater:
    """Update files with new webhook URLs"""
    
    def __init__(self):
        self.stats = {'files_updated': 0, 'replacements': 0, 'files_backed_up': 0}
        self.base_path = Path(config.fivem_path).resolve()
    
    async def update_all(self, webhook_mappings: Dict[str, str], file_occurrences: Dict[str, List[tuple]], progress_callback=None):
        """Update all files with new webhooks"""
        
        if config.create_backups:
            backup_dir = Path(config.backup_dir) / datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir.mkdir(parents=True, exist_ok=True)
            if progress_callback:
                await progress_callback(message=f"💾 Backup directory: {backup_dir}")
        else:
            backup_dir = None
        
        if progress_callback:
            await progress_callback(message=f"🔍 Searching for files to update...")
        
        files_to_update = self._find_all_files_with_webhooks(webhook_mappings)
        
        if not files_to_update:
            if progress_callback:
                await progress_callback(message=f"⚠️ No files found to update. Webhook URLs may already be current.")
            return
        
        if progress_callback:
            await progress_callback(message=f"📝 Found {len(files_to_update)} files to update...")
        
        for idx, file_path in enumerate(files_to_update):
            self._update_file(file_path, webhook_mappings, backup_dir)
            
            if progress_callback and (idx + 1) % 5 == 0:
                await progress_callback(message=f"⏳ Updated {idx + 1}/{len(files_to_update)} files...")
        
        if progress_callback:
            await progress_callback(message=f"✅ Updated {self.stats['files_updated']} files ({self.stats['replacements']} replacements)")
    
    def _find_all_files_with_webhooks(self, webhook_mappings: Dict[str, str]) -> List[Path]:
        """Scan all files to find those containing old webhook URLs"""
        files_with_webhooks = []
        
        for root, dirs, files in os.walk(self.base_path, topdown=True):
            dirs[:] = [d for d in dirs if not any(skip in d.lower() for skip in config.skip_folders)]
            
            for filename in files:
                if any(filename.endswith(ext) for ext in config.file_extensions):
                    file_path = Path(root) / filename
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        for old_url in webhook_mappings.keys():
                            if old_url in content:
                                files_with_webhooks.append(file_path)
                                break
                    except:
                        pass
        
        return files_with_webhooks
    
    def _update_file(self, file_path: Path, webhook_mappings: Dict[str, str], backup_dir: Optional[Path]):
        """Update a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original = content
            replacements = 0
            
            for old_url, new_url in webhook_mappings.items():
                if old_url in content:
                    occurrences = content.count(old_url)
                    content = content.replace(old_url, new_url)
                    replacements += occurrences
            
            if replacements > 0:
                if backup_dir and config.create_backups:
                    backup_file = backup_dir / file_path.name
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(backup_file, 'w', encoding='utf-8', errors='ignore') as f:
                        f.write(original)
                    self.stats['files_backed_up'] += 1
                
                with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(content)
                
                self.stats['files_updated'] += 1
                self.stats['replacements'] += replacements
        
        except Exception as e:
            pass

# ============================================
# ============================================

class ResultsSaver:
    """Save results to JSON"""
    
    @staticmethod
    async def save(webhook_mappings: Dict[str, str], channels: List[Dict], progress_callback=None):
        """Save webhook mappings"""
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'channels_created': channels,
            'webhook_mappings': webhook_mappings,
            'statistics': {
                'channels': len(channels),
                'webhooks': len(webhook_mappings)
            }
        }
        
        json_path = output_dir / 'webhook_mappings.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        guide_path = output_dir / 'webhook_guide.txt'
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("QB-CORE WEBHOOK MAPPINGS\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for channel in channels:
                f.write(f"\nChannel:
                f.write(f"Resource: {channel['resource']}\n")
                f.write(f"{'-' * 70}\n")
                
                for old_url, new_url in webhook_mappings.items():
                    f.write(f"Old: {old_url}\n")
                    f.write(f"New: {new_url}\n\n")
        
        if progress_callback:
            await progress_callback(message=f"💾 Saved results to {output_dir}/")

# ============================================
# ============================================

class QBWebhookBot(discord.Client):
    """Discord bot with slash commands"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        """Setup slash commands"""
        guild = discord.Object(id=int(config.guild_id))
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
    
    async def on_ready(self):
        """Bot is ready"""
        print(f"\n{'=' * 70}")
        print(f"  🤖 QB-CORE WEBHOOK BOT v9.0")
        print(f"{'=' * 70}\n")
        print(f"✅ Logged in as: {self.user}")
        print(f"✅ Guild ID: {config.guild_id}")
        print(f"✅ QB Logs Category: {config.qb_logs_category_id}")
        print(f"✅ FiveM Path: {config.fivem_path}")
        print()
        print(f"🎯 Use /scan-webhooks in Discord to start!")
        print(f"{'=' * 70}\n")

bot = QBWebhookBot()

# ============================================
# ============================================

@bot.tree.command(name="scan-webhooks", description="Scan QB-Core resources and create webhooks")
async def scan_webhooks(interaction: discord.Interaction):
    """Slash command to scan and create webhooks"""
    
    await interaction.response.defer(ephemeral=False)
    
    async def update_progress(message: str = None, embed: discord.Embed = None):
        """Update the user with progress"""
        try:
            if embed:
                await interaction.followup.send(embed=embed)
            elif message:
                await interaction.followup.send(message)
        except:
            pass
    
    try:
        await update_progress(message="🔍 **STEP 1/4: Scanning QB-Core Resources**")
        scanner = QBCoreScanner()
        webhooks_by_resource = await scanner.scan(update_progress)
        
        if not webhooks_by_resource:
            await update_progress(message="❌ No webhooks found in QB-Core resources!")
            return
        
        await update_progress(message="\n🔨 **STEP 2/4: Creating Channels & Webhooks**")
        creator = WebhookCreator(interaction.guild, config.qb_logs_category_id)
        success = await creator.create_all(webhooks_by_resource, update_progress)
        
        if not success:
            await update_progress(message="❌ Failed to create channels/webhooks!")
            return
        
        await update_progress(message="\n📝 **STEP 3/4: Updating Files**")
        updater = FileUpdater()
        await updater.update_all(creator.webhook_mappings, scanner.file_occurrences, update_progress)
        
        await update_progress(message="\n💾 **STEP 4/4: Saving Results**")
        await ResultsSaver.save(creator.webhook_mappings, creator.created_channels, update_progress)
        
        embed = discord.Embed(
            title="✅ QB-Core Webhook Setup Complete!",
            description="All webhooks have been created and files updated.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 Summary",
            value=f"```\n"
                  f"Channels Created: {len(creator.created_channels)}\n"
                  f"Webhooks Created: {len(creator.webhook_mappings)}\n"
                  f"Files Updated:    {updater.stats['files_updated']}\n"
                  f"Replacements:     {updater.stats['replacements']}\n"
                  f"```",
            inline=False
        )
        
        embed.add_field(
            name="📁 Output",
            value=f"Results saved to `{config.output_dir}/`\n"
                  f"Backups saved to `{config.backup_dir}/`",
            inline=False
        )
        
        embed.add_field(
            name="🚀 Next Steps",
            value="1. Check Discord channels for new webhooks\n"
                  "2. Restart your FiveM server\n"
                  "3. Test webhooks in-game",
            inline=False
        )
        
        await update_progress(embed=embed)
        
    except Exception as e:
        await update_progress(message=f"❌ **Error:** {str(e)}")
        import traceback
        print(traceback.format_exc())

@bot.tree.command(name="webhook-status", description="Check webhook bot status")
async def webhook_status(interaction: discord.Interaction):
    """Check bot status"""
    
    embed = discord.Embed(
        title="🤖 QB-Core Webhook Bot Status",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    category = interaction.guild.get_channel(int(config.qb_logs_category_id))
    category_status = "✅ Found" if category else "❌ Not Found"
    
    embed.add_field(
        name="Configuration",
        value=f"```\n"
              f"Guild:     {interaction.guild.name}\n"
              f"Category:  {category_status}\n"
              f"FiveM:     {config.fivem_path}\n"
              f"```",
        inline=False
    )
    
    if category:
        channels_in_category = len(category.channels)
        embed.add_field(
            name="QB-Core Logs Category",
            value=f"Name: `{category.name}`\n"
                  f"Channels: `{channels_in_category}`",
            inline=False
        )
    
    embed.add_field(
        name="Commands",
        value="`/scan-webhooks` - Scan and create webhooks\n"
              "`/webhook-status` - Check bot status",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ============================================
# ============================================

def main():
    """Main entry point"""
    
    print("\n🚀 Starting QB-Core Webhook Bot...\n")
    
    valid, errors = config.validate()
    if not valid:
        print("❌ Configuration Error!\n")
        for error in errors:
            print(f"  • {error}")
        print("\n📝 Required Environment Variables:")
        print("  • DISCORD_BOT_TOKEN")
        print("  • DISCORD_GUILD_ID")
        print("  • QB_LOGS_CATEGORY_ID")
        print("  • FIVEM_RESOURCES_PATH")
        print()
        return 1
    
    try:
        bot.run(config.bot_token)
    except KeyboardInterrupt:
        print("\n\n⚠️  Bot stopped by user")
        return 0
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
