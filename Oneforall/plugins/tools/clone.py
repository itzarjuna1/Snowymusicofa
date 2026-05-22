"""
Bot Cloning System - Simple & Working
"""

import os
import json
import logging
import asyncio
import shutil
from typing import Dict, Optional
from datetime import datetime
import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotCloner:
    """Simple bot cloning system"""
    
    def __init__(self, storage_path: str = "./cloned_bots"):
        self.storage_path = storage_path
        self.cloned_bots: Dict[str, dict] = {}
        self.plugin_dirs = ['play', 'bot', 'admins', 'sudo', 'misc', 'security', 'tools']
        os.makedirs(storage_path, exist_ok=True)
        
    async def load_config(self):
        """Load saved bots"""
        config_file = os.path.join(self.storage_path, "bots.json")
        try:
            if os.path.exists(config_file):
                async with aiofiles.open(config_file, 'r') as f:
                    content = await f.read()
                    self.cloned_bots = json.loads(content)
                logger.info(f"✅ Loaded {len(self.cloned_bots)} bots")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.cloned_bots = {}
    
    async def save_config(self):
        """Save bots config"""
        config_file = os.path.join(self.storage_path, "bots.json")
        try:
            async with aiofiles.open(config_file, 'w') as f:
                await f.write(json.dumps(self.cloned_bots, indent=2))
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def validate_token(self, token: str) -> bool:
        """Validate token format"""
        try:
            if ':' not in token:
                return False
            parts = token.split(':')
            if len(parts) != 2:
                return False
            return len(parts[0]) > 0 and len(parts[1]) > 20
        except:
            return False
    
    async def clone_bot(self, user_id: str, bot_token: str, bot_name: str) -> Dict:
        """Clone a bot"""
        try:
            # Validate
            if not self.validate_token(bot_token):
                return {"success": False, "error": "❌ Invalid token format!\n\nFormat: `token_id:token_hash`"}
            
            if user_id in self.cloned_bots:
                return {"success": False, "error": f"❌ You already have a bot! Delete it first with /deleteclone"}
            
            # Create directory
            bot_dir = os.path.join(self.storage_path, f"bot_{user_id}")
            os.makedirs(bot_dir, exist_ok=True)
            
            # Copy plugins
            plugins_dir = os.path.join(bot_dir, "plugins")
            os.makedirs(plugins_dir, exist_ok=True)
            
            for plugin_dir in self.plugin_dirs:
                src = f"./Oneforall/plugins/{plugin_dir}"
                dst = os.path.join(plugins_dir, plugin_dir)
                if os.path.exists(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
            
            # Count plugins
            plugin_count = 0
            for root, dirs, files in os.walk(plugins_dir):
                for f in files:
                    if f.endswith('.py') and not f.startswith('__'):
                        plugin_count += 1
            
            # Save bot config
            self.cloned_bots[user_id] = {
                "token": bot_token,
                "name": bot_name,
                "created": datetime.now().isoformat(),
                "plugins": plugin_count,
                "status": "created",
                "dir": bot_dir
            }
            
            await self.save_config()
            
            return {
                "success": True,
                "message": f"✅ Bot **{bot_name}** cloned!",
                "plugins": plugin_count
            }
        except Exception as e:
            logger.error(f"Clone error: {e}")
            return {"success": False, "error": f"❌ Error: {str(e)}"}
    
    async def delete_bot(self, user_id: str) -> Dict:
        """Delete a bot"""
        try:
            if user_id not in self.cloned_bots:
                return {"success": False, "error": "❌ No bot found!"}
            
            bot_dir = self.cloned_bots[user_id]["dir"]
            if os.path.exists(bot_dir):
                shutil.rmtree(bot_dir)
            
            del self.cloned_bots[user_id]
            await self.save_config()
            
            return {"success": True, "message": "✅ Bot deleted!"}
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"success": False, "error": f"❌ Error: {str(e)}"}
    
    async def get_status(self, user_id: str) -> Dict:
        """Get bot status"""
        try:
            if user_id not in self.cloned_bots:
                return {"success": False, "error": "❌ No bot found!"}
            
            bot = self.cloned_bots[user_id]
            return {
                "success": True,
                "name": bot["name"],
                "status": bot["status"],
                "plugins": bot["plugins"],
                "created": bot["created"]
            }
        except Exception as e:
            return {"success": False, "error": f"❌ Error: {str(e)}"}
    
    async def list_bots(self) -> Dict:
        """List all bots"""
        try:
            bots_list = []
            for user_id, bot in self.cloned_bots.items():
                bots_list.append({
                    "name": bot["name"],
                    "status": bot["status"],
                    "plugins": bot["plugins"],
                    "created": bot["created"]
                })
            
            return {"success": True, "bots": bots_list, "total": len(bots_list)}
        except Exception as e:
            return {"success": False, "bots": [], "total": 0}


# Global instance
cloner = None


async def init_cloner():
    """Initialize cloner"""
    global cloner
    cloner = BotCloner()
    await cloner.load_config()
    logger.info("✅ Bot cloner initialized")


# Command handlers
async def setup_clone_commands(app: Client):
    """Setup clone commands - CALL THIS IN YOUR MAIN BOT"""
    
    await init_cloner()
    
    @app.on_message(filters.command("clone"))
    async def clone_cmd(client: Client, message: Message):
        """Clone bot"""
        try:
            user_id = str(message.from_user.id)
            args = message.text.split()
            
            if len(args) < 3:
                await message.reply(
                    "❌ **Usage:** `/clone <token> <name>`\n\n"
                    "**Example:** `/clone 123456:ABC MyBot`\n\n"
                    "Get token from @BotFather",
                    parse_mode="markdown"
                )
                return
            
            token = args[1]
            name = " ".join(args[2:])
            
            msg = await message.reply("🔄 Cloning...")
            result = await cloner.clone_bot(user_id, token, name)
            
            if result["success"]:
                text = f"{result['message']}\n📦 Plugins: {result['plugins']}"
            else:
                text = result["error"]
            
            await msg.edit_text(text, parse_mode="markdown")
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")
    
    @app.on_message(filters.command("clonestatus"))
    async def status_cmd(client: Client, message: Message):
        """Get bot status"""
        try:
            user_id = str(message.from_user.id)
            result = await cloner.get_status(user_id)
            
            if result["success"]:
                text = (
                    f"🤖 **Bot Status**\n\n"
                    f"Name: `{result['name']}`\n"
                    f"Status: `{result['status']}`\n"
                    f"Plugins: `{result['plugins']}`\n"
                    f"Created: `{result['created'][:19]}`"
                )
            else:
                text = result["error"]
            
            await message.reply(text, parse_mode="markdown")
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")
    
    @app.on_message(filters.command("deleteclone"))
    async def delete_cmd(client: Client, message: Message):
        """Delete bot"""
        try:
            user_id = str(message.from_user.id)
            result = await cloner.delete_bot(user_id)
            await message.reply(result["message"] if result["success"] else result["error"], parse_mode="markdown")
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")
    
    @app.on_message(filters.command("listclones"))
    async def list_cmd(client: Client, message: Message):
        """List all bots"""
        try:
            result = await cloner.list_bots()
            
            if result["success"] and result["total"] > 0:
                text = f"📊 **Total Bots: {result['total']}**\n\n"
                for bot in result["bots"]:
                    text += f"🤖 {bot['name']}\n   Plugins: {bot['plugins']}\n\n"
            else:
                text = "❌ No bots found"
            
            await message.reply(text, parse_mode="markdown")
        except Exception as e:
            await message.reply(f"❌ Error: {str(e)}")
    
    logger.info("✅ Clone commands registered!")
