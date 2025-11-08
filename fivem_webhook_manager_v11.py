#!/usr/bin/env python3
"""
QB-Core Webhook Bot v11.0 - Fixed Resource Detection
Discord bot with slash command to manage QB-Core webhooks

FIXES:
- Proper resource detection (webhooks go to correct channels)
- More aggressive webhook pattern matching
- Better file path parsing
- Scans literally everything
"""

import os
import re
import json
import asyncio
import discord
from discord import app_commands
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """Configuration"""
    bot_token: str = os.getenv("DISCORD_BOT_TOKEN", "")
    guild_id: str = os.getenv("DISCORD_GUILD_ID", "")
    qb_logs_category_id: str = os.getenv("QB_LOGS_CATEGORY_ID", "")
    fivem_path: str = os.getenv("FIVEM_RESOURCES_PATH", "")
    
    file_extensions = ['.lua', '.js', '.ts', '.jsx', '.tsx', '.json', '.cfg', '.config', 
                      '.txt', '.md', '.env', '.xml', '.yml', '.yaml', '.ini', '.toml']
    skip_folders = ['node_modules', '.git', '__pycache__', 'cache', 'logs', '.idea', 
                   '.vscode', 'dist', 'build', 'target', 'obj', 'bin']
    
    rate_limit_delay: float = 1.5
    channel_creation_delay: float = 1.5
    webhook_creation_delay: float = 1.0
    
    create_backups: bool = True
    backup_dir: str = "webhook_backups"
    output_dir: str = "webhook_output"
    
    def validate(self):
        errors = []
        if not self.bot_token:
            errors.append("DISCORD_BOT_TOKEN required")
        if not self.guild_id:
            errors.append("DISCORD_GUILD_ID required")
        if not self.qb_logs_category_id:
            errors.append("QB_LOGS_CATEGORY_ID required")
        if not self.fivem_path:
            errors.append("FIVEM_RESOURCES_PATH required")
        elif not Path(self.fivem_path).exists():
            errors.append(f"FiveM path does not exist: {self.fivem_path}")
        return len(errors) == 0, errors


config = Config()


class EnhancedScanner:
    """Ultra-aggressive webhook scanner with proper resource detection"""
    
    def __init__(self):
        self.base_path = Path(config.fivem_path).resolve()
        self.webhooks_by_resource: Dict[str, Set[str]] = defaultdict(set)
        self.file_occurrences: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self.scan_stats = {
            'files_scanned': 0,
            'webhooks_found': 0,
            'files_with_webhooks': 0,
            'resources_found': set()
        }
        
        self.webhook_url_pattern = re.compile(
            r'https?://(?:discord(?:app)?\.com|ptb\.discord\.com)/api/webhooks/\d+/[\w-]+',
            re.IGNORECASE
        )
        
        self.webhook_value_patterns = [
            re.compile(r'["\']webhook[_\s-]*url?["\']\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE | re.MULTILINE),
            re.compile(r'\bwebhook\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE | re.MULTILINE),
            re.compile(r'\bwebhook_?url\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE | re.MULTILINE),
            re.compile(r'\bwebhookurl\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE | re.MULTILINE),
            re.compile(r'webhook["\']?\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE | re.MULTILINE),
            re.compile(r'["\']url["\']\s*[:=]\s*["\'](https?://discord[^"\']+)["\']', re.IGNORECASE | re.MULTILINE),
        ]
    
    async def scan(self, progress_callback=None) -> Dict[str, Set[str]]:
        files = list(self._get_all_files())
        
        if progress_callback:
            await progress_callback(message=f"📁 Scanning {len(files)} files in {self.base_path}")
        
        for idx, file_path in enumerate(files):
            self._scan_file(file_path)
            
            if progress_callback and idx > 0 and idx % 500 == 0:
                await progress_callback(message=f"⏳ Progress: {idx}/{len(files)} files... ({len(self.webhooks_by_resource)} resources, {self.scan_stats['webhooks_found']} webhooks)")
        
        self.scan_stats['files_scanned'] = len(files)
        
        if progress_callback:
            await progress_callback(message=f"✅ Scan Complete!")
            await progress_callback(message=f"   📊 Files Scanned: {self.scan_stats['files_scanned']}")
            await progress_callback(message=f"   📊 Files with Webhooks: {self.scan_stats['files_with_webhooks']}")
            await progress_callback(message=f"   📊 Resources Found: {len(self.webhooks_by_resource)}")
            await progress_callback(message=f"   📊 Total Webhooks: {self.scan_stats['webhooks_found']}")
        
        return self.webhooks_by_resource
    
    def _get_all_files(self):
        """Get ALL files, no exceptions"""
        for root, dirs, files in os.walk(self.base_path, topdown=True, followlinks=False):
            dirs[:] = [d for d in dirs if not any(skip in d.lower() for skip in config.skip_folders)]
            
            for file in files:
                if any(file.lower().endswith(ext) for ext in config.file_extensions):
                    yield Path(root) / file
    
    def _scan_file(self, file_path: Path):
        """Scan file for webhooks with proper resource attribution"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            found_any = False
            resource_name = self._extract_resource_name(file_path)
            
            for match in self.webhook_url_pattern.finditer(content):
                webhook_url = match.group(0)
                if self._is_valid_webhook(webhook_url):
                    self.webhooks_by_resource[resource_name].add(webhook_url)
                    self.file_occurrences[webhook_url].append((str(file_path), resource_name))
                    self.scan_stats['webhooks_found'] += 1
                    self.scan_stats['resources_found'].add(resource_name)
                    found_any = True
            
            for pattern in self.webhook_value_patterns:
                for match in pattern.finditer(content):
                    webhook_url = match.group(1)
                    if self._is_valid_webhook(webhook_url):
                        self.webhooks_by_resource[resource_name].add(webhook_url)
                        self.file_occurrences[webhook_url].append((str(file_path), resource_name))
                        self.scan_stats['webhooks_found'] += 1
                        self.scan_stats['resources_found'].add(resource_name)
                        found_any = True
            
            if found_any:
                self.scan_stats['files_with_webhooks'] += 1
        
        except Exception as e:
            pass
    
    def _extract_resource_name(self, file_path: Path) -> str:
        """
        Extract resource name with proper hierarchy handling.
        This fixes the issue where webhooks were assigned to wrong resources.
        """
        try:
            relative = file_path.relative_to(self.base_path)
            parts = list(relative.parts)
            
            if not parts:
                return 'unknown'
            
            resource_name = None
            
            if 'resources' in parts:
                res_idx = parts.index('resources')
                if res_idx + 1 < len(parts):
                    resource_name = parts[res_idx + 1]
            
            if not resource_name and len(parts) >= 1:
                if parts[0].startswith('[') and parts[0].endswith(']'):
                    if len(parts) >= 2:
                        resource_name = parts[1]
                    else:
                        resource_name = parts[0]
                else:
                    resource_name = parts[0]
            
            if resource_name:
                resource_name = resource_name.strip('[]').strip()
                return resource_name if resource_name else 'unknown'
            
            return 'unknown'
        
        except Exception as e:
            return 'unknown'
    
    def _is_valid_webhook(self, url: str) -> bool:
        """Strict webhook validation"""
        if not url or len(url) < 50:
            return False
        
        url_lower = url.lower()
        if not any(domain in url_lower for domain in ['discord.com/api/webhooks/', 'discordapp.com/api/webhooks/']):
            return False
        
        parts = url.split('/')
        if len(parts) < 7:
            return False
        
        webhook_id = parts[-2]
        webhook_token = parts[-1]
        
        if not webhook_id.isdigit() or len(webhook_id) < 17:
            return False
        
        if len(webhook_token) < 50 or not all(c.isalnum() or c in '-_' for c in webhook_token):
            return False
        
        return True


class WebhookCreator:
    """Creates channels with proper resource mapping"""
    
    def __init__(self, guild: discord.Guild, category_id: str):
        self.guild = guild
        self.category_id = int(category_id)
        self.webhook_mappings: Dict[str, str] = {}
        self.created_channels = []
    
    async def create_all(self, webhooks_by_resource: Dict[str, Set[str]], progress_callback=None):
        total_resources = len(webhooks_by_resource)
        
        if progress_callback:
            await progress_callback(message=f"🔨 Creating {total_resources} channels (1 per resource)...")
        
        for idx, (resource_name, old_webhooks) in enumerate(sorted(webhooks_by_resource.items())):
            try:
                channel_name = self._sanitize_name(f"{resource_name}-logs")
                
                category = self.guild.get_channel(self.category_id)
                if not category:
                    if progress_callback:
                        await progress_callback(message=f"❌ Category not found!")
                    return False
                
                existing_channel = discord.utils.get(self.guild.text_channels, name=channel_name, category_id=self.category_id)
                
                if existing_channel:
                    channel = existing_channel
                    if progress_callback:
                        await progress_callback(message=f"♻️  [{idx+1}/{total_resources}] Reusing #{channel_name} ({len(old_webhooks)} webhooks)")
                else:
                    channel = await self.guild.create_text_channel(name=channel_name, category=category)
                    if progress_callback:
                        await progress_callback(message=f"✅ [{idx+1}/{total_resources}] Created #{channel_name} ({len(old_webhooks)} webhooks)")
                    await asyncio.sleep(config.channel_creation_delay)
                
                self.created_channels.append({
                    'name': channel_name,
                    'id': channel.id,
                    'resource': resource_name,
                    'webhook_count': len(old_webhooks)
                })
                
                for webhook_idx, old_url in enumerate(sorted(old_webhooks), 1):
                    webhook_name = f"{resource_name}" if len(old_webhooks) == 1 else f"{resource_name}-{webhook_idx}"
                    webhook = await channel.create_webhook(name=webhook_name)
                    self.webhook_mappings[old_url] = webhook.url
                    await asyncio.sleep(config.webhook_creation_delay)
            
            except discord.HTTPException as e:
                if progress_callback:
                    await progress_callback(message=f"⚠️  [{idx+1}/{total_resources}] Skipped {resource_name}: {str(e)}")
                continue
            except Exception as e:
                if progress_callback:
                    await progress_callback(message=f"⚠️  [{idx+1}/{total_resources}] Error with {resource_name}: {str(e)}")
                continue
        
        return True
    
    def _sanitize_name(self, name: str) -> str:
        name = name.lower()
        
        # Discord doesn't allow "discord" in channel names - replace it
        name = re.sub(r'\bdiscord\b', 'disc', name, flags=re.IGNORECASE)
        name = re.sub(r'\bclyde\b', 'assistant', name, flags=re.IGNORECASE)
        
        name = re.sub(r'[\s_]+', '-', name)
        name = re.sub(r'[^a-z0-9\-]', '', name)
        name = re.sub(r'-+', '-', name)
        name = name.strip('-')
        
        # Ensure it's not empty and within Discord's limits
        name = name[:100] if name else 'resource-logs'
        
        return name


class FileUpdater:
    """Updates files with new webhooks"""
    
    def __init__(self):
        self.stats = {'files_updated': 0, 'replacements': 0, 'files_backed_up': 0}
    
    async def update_all(self, webhook_mappings: Dict[str, str], file_occurrences: Dict[str, List[Tuple[str, str]]], progress_callback=None):
        if config.create_backups:
            backup_dir = Path(config.backup_dir) / datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir.mkdir(parents=True, exist_ok=True)
            if progress_callback:
                await progress_callback(message=f"💾 Backup: {backup_dir}")
        else:
            backup_dir = None
        
        files_to_update = set()
        for old_url in webhook_mappings.keys():
            for file_path, _ in file_occurrences.get(old_url, []):
                files_to_update.add(file_path)
        
        if progress_callback:
            await progress_callback(message=f"📝 Updating {len(files_to_update)} files...")
        
        for idx, file_path in enumerate(files_to_update):
            self._update_file(Path(file_path), webhook_mappings, backup_dir)
            
            if progress_callback and idx > 0 and idx % 25 == 0:
                await progress_callback(message=f"⏳ Progress: {idx}/{len(files_to_update)} files updated...")
        
        if progress_callback:
            await progress_callback(message=f"✅ Updated {self.stats['files_updated']} files ({self.stats['replacements']} replacements)")
    
    def _update_file(self, file_path: Path, webhook_mappings: Dict[str, str], backup_dir: Optional[Path]):
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
                    counter = 1
                    while backup_file.exists():
                        backup_file = backup_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                        counter += 1
                    
                    with open(backup_file, 'w', encoding='utf-8', errors='ignore') as f:
                        f.write(original)
                    self.stats['files_backed_up'] += 1
                
                with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(content)
                
                self.stats['files_updated'] += 1
                self.stats['replacements'] += replacements
        
        except Exception as e:
            pass


class ResultsSaver:
    """Save detailed results"""
    
    @staticmethod
    async def save(webhook_mappings: Dict[str, str], channels: List[Dict], file_occurrences: Dict[str, List[Tuple[str, str]]], scan_stats: Dict, progress_callback=None):
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'scan_statistics': {
                'files_scanned': scan_stats.get('files_scanned', 0),
                'files_with_webhooks': scan_stats.get('files_with_webhooks', 0),
                'resources_found': len(scan_stats.get('resources_found', set())),
                'total_webhooks': scan_stats.get('webhooks_found', 0)
            },
            'channels_created': channels,
            'webhook_mappings': webhook_mappings,
            'file_locations': {old_url: [(path, res) for path, res in locs] for old_url, locs in file_occurrences.items()}
        }
        
        json_path = output_dir / 'webhook_mappings.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        guide_path = output_dir / 'webhook_guide.txt'
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("QB-CORE WEBHOOK MAPPINGS - v11.0 Enhanced\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Scan Results:\n")
            f.write(f"  Files Scanned:        {data['scan_statistics']['files_scanned']}\n")
            f.write(f"  Files with Webhooks:  {data['scan_statistics']['files_with_webhooks']}\n")
            f.write(f"  Resources Found:      {data['scan_statistics']['resources_found']}\n")
            f.write(f"  Total Webhooks:       {data['scan_statistics']['total_webhooks']}\n\n")
            f.write("=" * 80 + "\n\n")
            
            for channel in sorted(channels, key=lambda x: x['resource']):
                f.write(f"\n{'=' * 80}\n")
                f.write(f"RESOURCE: {channel['resource']}\n")
                f.write(f"CHANNEL: #{channel['name']}\n")
                f.write(f"WEBHOOKS: {channel['webhook_count']}\n")
                f.write(f"{'=' * 80}\n\n")
                
                resource_webhooks = [(old, new) for old, new in webhook_mappings.items() 
                                    if any(res == channel['resource'] for _, res in file_occurrences.get(old, []))]
                
                for idx, (old_url, new_url) in enumerate(resource_webhooks, 1):
                    f.write(f"Webhook {idx}:\n")
                    f.write(f"  Old: {old_url}\n")
                    f.write(f"  New: {new_url}\n")
                    
                    files = file_occurrences.get(old_url, [])
                    if files:
                        f.write(f"  Found in {len(files)} file(s):\n")
                        for file_path, _ in files[:5]:
                            f.write(f"    - {Path(file_path).name}\n")
                        if len(files) > 5:
                            f.write(f"    ... and {len(files) - 5} more\n")
                    f.write("\n")
        
        if progress_callback:
            await progress_callback(message=f"💾 Results saved to {output_dir}/")


class QBWebhookBot(discord.Client):
    """Discord bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        guild = discord.Object(id=int(config.guild_id))
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
    
    async def on_ready(self):
        print(f"\n{'=' * 70}")
        print(f"  🤖 QB-CORE WEBHOOK BOT v11.0 - Fixed Resource Detection")
        print(f"{'=' * 70}\n")
        print(f"✅ Logged in as: {self.user}")
        
        guild = discord.utils.get(self.guilds, id=int(config.guild_id))
        print(f"✅ Guild: {guild.name if guild else config.guild_id}")
        print(f"✅ QB Logs Category: {config.qb_logs_category_id}")
        print(f"✅ FiveM Path: {config.fivem_path}")
        print(f"\n🎯 Use /scan-webhooks in Discord!")
        print(f"{'=' * 70}\n")


bot = QBWebhookBot()


@bot.tree.command(name="scan-webhooks", description="Scan QB-Core resources (v11 - Fixed resource detection)")
async def scan_webhooks(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    
    async def update_progress(message: str = None, embed: discord.Embed = None):
        try:
            if embed:
                await interaction.followup.send(embed=embed)
            elif message:
                await interaction.followup.send(message)
        except:
            pass
    
    try:
        await update_progress(message="🔍 **STEP 1/4: Scanning Resources**")
        await update_progress(message="⚡ v11 Enhanced: Proper resource detection + aggressive scanning")
        
        scanner = EnhancedScanner()
        webhooks_by_resource = await scanner.scan(update_progress)
        
        if not webhooks_by_resource:
            await update_progress(message="❌ No webhooks found!")
            return
        
        await update_progress(message="\n🔨 **STEP 2/4: Creating Channels**")
        creator = WebhookCreator(interaction.guild, config.qb_logs_category_id)
        success = await creator.create_all(webhooks_by_resource, update_progress)
        
        if not success:
            return
        
        await update_progress(message="\n📝 **STEP 3/4: Updating Files**")
        updater = FileUpdater()
        await updater.update_all(creator.webhook_mappings, scanner.file_occurrences, update_progress)
        
        await update_progress(message="\n💾 **STEP 4/4: Saving Results**")
        await ResultsSaver.save(creator.webhook_mappings, creator.created_channels, scanner.file_occurrences, scanner.scan_stats, update_progress)
        
        embed = discord.Embed(
            title="✅ Webhook Setup Complete! (v11 Fixed)",
            description="Enhanced scanning with proper resource detection",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📊 Scan Results",
            value=f"```\n"
                  f"Files Scanned:        {scanner.scan_stats['files_scanned']}\n"
                  f"Files with Webhooks:  {scanner.scan_stats['files_with_webhooks']}\n"
                  f"Resources Found:      {len(webhooks_by_resource)}\n"
                  f"Total Webhooks:       {scanner.scan_stats['webhooks_found']}\n"
                  f"```",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Actions Taken",
            value=f"```\n"
                  f"Channels Created:     {len(creator.created_channels)}\n"
                  f"New Webhooks:         {len(creator.webhook_mappings)}\n"
                  f"Files Updated:        {updater.stats['files_updated']}\n"
                  f"Replacements:         {updater.stats['replacements']}\n"
                  f"```",
            inline=False
        )
        
        if len(webhooks_by_resource) <= 10:
            resources_list = "\n".join([f"• {res} ({len(hooks)} webhooks)" for res, hooks in sorted(webhooks_by_resource.items())])
            embed.add_field(
                name="📦 Resources Found",
                value=resources_list[:1024],
                inline=False
            )
        
        embed.add_field(
            name="📁 Output",
            value=f"• `{config.output_dir}/webhook_mappings.json`\n"
                  f"• `{config.output_dir}/webhook_guide.txt`\n"
                  f"• `{config.backup_dir}/[timestamp]/`",
            inline=False
        )
        
        await update_progress(embed=embed)
        
    except Exception as e:
        await update_progress(message=f"❌ **Error:** {str(e)}")
        import traceback
        print(traceback.format_exc())


@bot.tree.command(name="webhook-status", description="Check bot status")
async def webhook_status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 QB-Core Webhook Bot v11.0",
        description="**FIXED:** Proper resource detection\n**ENHANCED:** More aggressive scanning",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    category = interaction.guild.get_channel(int(config.qb_logs_category_id))
    
    embed.add_field(
        name="Configuration",
        value=f"```\n"
              f"Guild:     {interaction.guild.name}\n"
              f"Category:  {'✅ Found' if category else '❌ Not Found'}\n"
              f"FiveM:     {config.fivem_path}\n"
              f"```",
        inline=False
    )
    
    if category:
        embed.add_field(
            name="Category Info",
            value=f"Name: `{category.name}`\nChannels: `{len(category.channels)}`",
            inline=False
        )
    
    embed.add_field(
        name="v11 Fixes",
        value="✅ Webhooks now go to CORRECT channels\n"
              "✅ Better resource name extraction\n"
              "✅ More file types scanned\n"
              "✅ Stricter webhook validation",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


def main():
    print("\n🚀 Starting QB-Core Webhook Bot v11.0...\n")
    
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
        return 1
    
    try:
        bot.run(config.bot_token)
    except KeyboardInterrupt:
        print("\n⚠️  Stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
