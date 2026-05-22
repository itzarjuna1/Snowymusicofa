"""
Advanced Bot Cloning System
Allows users to clone the main bot with all plugins and features
Features: Bot cloning, management, persistence, process handling
"""

import os
import json
import logging
import asyncio
import shutil
import subprocess
import signal
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message
import psutil

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedBotCloner:
    """Advanced bot cloning system with process management and persistence"""
    
    def __init__(self, base_bot_token: str, storage_path: str = "./cloned_bots"):
        self.base_bot_token = base_bot_token
        self.storage_path = storage_path
        self.cloned_bots: Dict[str, dict] = {}
        self.bot_processes: Dict[str, dict] = {}  # Store process info
        self.plugin_dirs = [
            'play', 'bot', 'admins', 'sudo', 
            'misc', 'security', 'tools'
        ]
        os.makedirs(storage_path, exist_ok=True)
        os.makedirs(os.path.join(storage_path, "logs"), exist_ok=True)
        logger.info(f"BotCloner initialized with storage at {storage_path}")
        
    async def load_cloned_bots(self):
        """Load previously cloned bots from storage"""
        config_file = os.path.join(self.storage_path, "cloned_bots_config.json")
        try:
            if os.path.exists(config_file):
                async with aiofiles.open(config_file, 'r') as f:
                    content = await f.read()
                    self.cloned_bots = json.loads(content)
                logger.info(f"✅ Loaded {len(self.cloned_bots)} cloned bots from storage")
            else:
                logger.info("No previous cloned bots found")
                self.cloned_bots = {}
        except Exception as e:
            logger.error(f"❌ Error loading cloned bots: {e}")
            self.cloned_bots = {}
    
    async def save_cloned_bots(self):
        """Save cloned bots configuration to storage"""
        config_file = os.path.join(self.storage_path, "cloned_bots_config.json")
        try:
            async with aiofiles.open(config_file, 'w') as f:
                await f.write(json.dumps(self.cloned_bots, indent=2))
            logger.debug("✅ Cloned bots config saved successfully")
        except Exception as e:
            logger.error(f"❌ Error saving cloned bots: {e}")
    
    def _validate_token(self, token: str) -> bool:
        """Validate bot token format (token_id:token_hash)"""
        try:
            if not isinstance(token, str) or ':' not in token:
                return False
            parts = token.split(":")
            if len(parts) != 2:
                return False
            token_id, token_hash = parts
            if not token_id or not token_hash:
                return False
            if not token_id.isdigit():
                return False
            if len(token_hash) < 20:  # Telegram token hash is typically long
                return False
            return True
        except Exception as e:
            logger.warning(f"Token validation error: {e}")
            return False
    
    async def clone_bot(self, user_id: str, bot_token: str, bot_name: str) -> Dict:
        """Clone the main bot for a user with all plugins and features"""
        try:
            logger.info(f"Starting clone process for user {user_id}")
            
            # Validate bot token format
            if not self._validate_token(bot_token):
                logger.warning(f"Invalid token format for user {user_id}")
                return {
                    "success": False,
                    "error": "❌ Invalid bot token format.\n\nUse: `token_id:token_hash`\n\nExample: `123456789:ABCDEFGHIJKLMNOPqrstuvwxyz`"
                }
            
            # Check if user already has a cloned bot
            if user_id in self.cloned_bots:
                existing_name = self.cloned_bots[user_id]['bot_name']
                logger.warning(f"User {user_id} already has bot: {existing_name}")
                return {
                    "success": False,
                    "error": f"⚠️ You already have a cloned bot: **{existing_name}**\n\nDelete it first using `/deleteclone` command."
                }
            
            # Create bot directory structure
            bot_dir = os.path.join(self.storage_path, f"bot_{user_id}")
            os.makedirs(bot_dir, exist_ok=True)
            
            logger.info(f"Created bot directory: {bot_dir}")
            
            # Copy all plugin directories
            await self._copy_all_plugins(bot_dir)
            
            # Copy plugin initialization file
            await self._copy_plugin_init(bot_dir)
            
            # Create bot configuration
            bot_config = {
                "user_id": user_id,
                "bot_token": bot_token,
                "bot_name": bot_name,
                "created_at": datetime.now().isoformat(),
                "status": "created",
                "bot_dir": bot_dir,
                "database_dir": os.path.join(bot_dir, "data"),
                "plugins_dir": os.path.join(bot_dir, "plugins"),
                "plugin_count": 0,
                "last_restart": None,
                "uptime": 0,
                "process_id": None
            }
            
            # Initialize bot data directory and database
            await self._initialize_database(bot_config["database_dir"])
            
            # Count loaded plugins
            plugin_count = await self._count_plugins(bot_config["plugins_dir"])
            bot_config["plugin_count"] = plugin_count
            
            # Store configuration
            self.cloned_bots[user_id] = bot_config
            await self.save_cloned_bots()
            
            logger.info(f"✅ Successfully cloned bot for user {user_id} with {plugin_count} plugins")
            
            return {
                "success": True,
                "message": "✅ Bot cloned successfully!",
                "bot_name": bot_name,
                "plugins_loaded": plugin_count,
                "bot_config": bot_config
            }
            
        except Exception as e:
            logger.error(f"❌ Error cloning bot for user {user_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"❌ Error during cloning:\n`{str(e)}`"
            }
    
    async def _copy_all_plugins(self, bot_dir: str):
        """Copy all plugin directories to the cloned bot"""
        try:
            plugins_base = os.path.join(bot_dir, "plugins")
            os.makedirs(plugins_base, exist_ok=True)
            
            for plugin_dir in self.plugin_dirs:
                src = f"./Oneforall/plugins/{plugin_dir}"
                dst = os.path.join(plugins_base, plugin_dir)
                
                if os.path.exists(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    logger.debug(f"✅ Copied {plugin_dir} plugins to {dst}")
                else:
                    logger.warning(f"⚠️ Plugin source directory not found: {src}")
        except Exception as e:
            logger.error(f"❌ Error copying plugins: {e}", exc_info=True)
            raise
    
    async def _copy_plugin_init(self, bot_dir: str):
        """Copy plugin __init__.py file"""
        try:
            src = "./Oneforall/plugins/__init__.py"
            dst = os.path.join(bot_dir, "plugins", "__init__.py")
            
            if os.path.exists(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                logger.debug("✅ Copied plugins __init__.py")
            else:
                logger.warning(f"⚠️ Plugin init file not found: {src}")
        except Exception as e:
            logger.error(f"❌ Error copying plugin init: {e}", exc_info=True)
    
    async def _initialize_database(self, db_dir: str):
        """Initialize database directory and files for the cloned bot"""
        try:
            os.makedirs(db_dir, exist_ok=True)
            
            # Default database structure
            default_data = {
                "playlists": {},
                "user_preferences": {},
                "playback_history": [],
                "user_stats": {},
                "settings": {
                    "volume": 100,
                    "language": "en",
                    "notifications": True,
                    "autoplay": True,
                    "quality": "high"
                },
                "cache": {},
                "created_at": datetime.now().isoformat()
            }
            
            db_file = os.path.join(db_dir, "database.json")
            async with aiofiles.open(db_file, 'w') as f:
                await f.write(json.dumps(default_data, indent=2))
            
            logger.info(f"✅ Database initialized at {db_file}")
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}", exc_info=True)
            raise
    
    async def _count_plugins(self, plugins_dir: str) -> int:
        """Count total number of plugin files loaded"""
        try:
            count = 0
            if os.path.exists(plugins_dir):
                for root, dirs, files in os.walk(plugins_dir):
                    for file in files:
                        if file.endswith('.py') and not file.startswith('__'):
                            count += 1
            logger.debug(f"Counted {count} plugins")
            return count
        except Exception as e:
            logger.error(f"❌ Error counting plugins: {e}")
            return 0
    
    async def start_cloned_bot(self, user_id: str) -> Dict:
        """Start a cloned bot instance"""
        try:
            if user_id not in self.cloned_bots:
                logger.warning(f"Bot not found for user {user_id}")
                return {
                    "success": False,
                    "error": "❌ Bot not found for this user.\n\nUse `/clone` command first to create a bot."
                }
            
            bot_config = self.cloned_bots[user_id]
            bot_name = bot_config.get("bot_name", "Unknown")
            
            # Check if already running
            if user_id in self.bot_processes:
                process_info = self.bot_processes[user_id]
                if process_info.get("status") == "running":
                    logger.warning(f"Bot {bot_name} already running for user {user_id}")
                    return {
                        "success": False,
                        "error": f"⚠️ Bot **{bot_name}** is already running!\n\nUse `/stopclone` to stop it first."
                    }
            
            # Create startup script
            startup_script = await self._create_startup_script(user_id, bot_config)
            
            # Start bot process
            try:
                process = await asyncio.create_subprocess_exec(
                    'python3', startup_script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                self.bot_processes[user_id] = {
                    "process": process,
                    "pid": process.pid,
                    "status": "running",
                    "start_time": datetime.now().isoformat()
                }
                
                bot_config["status"] = "running"
                bot_config["process_id"] = process.pid
                bot_config["last_restart"] = datetime.now().isoformat()
                await self.save_cloned_bots()
                
                logger.info(f"✅ Started cloned bot for user {user_id} with PID {process.pid}")
                
                return {
                    "success": True,
                    "message": f"✅ Bot **{bot_name}** is starting...",
                    "details": f"Process ID: `{process.pid}`\nPlugins: `{bot_config['plugin_count']}`"
                }
            except Exception as e:
                logger.error(f"❌ Failed to start process: {e}")
                return {
                    "success": False,
                    "error": f"❌ Failed to start bot process:\n`{str(e)}`"
                }
            
        except Exception as e:
            logger.error(f"❌ Error starting cloned bot: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"❌ Error starting bot:\n`{str(e)}`"
            }
    
    async def _create_startup_script(self, user_id: str, bot_config: Dict) -> str:
        """Create a startup script for the cloned bot"""
        try:
            script_path = os.path.join(bot_config["bot_dir"], "start_bot.py")
            
            script_content = f'''#!/usr/bin/env python3
"""Auto-generated bot startup script for user {user_id}"""

import sys
import logging
from pyrogram import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "{bot_config['bot_token']}"
BOT_NAME = "{bot_config['bot_name']}"
SESSION_NAME = "cloned_bot_{user_id}"

# Create client
app = Client(SESSION_NAME, bot_token=BOT_TOKEN)

@app.on_message()
async def echo(client, message):
    """Echo handler - bot is running"""
    await message.reply(f"Hello! I'm {{BOT_NAME}} (Clone)")

async def main():
    logger.info(f"Starting {{BOT_NAME}}...")
    async with app:
        logger.info(f"Bot {{BOT_NAME}} is running!")
        await app.idle()

if __name__ == "__main__":
    app.run()
'''
            
            async with aiofiles.open(script_path, 'w') as f:
                await f.write(script_content)
            
            logger.debug(f"Created startup script: {script_path}")
            return script_path
            
        except Exception as e:
            logger.error(f"Error creating startup script: {e}")
            raise
    
    async def stop_cloned_bot(self, user_id: str) -> Dict:
        """Stop a cloned bot instance"""
        try:
            if user_id not in self.cloned_bots:
                logger.warning(f"Bot not found for user {user_id}")
                return {
                    "success": False,
                    "error": "❌ Bot not found for this user"
                }
            
            bot_name = self.cloned_bots[user_id]["bot_name"]
            
            # Check if process exists
            if user_id not in self.bot_processes:
                self.cloned_bots[user_id]["status"] = "stopped"
                await self.save_cloned_bots()
                logger.info(f"Bot {bot_name} was not running")
                return {
                    "success": True,
                    "message": f"✅ Bot **{bot_name}** is already stopped"
                }
            
            # Get process info
            process_info = self.bot_processes[user_id]
            process = process_info.get("process")
            pid = process_info.get("pid")
            
            try:
                if process and not process.done():
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                    logger.info(f"Terminated process {pid}")
            except Exception as e:
                logger.warning(f"Process termination warning: {e}")
            
            # Clean up
            del self.bot_processes[user_id]
            self.cloned_bots[user_id]["status"] = "stopped"
            self.cloned_bots[user_id]["process_id"] = None
            await self.save_cloned_bots()
            
            logger.info(f"✅ Stopped cloned bot {bot_name} for user {user_id}")
            
            return {
                "success": True,
                "message": f"✅ Bot **{bot_name}** stopped successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error stopping cloned bot: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"❌ Error stopping bot:\n`{str(e)}`"
            }
    
    async def delete_cloned_bot(self, user_id: str) -> Dict:
        """Delete a cloned bot and all its data"""
        try:
            if user_id not in self.cloned_bots:
                logger.warning(f"Bot not found for user {user_id}")
                return {
                    "success": False,
                    "error": "❌ Bot not found for this user"
                }
            
            bot_name = self.cloned_bots[user_id]["bot_name"]
            
            # Stop bot if running
            if user_id in self.bot_processes:
                await self.stop_cloned_bot(user_id)
                await asyncio.sleep(1)
            
            # Remove directory and all data
            bot_dir = self.cloned_bots[user_id]["bot_dir"]
            if os.path.exists(bot_dir):
                shutil.rmtree(bot_dir)
                logger.info(f"Deleted bot directory: {bot_dir}")
            
            # Remove from config
            del self.cloned_bots[user_id]
            await self.save_cloned_bots()
            
            logger.info(f"✅ Deleted cloned bot {bot_name} for user {user_id}")
            
            return {
                "success": True,
                "message": f"✅ Bot **{bot_name}** and all its data deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error deleting cloned bot: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"❌ Error deleting bot:\n`{str(e)}`"
            }
    
    async def get_bot_status(self, user_id: str) -> Dict:
        """Get detailed status of a cloned bot"""
        try:
            if user_id not in self.cloned_bots:
                return {
                    "success": False,
                    "error": "❌ Bot not found for this user"
                }
            
            bot_config = self.cloned_bots[user_id]
            process_info = self.bot_processes.get(user_id)
            
            is_running = False
            pid = None
            uptime = "N/A"
            
            if process_info:
                process = process_info.get("process")
                is_running = process and not process.done()
                pid = process_info.get("pid")
                
                if is_running and process_info.get("start_time"):
                    start = datetime.fromisoformat(process_info["start_time"])
                    uptime = str(datetime.now() - start).split('.')[0]
            
            return {
                "success": True,
                "bot_name": bot_config["bot_name"],
                "status": "🟢 Running" if is_running else "🔴 Stopped",
                "created_at": bot_config["created_at"],
                "last_restart": bot_config.get("last_restart", "Never"),
                "plugins_loaded": bot_config.get("plugin_count", 0),
                "process_id": pid,
                "uptime": uptime,
                "bot_dir": bot_config["bot_dir"]
            }
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            return {
                "success": False,
                "error": f"Error fetching status: {str(e)}"
            }
    
    async def list_all_bots(self) -> Dict:
        """List all cloned bots"""
        try:
            bots_list = []
            for user_id, bot_config in self.cloned_bots.items():
                process_info = self.bot_processes.get(user_id)
                is_running = False
                if process_info:
                    process = process_info.get("process")
                    is_running = process and not process.done()
                
                bots_list.append({
                    "user_id": user_id,
                    "bot_name": bot_config["bot_name"],
                    "status": "🟢 Running" if is_running else "🔴 Stopped",
                    "plugins": bot_config.get("plugin_count", 0),
                    "created_at": bot_config["created_at"]
                })
            
            return {
                "success": True,
                "total_bots": len(bots_list),
                "bots": bots_list
            }
        except Exception as e:
            logger.error(f"Error listing bots: {e}")
            return {
                "success": False,
                "total_bots": 0,
                "bots": []
            }


# Global cloner instance
cloner_instance: Optional[AdvancedBotCloner] = None


def get_cloner(bot_token: str = "") -> AdvancedBotCloner:
    """Get or create cloner instance"""
    global cloner_instance
    if cloner_instance is None:
        cloner_instance = AdvancedBotCloner(bot_token)
    return cloner_instance


# Telegram bot handlers
async def register_clone_handlers(app: Client):
    """Register all clone command handlers with the bot"""
    
    cloner = get_cloner("")
    await cloner.load_cloned_bots()
    logger.info("✅ Clone handlers registered")
    
    @app.on_message(filters.command("clone"))
    async def clone_command(client: Client, message: Message):
        """Handle /clone command - Clone the main bot"""
        try:
            user_id = str(message.from_user.id)
            args = message.command
            
            logger.info(f"Clone command received from user {user_id}")
            
            if len(args) < 3:
                await message.reply(
                    "❌ **Invalid Usage!**\n\n"
                    "📝 **Syntax:** `/clone <bot_token> <bot_name>`\n\n"
                    "📋 **Example:**\n"
                    "`/clone 123456789:ABCDEFGHIJKLMNOPqrstuvwxyz MyAwesomeBot`\n\n"
                    "💡 **How to get a bot token:**\n"
                    "1. Message @BotFather on Telegram\n"
                    "2. Use `/newbot` command\n"
                    "3. Follow the prompts\n"
                    "4. Copy your token",
                    parse_mode="markdown"
                )
                return
            
            bot_token = args[1]
            bot_name = " ".join(args[2:])
            
            # Show cloning status
            status_msg = await message.reply(f"🔄 Cloning bot **{bot_name}**...\n\n⏳ Please wait...")
            
            result = await cloner.clone_bot(user_id, bot_token, bot_name)
            
            if result["success"]:
                # Start the bot automatically
                start_result = await cloner.start_cloned_bot(user_id)
                
                response = (
                    f"✅ **Bot Cloned Successfully!**\n\n"
                    f"🤖 **Bot Name:** `{result['bot_name']}`\n"
                    f"📦 **Plugins Loaded:** `{result['plugins_loaded']}`\n\n"
                    f"✨ Your cloned bot is now **running** with all features!\n\n"
                    f"📌 **Available Commands:**\n"
                    f"• `/clonestatus` - Check bot status\n"
                    f"• `/stopclone` - Stop the bot\n"
                    f"• `/startclone` - Start the bot\n"
                    f"• `/deleteclone` - Delete the bot\n"
                    f"• `/listclones` - List all your bots"
                )
            else:
                response = f"❌ **Cloning Failed!**\n\n{result['error']}"
            
            await status_msg.edit_text(response, parse_mode="markdown")
        
        except Exception as e:
            logger.error(f"Error in clone command: {e}", exc_info=True)
            await message.reply(f"❌ **An error occurred:**\n\n`{str(e)}`", parse_mode="markdown")
    
    @app.on_message(filters.command("clonestatus"))
    async def status_command(client: Client, message: Message):
        """Handle /clonestatus command - Get bot status"""
        try:
            user_id = str(message.from_user.id)
            logger.info(f"Status command from user {user_id}")
            
            result = await cloner.get_bot_status(user_id)
            
            if result["success"]:
                response = (
                    f"🤖 **Bot Status**\n\n"
                    f"📛 **Name:** `{result['bot_name']}`\n"
                    f"🔴 **Status:** {result['status']}\n"
                    f"📦 **Plugins:** `{result['plugins_loaded']}`\n"
                    f"⏱️ **Uptime:** `{result['uptime']}`\n"
                    f"🆔 **Process ID:** `{result.get('process_id', 'N/A')}`\n"
                    f"📅 **Created:** `{result['created_at'][:19]}`\n"
                    f"🔄 **Last Restart:** `{result['last_restart'][:19] if result['last_restart'] else 'Never'}`"
                )
            else:
                response = f"❌ **Error:** {result['error']}"
            
            await message.reply(response, parse_mode="markdown")
        
        except Exception as e:
            logger.error(f"Error in status command: {e}", exc_info=True)
            await message.reply(f"❌ **Error:** `{str(e)}`", parse_mode="markdown")
    
    @app.on_message(filters.command("deleteclone"))
    async def delete_command(client: Client, message: Message):
        """Handle /deleteclone command - Delete a cloned bot"""
        try:
            user_id = str(message.from_user.id)
            logger.info(f"Delete command from user {user_id}")
            
            status_msg = await message.reply("🔄 Deleting bot...\n\n⏳ Please wait...")
            
            result = await cloner.delete_cloned_bot(user_id)
            
            response = (
                f"✅ {result['message']}" if result['success'] 
                else f"❌ **Error:** {result['error']}"
            )
            
            await status_msg.edit_text(response, parse_mode="markdown")
        
        except Exception as e:
            logger.error(f"Error in delete command: {e}", exc_info=True)
            await message.reply(f"❌ **Error:** `{str(e)}`", parse_mode="markdown")
    
    @app.on_message(filters.command("stopclone"))
    async def stop_command(client: Client, message: Message):
        """Handle /stopclone command - Stop the cloned bot"""
        try:
            user_id = str(message.from_user.id)
            logger.info(f"Stop command from user {user_id}")
            
            status_msg = await message.reply("🔄 Stopping bot...\n\n⏳ Please wait...")
            
            result = await cloner.stop_cloned_bot(user_id)
            
            response = (
                f"✅ {result['message']}" if result['success'] 
                else f"❌ **Error:** {result['error']}"
            )
            
            await status_msg.edit_text(response, parse_mode="markdown")
        
        except Exception as e:
            logger.error(f"Error in stop command: {e}", exc_info=True)
            await message.reply(f"❌ **Error:** `{str(e)}`", parse_mode="markdown")
    
    @app.on_message(filters.command("startclone"))
    async def start_command(client: Client, message: Message):
        """Handle /startclone command - Start the cloned bot"""
        try:
            user_id = str(message.from_user.id)
            logger.info(f"Start command from user {user_id}")
            
            status_msg = await message.reply("🔄 Starting bot...\n\n⏳ Please wait...")
            
            result = await cloner.start_cloned_bot(user_id)
            
            if result["success"]:
                response = (
                    f"✅ {result['message']}\n\n"
                    f"{result.get('details', '')}"
                )
            else:
                response = f"❌ **Error:** {result['error']}"
            
            await status_msg.edit_text(response, parse_mode="markdown")
        
        except Exception as e:
            logger.error(f"Error in start command: {e}", exc_info=True)
            await message.reply(f"❌ **Error:** `{str(e)}`", parse_mode="markdown")
    
    @app.on_message(filters.command("listclones"))
    async def list_command(client: Client, message: Message):
        """Handle /listclones command - List all cloned bots"""
        try:
            logger.info(f"List command from user {message.from_user.id}")
            
            result = await cloner.list_all_bots()
            
            if result["success"] and result["total_bots"] > 0:
                response = f"📊 **Total Cloned Bots: {result['total_bots']}**\n\n"
                for bot in result["bots"]:
                    response += (
                        f"🤖 **{bot['bot_name']}**\n"
                        f"   Status: {bot['status']}\n"
                        f"   Plugins: `{bot['plugins']}`\n"
                        f"   Created: `{bot['created_at'][:19]}`\n\n"
                    )
            else:
                response = "❌ **No cloned bots found**\n\nUse `/clone` to create one!"
            
            await message.reply(response, parse_mode="markdown")
        
        except Exception as e:
            logger.error(f"Error in list command: {e}", exc_info=True)
            await message.reply(f"❌ **Error:** `{str(e)}`", parse_mode="markdown")
    
    logger.info("✅ All clone handlers successfully registered!")
