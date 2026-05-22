"""
✦ Real Multi Client Clone System ✦
"""

import os
import json
import shutil
import logging
from typing import Dict, Optional
from datetime import datetime

import aiofiles
from pyrogram import Client

from config import API_ID, API_HASH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLONE_IMG = "https://graph.org/file/91f8d6a8fd408555c2aa4-202c7be9409983cefd.jpg"


class BotCloner:

    def __init__(
        self,
        storage_path: str = "./cloned_bots"
    ):

        self.storage_path = storage_path

        self.cloned_bots: Dict[str, dict] = {}

        self.running_clients: Dict[str, Client] = {}

        self.plugin_dirs = [
            "play",
            "bot",
            "admins",
            "sudo",
            "misc",
            "security",
            "tools"
        ]

        os.makedirs(
            self.storage_path,
            exist_ok=True
        )

    async def load_config(self):

        config_file = os.path.join(
            self.storage_path,
            "bots.json"
        )

        try:

            if os.path.exists(config_file):

                async with aiofiles.open(
                    config_file,
                    "r"
                ) as f:

                    content = await f.read()

                    self.cloned_bots = json.loads(content)

                logger.info(
                    f"✅ Loaded "
                    f"{len(self.cloned_bots)} cloned bots"
                )

        except Exception as e:

            logger.error(
                f"Load config error: {e}"
            )

            self.cloned_bots = {}

    async def load_cloned_bots(self):
        return await self.load_config()

    async def save_config(self):

        config_file = os.path.join(
            self.storage_path,
            "bots.json"
        )

        try:

            async with aiofiles.open(
                config_file,
                "w"
            ) as f:

                await f.write(
                    json.dumps(
                        self.cloned_bots,
                        indent=2
                    )
                )

        except Exception as e:

            logger.error(
                f"Save config error: {e}"
            )

    def validate_token(
        self,
        token: str
    ) -> bool:

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

            if not self.validate_token(
                bot_token
            ):

                return {
                    "success": False,
                    "error": (
                        "❌ **ɪɴᴠᴀʟɪᴅ "
                        "ʙᴏᴛ ᴛᴏᴋᴇɴ !**"
                    )
                }

            if user_id in self.cloned_bots:

                return {
                    "success": False,
                    "error": (
                        "❌ **ʏᴏᴜ "
                        "ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ "
                        "ᴀ ᴄʟᴏɴᴇᴅ ʙᴏᴛ !**"
                    )
                }

            bot_dir = os.path.join(
                self.storage_path,
                f"bot_{user_id}"
            )

            os.makedirs(
                bot_dir,
                exist_ok=True
            )

            plugins_dir = os.path.join(
                bot_dir,
                "plugins"
            )

            os.makedirs(
                plugins_dir,
                exist_ok=True
            )

            for plugin_dir in self.plugin_dirs:

                src = (
                    f"./Oneforall/plugins/"
                    f"{plugin_dir}"
                )

                dst = os.path.join(
                    plugins_dir,
                    plugin_dir
                )

                if os.path.exists(src):

                    if os.path.exists(dst):
                        shutil.rmtree(dst)

                    shutil.copytree(src, dst)

            plugin_count = 0

            for root, dirs, files in os.walk(
                plugins_dir
            ):

                for file in files:

                    if (
                        file.endswith(".py")
                        and not file.startswith("__")
                    ):
                        plugin_count += 1

            session_name = (
                f"clone_{user_id}"
            )

            clone_client = Client(
                name=session_name,
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=bot_token,
                plugins={
                    "root": plugins_dir
                },
                workdir=bot_dir
            )

            await clone_client.start()

            self.running_clients[
                user_id
            ] = clone_client

            created_at = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            self.cloned_bots[user_id] = {
                "token": bot_token,
                "name": bot_name,
                "created": created_at,
                "plugins": plugin_count,
                "status": "running",
                "dir": bot_dir,
                "session": session_name,
                "last_restart": created_at
            }

            await self.save_config()

            logger.info(
                f"✅ Started cloned bot "
                f"{bot_name}"
            )

            return {
                "success": True,
                "message": (
                    f"✅ **{bot_name} "
                    f"ᴄʟᴏɴᴇᴅ "
                    f"sᴜᴄᴄᴇssғᴜʟʟʏ !**"
                ),
                "plugins": plugin_count,
                "bot_name": bot_name,
                "plugins_loaded": plugin_count,
                "bot_config": {
                    "bot_dir": bot_dir,
                    "created_at": created_at
                }
            }

        except Exception as e:

            logger.error(
                f"Clone error: {e}"
            )

            return {
                "success": False,
                "error": f"❌ `{str(e)}`"
            }

    async def start_cloned_bot(
        self,
        user_id: str
    ):

        try:

            if user_id not in self.cloned_bots:

                return {
                    "success": False,
                    "error": (
                        "❌ ɴᴏ "
                        "ʙᴏᴛ ғᴏᴜɴᴅ !"
                    )
                }

            if user_id in self.running_clients:

                return {
                    "success": False,
                    "error": (
                        "❌ ʙᴏᴛ "
                        "ɪs ᴀʟʀᴇᴀᴅʏ "
                        "ʀᴜɴɴɪɴɢ !"
                    )
                }

            bot = self.cloned_bots[user_id]

            plugins_dir = os.path.join(
                bot["dir"],
                "plugins"
            )

            clone_client = Client(
                name=bot["session"],
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=bot["token"],
                plugins={
                    "root": plugins_dir
                },
                workdir=bot["dir"]
            )

            await clone_client.start()

            self.running_clients[
                user_id
            ] = clone_client

            self.cloned_bots[user_id][
                "status"
            ] = "running"

            self.cloned_bots[user_id][
                "last_restart"
            ] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            await self.save_config()

            return {
                "success": True,
                "message": (
                    "✅ ʙᴏᴛ "
                    "sᴛᴀʀᴛᴇᴅ !"
                )
            }

        except Exception as e:

            return {
                "success": False,
                "error": f"❌ `{str(e)}`"
            }

    async def stop_cloned_bot(
        self,
        user_id: str
    ):

        try:

            if user_id not in self.running_clients:

                return {
                    "success": False,
                    "error": (
                        "❌ ʙᴏᴛ "
                        "ɪs ɴᴏᴛ "
                        "ʀᴜɴɴɪɴɢ !"
                    )
                }

            client = self.running_clients[
                user_id
            ]

            await client.stop()

            del self.running_clients[
                user_id
            ]

            self.cloned_bots[user_id][
                "status"
            ] = "stopped"

            await self.save_config()

            return {
                "success": True,
                "message": (
                    "🛑 ʙᴏᴛ "
                    "sᴛᴏᴘᴘᴇᴅ !"
                )
            }

        except Exception as e:

            return {
                "success": False,
                "error": f"❌ `{str(e)}`"
            }

    async def delete_bot(
        self,
        user_id: str
    ) -> Dict:

        try:

            if user_id not in self.cloned_bots:

                return {
                    "success": False,
                    "error": (
                        "❌ **ɴᴏ "
                        "ᴄʟᴏɴᴇᴅ "
                        "ʙᴏᴛ "
                        "ғᴏᴜɴᴅ !**"
                    )
                }

            if user_id in self.running_clients:

                try:
                    await self.running_clients[
                        user_id
                    ].stop()

                except Exception:
                    pass

                del self.running_clients[
                    user_id
                ]

            bot_dir = self.cloned_bots[
                user_id
            ]["dir"]

            if os.path.exists(bot_dir):
                shutil.rmtree(bot_dir)

            del self.cloned_bots[user_id]

            await self.save_config()

            return {
                "success": True,
                "message": (
                    "✅ **ᴄʟᴏɴᴇᴅ "
                    "ʙᴏᴛ "
                    "ᴅᴇʟᴇᴛᴇᴅ !**"
                )
            }

        except Exception as e:

            return {
                "success": False,
                "error": f"❌ `{str(e)}`"
            }

    async def delete_cloned_bot(
        self,
        user_id: str
    ):
        return await self.delete_bot(
            user_id
        )

    async def get_status(
        self,
        user_id: str
    ) -> Dict:

        try:

            if user_id not in self.cloned_bots:

                return {
                    "success": False,
                    "error": (
                        "❌ **ɴᴏ "
                        "ʙᴏᴛ "
                        "ғᴏᴜɴᴅ !**"
                    )
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

    async def get_bot_status(
        self,
        user_id: str
    ):

        result = await self.get_status(
            user_id
        )

        if not result["success"]:
            return result

        bot = self.cloned_bots[user_id]

        return {
            "success": True,
            "bot_name": bot["name"],
            "status": bot["status"],
            "plugins_loaded": bot["plugins"],
            "created_at": bot["created"],
            "last_restart": bot["last_restart"],
            "bot_dir": bot["dir"]
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


_cloner_instance: Optional[
    BotCloner
] = None


async def init_cloner(
    storage_path: str = "./cloned_bots"
) -> BotCloner:

    global _cloner_instance

    if _cloner_instance is None:

        _cloner_instance = BotCloner(
            storage_path
        )

        await _cloner_instance.load_config()

        logger.info(
            "✅ Cloner initialized"
        )

    return _cloner_instance


def get_cloner(
    *args,
    **kwargs
) -> BotCloner:

    global _cloner_instance

    if _cloner_instance is None:
        _cloner_instance = BotCloner()

    return _cloner_instance
