"""
Bot Cloning System
Allows users to clone the main bot with all plugins and features
"""

import os
import json
import logging
import asyncio
import shutil
from typing import Dict, List, Optional
from datetime import datetime
import aiofiles
from pyrogram import Client, filters
from Oneforall import app
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotCloner:
    """Handles cloning of bots and management of cloned bot instances"""
    
    def __init__(self, base_bot_token: str, storage_path: str = "./cloned_bots"):
        self.base_bot_token = base_bot_token
        self.storage_path = storage_path
        self.cloned_bots: Dict[str, dict] = {}
        self.bot_processes: Dict[str, asyncio.Task] = {}
        self.plugin_dirs = [
            'play', 'bot', 'admins', 'sudo', 
            'misc', 'security', 'tools'
        ]
        os.makedirs(storage_path, exist_ok=True)
        
    async def load_cloned_bots(self):
        """Load previously cloned bots from storage"""
        config_file = os.path.join(self.storage_path, "cloned_bots_config.json")
        try:
            if os.path.exists(config_file):
                async with aiofiles.open(config_file, 'r') as f:
                    content = await f.read()
                    self.cloned_bots = json.loads(content)
                logger.info(f"Loaded {len(self.cloned_bots)} cloned bots from storage")
        except Exception as e:
            logger.error(f"Error loading cloned bots: {e}")
            self.cloned_bots = {}
    
    async def save_cloned_bots(self):
        """Save cloned bots configuration to storage"""
        config_file = os.path.join(self.storage_path, "cloned_bots_config.json")
        try:
            async with aiofiles.open(config_file, 'w') as f:
                await f.write(json.dumps(self.cloned_bots, indent=2))
            logger.info("Cloned bots config saved successfully")
        except Exception as e:
            logger.error(f"Error saving cloned bots: {e}")
    
    async def clone_bot(self, user_id: str, bot_token: str, bot_name: str) -> Dict:
        """
        Clone the main bot for a user with all plugins and features
        
        Args:
            user_id: Telegram user ID
            bot_token: User's bot token
            bot_name: Name for the cloned bot
            
        Returns:
            Dictionary with cloning status and details
        """
        try:
            # Validate bot token format
            if not self._validate_token(bot_token):
                return {
                    "success": False,
                    "error": "Invalid bot token format. Use: token_id:token_hash"
                }
            
            # Check if user already has a cloned bot
            if user_id in self.cloned_bots:
                return {
                    "success": False,
                    "error": f"You already have a cloned bot: {self.cloned_bots[user_id]['bot_name']}. Delete it first using /deleteclone",
                    "existing_bot": self.cloned_bots[user_id]['bot_name']
                }
            
            # Create bot directory structure
            bot_dir = os.path.join(self.storage_path, f"bot_{user_id}")
            os.makedirs(bot_dir, exist_ok=True)
            
            logger.info(f"Creating cloned bot directory: {bot_dir}")
            
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
                "status": "active",
                "bot_dir": bot_dir,
                "database_dir": os.path.join(bot_dir, "data"),
                "plugins_dir": os.path.join(bot_dir, "plugins"),
                "plugin_count": 0,
                "last_restart": datetime.now().isoformat()
            }
            
            # Initialize bot data directory and database
            await self._initialize_database(bot_config["database_dir"])
            
            # Count loaded plugins
            plugin_count = await self._count_plugins(bot_config["plugins_dir"])
            bot_config["plugin_count"] = plugin_count
            
            # Store configuration
            self.cloned_bots[user_id] = bot_config
            await self.save_cloned_bots()
            
            logger.info(f"Successfully cloned bot for user {user_id} with {plugin_count} plugins")
            
            return {
                "success": True,
                "message": f"✅ Bot cloned successfully!",
                "bot_name": bot_name,
                "plugins_loaded": plugin_count,
                "bot_config": bot_config
            }
            
        except Exception as e:
            logger.error(f"Error cloning bot for user {user_id}: {e}")
            return {
                "success": False,
                "error": f"Error during cloning: {str(e)}"
            }
    
    async def _copy_all_plugins(self, bot_dir: str):
        """Copy all plugin directories to the cloned bot"""
        try:
            for plugin_dir in self.plugin_dirs:
                src = f"./Oneforall/plugins/{plugin_dir}"
                dst = os.path.join(bot_dir, "plugins", plugin_dir)
                
                if os.path.exists(src):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    logger.info(f"Copied {plugin_dir} plugins to {dst}")
                else:
                    logger.warning(f"Plugin source directory not found: {src}")
        except Exception as e:
            logger.error(f"Error copying plugins: {e}")
            raise
    
    async def _copy_plugin_init(self, bot_dir: str):
        """Copy plugin __init__.py file"""
        try:
            src = "./Oneforall/plugins/__init__.py"
            dst = os.path.join(bot_dir, "plugins", "__init__.py")
            
            if os.path.exists(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                logger.info(f"Copied plugins __init__.py")
        except Exception as e:
            logger.error(f"Error copying plugin init: {e}")
    
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
            
            logger.info(f"Database initialized at {db_file}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def _count_plugins(self, plugins_dir: str) -> int:
        """Count total number of plugin files loaded"""
        try:
            count = 0
            for root, dirs, files in os.walk(plugins_dir):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        count += 1
            return count
        except Exception as e:
            logger.error(f"Error counting plugins: {e}")
            return 0
    
    async def start_cloned_bot(self, user_id: str) -> Dict:
        """Start a cloned bot instance"""
        try:
            if user_id not in self.cloned_bots:
                return {
                    "success": False,
                    "error": "Bot not found for this user. Use /clone first"
                }
            
            bot_config = self.cloned_bots[user_id]
            
            # Check if already running
            if user_id in self.bot_processes and not self.bot_processes[user_id].done():
                return {
                    "success": False,
                    "error": f"Bot '{bot_config['bot_name']}' is already running"
                }
            
            # Start bot process
            task = asyncio.create_task(
                self._run_bot_instance(user_id, bot_config)
            )
            self.bot_processes[user_id] = task
            bot_config["status"] = "running"
            bot_config["last_restart"] = datetime.now().isoformat()
            await self.save_cloned_bots()
            
            logger.info(f"Started cloned bot for user {user_id}")
            
            return {
                "success": True,
                "message": f"✅ Bot '{bot_config['bot_name']}' started with {bot_config['plugin_count']} plugins"
            }
            
        except Exception as e:
            logger.error(f"Error starting cloned bot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _run_bot_instance(self, user_id: str, bot_config: Dict):
        """Run a cloned bot instance"""
        try:
            logger.info(f"Running bot instance for user {user_id}")
            
            # Keep bot running and monitor status
            while user_id in self.cloned_bots and self.cloned_bots[user_id]["status"] == "running":
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            logger.info(f"Bot instance {user_id} cancelled")
        except Exception as e:
            logger.error(f"Error in bot instance {user_id}: {e}")
            if user_id in self.cloned_bots:
                self.cloned_bots[user_id]["status"] = "error"
    
    async def stop_cloned_bot(self, user_id: str) -> Dict:
        """Stop a cloned bot instance"""
        try:
            if user_id not in self.cloned_bots:
                return {
                    "success": False,
                    "error": "Bot not found for this user"
                }
            
            if user_id not in self.bot_processes or self.bot_processes[user_id].done():
                self.cloned_bots[user_id]["status"] = "stopped"
                await self.save_cloned_bots()
                return {
                    "success": True,
                    "message": "Bot already stopped"
                }
            
            task = self.bot_processes[user_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self.bot_processes[user_id]
            self.cloned_bots[user_id]["status"] = "stopped"
            await self.save_cloned_bots()
            
            logger.info(f"Stopped cloned bot for user {user_id}")
            
            return {
                "success": True,
                "message": f"✅ Bot stopped successfully"
            }
            
        except Exception as e:
            logger.error(f"Error stopping cloned bot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_cloned_bot(self, user_id: str) -> Dict:
        """Delete a cloned bot and all its data"""
        try:
            if user_id not in self.cloned_bots:
                return {
                    "success": False,
                    "error": "Bot not found for this user"
                }
            
            bot_name = self.cloned_bots[user_id]["bot_name"]
            
            # Stop bot if running
            if user_id in self.bot_processes:
                await self.stop_cloned_bot(user_id)
            
            # Remove directory and all data
            bot_dir = self.cloned_bots[user_id]["bot_dir"]
            if os.path.exists(bot_dir):
                shutil.rmtree(bot_dir)
                logger.info(f"Deleted bot directory: {bot_dir}")
            
            # Remove from config
            del self.cloned_bots[user_id]
            await self.save_cloned_bots()
            
            logger.info(f"Deleted cloned bot for user {user_id}")
            
            return {
                "success": True,
                "message": f"✅ Bot '{bot_name}' and all its data deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting cloned bot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def restart_all_cloned_bots(self):
        """Restart all running cloned bots (called when main bot restarts)"""
        try:
            logger.info(f"Restarting all {len(self.cloned_bots)} cloned bots...")
            
            for user_id, bot_config in list(self.cloned_bots.items()):
                if bot_config["status"] == "running":
                    await self.stop_cloned_bot(user_id)
                    await asyncio.sleep(2)
                    await self.start_cloned_bot(user_id)
            
            logger.info("All cloned bots restarted successfully")
            
        except Exception as e:
            logger.error(f"Error restarting cloned bots: {e}")
    
    async def get_bot_status(self, user_id: str) -> Dict:
        """Get status of a cloned bot"""
        if user_id not in self.cloned_bots:
            return {
                "success": False,
                "error": "Bot not found for this user"
            }
        
        bot_config = self.cloned_bots[user_id]
        is_running = user_id in self.bot_processes and not self.bot_processes[user_id].done()
        
        return {
            "success": True,
            "bot_name": bot_config["bot_name"],
            "status": "running" if is_running else bot_config["status"],
            "created_at": bot_config["created_at"],
            "last_restart": bot_config.get("last_restart", "Never"),
            "plugins_loaded": bot_config.get("plugin_count", 0),
            "bot_dir": bot_config["bot_dir"]
        }
    
    async def list_all_bots(self) -> Dict:
        """List all cloned bots"""
        bots_list = []
        for user_id, bot_config in self.cloned_bots.items():
            is_running = user_id in self.bot_processes and not self.bot_processes[user_id].done()
            bots_list.append({
                "user_id": user_id,
                "bot_name": bot_config["bot_name"],
                "status": "🟢 Running" if is_running else "🔴 " + bot_config["status"],
                "plugins": bot_config.get("plugin_count", 0),
                "created_at": bot_config["created_at"]
            })
        
        return {
            "success": True,
            "total_bots": len(bots_list),
            "bots": bots_list
        }
    
    @staticmethod
    def _validate_token(token: str) -> bool:
        """Validate bot token format (token_id:token_hash)"""
        try:
            parts = token.split(":")
            return (
                len(parts) == 2 and 
                len(parts[0]) > 0 and 
                len(parts[1]) > 0 and
                parts[0].isdigit()
            )
        except:
            return False


# Initialize global cloner instance
cloner_instance: Optional[BotCloner] = None


def get_cloner(bot_token: str) -> BotCloner:
    """Get or create cloner instance"""
    global cloner_instance
    if cloner_instance is None:
        cloner_instance = BotCloner(bot_token)
    return cloner_instance


# Message handlers using @app.on_message decorators
async def register_clone_handlers(app: Client):
    """Register all clone command handlers with the bot"""
    
    cloner = get_cloner("")
    await cloner.load_cloned_bots()
    
    @app.on_message(filters.command("clone"))
    async def clone_command(client, message):
        """Handle /clone command"""
        try:
            user_id = str(message.from_user.id)
            args = message.command
            
            if len(args) < 3:
                await message.reply(
                    "❌ Usage: /clone <bot_token> <bot_name>\n\n"
                    "Example: /clone 123456789:ABCDEFGHIJKLMNOPqrstuvwxyz MyClonedBot"
                )
                return
            
            bot_token = args[1]
            bot_name = " ".join(args[2:])
            
            result = await cloner.clone_bot(user_id, bot_token, bot_name)
            
            if result["success"]:
                await cloner.start_cloned_bot(user_id)
                response = (
                    f"✅ {result['message']}\n"
                    f"🤖 Bot Name: {result['bot_name']}\n"
                    f"📦 Plugins Loaded: {result['plugins_loaded']}\n\n"
                    f"Your cloned bot is now running with all features!"
                )
            else:
                response = f"❌ {result['error']}"
            
            await message.reply(response)
        
        except Exception as e:
            logger.error(f"Error in clone command: {e}")
            await message.reply(f"❌ An error occurred: {str(e)}")
    
    @app.on_message(filters.command("clonestatus"))
    async def status_command(client, message):
        """Handle /clonestatus command"""
        try:
            user_id = str(message.from_user.id)
            result = await cloner.get_bot_status(user_id)
            
            if result["success"]:
                response = (
                    f"🤖 **Bot Status**\n"
                    f"Name: {result['bot_name']}\n"
                    f"Status: {result['status']}\n"
                    f"Plugins: {result['plugins_loaded']}\n"
                    f"Created: {result['created_at']}\n"
                    f"Last Restart: {result['last_restart']}"
                )
            else:
                response = f"❌ {result['error']}"
            
            await message.reply(response)
        
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await message.reply(f"❌ An error occurred: {str(e)}")
    
    @app.on_message(filters.command("deleteclone"))
    async def delete_command(client, message):
        """Handle /deleteclone command"""
        try:
            user_id = str(message.from_user.id)
            result = await cloner.delete_cloned_bot(user_id)
            
            response = (
                f"✅ {result['message']}" if result['success'] 
                else f"❌ {result['error']}"
            )
            
            await message.reply(response)
        
        except Exception as e:
            logger.error(f"Error in delete command: {e}")
            await message.reply(f"❌ An error occurred: {str(e)}")
    
    @app.on_message(filters.command("stopclone"))
    async def stop_command(client, message):
        """Handle /stopclone command"""
        try:
            user_id = str(message.from_user.id)
            result = await cloner.stop_cloned_bot(user_id)
            
            response = (
                f"✅ {result['message']}" if result['success'] 
                else f"❌ {result['error']}"
            )
            
            await message.reply(response)
        
        except Exception as e:
            logger.error(f"Error in stop command: {e}")
            await message.reply(f"❌ An error occurred: {str(e)}")
    
    @app.on_message(filters.command("startclone"))
    async def start_command(client, message):
        """Handle /startclone command"""
        try:
            user_id = str(message.from_user.id)
            result = await cloner.start_cloned_bot(user_id)
            
            response = (
                f"✅ {result['message']}" if result['success'] 
                else f"❌ {result['error']}"
            )
            
            await message.reply(response)
        
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await message.reply(f"❌ An error occurred: {str(e)}")
    
    @app.on_message(filters.command("listclones"))
    async def list_command(client, message):
        """Handle /listclones command"""
        try:
            result = await cloner.list_all_bots()
            
            if result["success"] and result["total_bots"] > 0:
                response = f"📊 **Total Cloned Bots: {result['total_bots']}**\n\n"
                for bot in result["bots"]:
                    response += (
                        f"🤖 {bot['bot_name']}\n"
                        f"   Status: {bot['status']}\n"
                        f"   Plugins: {bot['plugins']}\n"
                        f"   Created: {bot['created_at']}\n\n"
                    )
            else:
                response = "❌ No cloned bots found"
            
            await message.reply(response)
        
        except Exception as e:
            logger.error(f"Error in list command: {e}")
            await message.reply(f"❌ An error occurred: {str(e)}")
