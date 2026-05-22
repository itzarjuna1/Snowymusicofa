"""
✦ Simple Clone System ✦
"""

import os
import json
import logging
import shutil
from typing import Dict, Optional
from datetime import datetime

import aiofiles
from pyrogram import Client, filters
from pyrogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLONE_IMG = "https://files.catbox.moe/3rohdi.jpg"


class BotCloner:
    def __init__(self, storage_path: str = "./cloned_bots"):
        self.storage_path = storage_path
        self.cloned_bots: Dict[str, dict] = {}
        self.plugin_dirs = [
            "play",
            "bot",
            "admins",
            "sudo",
            "misc",
            "security",
            "tools"
        ]

        os.makedirs(storage_path, exist_ok=True)

    async def load_config(self):
        config_file = os.path.join(self.storage_path, "bots.json")

        try:
            if os.path.exists(config_file):
                async with aiofiles.open(config_file, "r") as f:
                    content = await f.read()
                    self.cloned_bots = json.loads(content)

                logger.info(
                    f"✅ Loaded {len(self.cloned_bots)} bots"
                )

        except Exception as e:
            logger.error(f"Load config error: {e}")
            self.cloned_bots = {}

    async def load_cloned_bots(self):
        return await self.load_config()

    async def save_config(self):
        config_file = os.path.join(self.storage_path, "bots.json")

        try:
            async with aiofiles.open(config_file, "w") as f:
                await f.write(
                    json.dumps(
                        self.cloned_bots,
                        indent=2
                    )
                )

        except Exception as e:
            logger.error(f"Save config error: {e}")

    def validate_token(self, token: str) -> bool:
        try:
            if ":" not in token:
                return False

            parts = token.split(":")

            if len(parts) != 2:
                return False

            return (
                len(parts[0]) > 0
                and len(parts[1]) > 20
            )

        except Exception:
            return False

    async def clone_bot(
        self,
        user_id: str,
        bot_token: str,
        bot_name: str
    ) -> Dict:

        try:
            if not self.validate_token(bot_token):
                return {
                    "success": False,
                    "error": "❌ **ɪɴᴠᴀʟɪᴅ ʙᴏᴛ ᴛᴏᴋᴇɴ !**"
                }

            if user_id in self.cloned_bots:
                return {
                    "success": False,
                    "error": "❌ **ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀ ᴄʟᴏɴᴇᴅ ʙᴏᴛ !**"
                }

            bot_dir = os.path.join(
                self.storage_path,
                f"bot_{user_id}"
            )

            os.makedirs(bot_dir, exist_ok=True)

            plugins_dir = os.path.join(
                bot_dir,
                "plugins"
            )

            os.makedirs(plugins_dir, exist_ok=True)

            for plugin_dir in self.plugin_dirs:
                src = f"./Oneforall/plugins/{plugin_dir}"

                dst = os.path.join(
                    plugins_dir,
                    plugin_dir
                )

                if os.path.exists(src):

                    if os.path.exists(dst):
                        shutil.rmtree(dst)

                    shutil.copytree(src, dst)

            plugin_count = 0

            for root, dirs, files in os.walk(plugins_dir):

                for file in files:

                    if (
                        file.endswith(".py")
                        and not file.startswith("__")
                    ):
                        plugin_count += 1

            self.cloned_bots[user_id] = {
                "token": bot_token,
                "name": bot_name,
                "created": datetime.now().isoformat(),
                "plugins": plugin_count,
                "status": "active",
                "dir": bot_dir
            }

            await self.save_config()

            return {
                "success": True,
                "message": (
                    f"✅ **{bot_name} "
                    f"ᴄʟᴏɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ !**"
                ),
                "plugins": plugin_count
            }

        except Exception as e:

            logger.error(f"Clone error: {e}")

            return {
                "success": False,
                "error": f"❌ `{str(e)}`"
            }

    async def delete_bot(self, user_id: str) -> Dict:
        try:
            if user_id not in self.cloned_bots:
                return {
                    "success": False,
                    "error": "❌ **ɴᴏ ᴄʟᴏɴᴇᴅ ʙᴏᴛ ғᴏᴜɴᴅ !**"
                }

            bot_dir = self.cloned_bots[user_id]["dir"]

            if os.path.exists(bot_dir):
                shutil.rmtree(bot_dir)

            del self.cloned_bots[user_id]

            await self.save_config()

            return {
                "success": True,
                "message": "✅ **ᴄʟᴏɴᴇᴅ ʙᴏᴛ ᴅᴇʟᴇᴛᴇᴅ !**"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"❌ `{str(e)}`"
            }

    async def get_status(self, user_id: str) -> Dict:
        try:
            if user_id not in self.cloned_bots:
                return {
                    "success": False,
                    "error": "❌ **ɴᴏ ʙᴏᴛ ғᴏᴜɴᴅ !**"
                }

            bot = self.cloned_bots[user_id]

            return {
                "success": True,
                "name": bot["name"],
                "status": bot["status"],
                "plugins": bot["plugins"],
                "created": bot["created"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"❌ `{str(e)}`"
            }

    async def list_bots(self) -> Dict:
        try:
            bots_list = []

            for _, bot in self.cloned_bots.items():
                bots_list.append({
                    "name": bot["name"],
                    "status": bot["status"],
                    "plugins": bot["plugins"],
                    "created": bot["created"]
                })

            return {
                "success": True,
                "bots": bots_list,
                "total": len(bots_list)
            }

        except Exception:
            return {
                "success": False,
                "bots": [],
                "total": 0
            }


_cloner_instance: Optional[BotCloner] = None


async def init_cloner(
    storage_path: str = "./cloned_bots"
) -> BotCloner:

    global _cloner_instance

    if _cloner_instance is None:
        _cloner_instance = BotCloner(storage_path)

        await _cloner_instance.load_config()

        logger.info("✅ Cloner initialized")

    return _cloner_instance


def get_cloner(
    *args,
    **kwargs
) -> BotCloner:

    global _cloner_instance

    if _cloner_instance is None:
        _cloner_instance = BotCloner()

    return _cloner_instance


async def setup_clone_commands(app: Client):

    cloner = await init_cloner()

    @app.on_message(filters.command("clone"))
    async def clone_cmd(
        client: Client,
        message: Message
    ):

        try:
            user_id = str(message.from_user.id)

            args = message.text.split()

            if len(args) < 3:

                return await message.reply_photo(
                    photo=CLONE_IMG,
                    caption=(
                        "❌ **ᴜsᴀɢᴇ :**\n\n"
                        "`/clone <token> <name>`\n\n"
                        "**ᴇxᴀᴍᴘʟᴇ :**\n"
                        "`/clone 123456:ABC MyBot`"
                    ),
                    parse_mode="markdown"
                )

            token = args[1]

            name = " ".join(args[2:])

            msg = await message.reply_photo(
                photo=CLONE_IMG,
                caption="🔄 **ᴄʟᴏɴɪɴɢ ʏᴏᴜʀ ʙᴏᴛ...**",
                parse_mode="markdown"
            )

            result = await cloner.clone_bot(
                user_id,
                token,
                name
            )

            if result["success"]:

                text = (
                    f"{result['message']}\n\n"
                    f"📦 **ᴘʟᴜɢɪɴs :** "
                    f"`{result['plugins']}`"
                )

            else:
                text = result["error"]

            await msg.edit_caption(
                caption=text,
                parse_mode="markdown"
            )

        except Exception as e:

            await message.reply_text(
                f"❌ `{str(e)}`",
                parse_mode="markdown"
            )

    @app.on_message(filters.command("clonestatus"))
    async def clonestatus_cmd(
        client: Client,
        message: Message
    ):

        user_id = str(message.from_user.id)

        result = await cloner.get_status(user_id)

        if result["success"]:

            text = (
                "🤖 **ᴄʟᴏɴᴇ ʙᴏᴛ sᴛᴀᴛᴜs**\n\n"
                f"ɴᴀᴍᴇ : `{result['name']}`\n"
                f"sᴛᴀᴛᴜs : `{result['status']}`\n"
                f"ᴘʟᴜɢɪɴs : `{result['plugins']}`"
            )

        else:
            text = result["error"]

        await message.reply_photo(
            photo=CLONE_IMG,
            caption=text,
            parse_mode="markdown"
        )

    @app.on_message(filters.command("deleteclone"))
    async def deleteclone_cmd(
        client: Client,
        message: Message
    ):

        user_id = str(message.from_user.id)

        result = await cloner.delete_bot(user_id)

        await message.reply_photo(
            photo=CLONE_IMG,
            caption=(
                result["message"]
                if result["success"]
                else result["error"]
            ),
            parse_mode="markdown"
        )

    @app.on_message(filters.command("listclones"))
    async def listclones_cmd(
        client: Client,
        message: Message
    ):

        result = await cloner.list_bots()

        if result["success"] and result["total"] > 0:

            text = (
                f"📊 **ᴛᴏᴛᴀʟ ᴄʟᴏɴᴇs :** "
                f"`{result['total']}`\n\n"
            )

            for bot in result["bots"]:

                text += (
                    f"🤖 `{bot['name']}`\n"
                    f"📦 ᴘʟᴜɢɪɴs : "
                    f"`{bot['plugins']}`\n\n"
                )

        else:
            text = "❌ **ɴᴏ ᴄʟᴏɴᴇᴅ ʙᴏᴛs ғᴏᴜɴᴅ !**"

        await message.reply_photo(
            photo=CLONE_IMG,
            caption=text,
            parse_mode="markdown"
        )

    logger.info("✅ Clone commands loaded")
