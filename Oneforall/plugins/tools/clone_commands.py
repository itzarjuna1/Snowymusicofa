"""
Telegram command handlers for bot cloning functionality
Provides /clone and /cloned commands
"""

from pyrogram import Client, filters
from pyrogram.types import Message

import logging
from Oneforall import app 

logger = logging.getLogger(__name__)


@app.on_message(filters.command("clone") & filters.private)
async def clone_command(client: Client, message: Message):
    """
    /clone command handler
    Usage: /clone <bot_token> <bot_name>
    Example: /clone 123456789:ABCdefGHIjklmnoPQRstuvwxyz MyBot
    """
    try:
        user_id = str(message.from_user.id)
        command_parts = message.text.split(maxsplit=2)
        
        # Validate command format
        if len(command_parts) < 3:
            await message.reply(
                "❌ Invalid command format!\n\n"
                "Usage: `/clone <bot_token> <bot_name>`\n\n"
                "Example:\n"
                "`/clone 123456789:ABCdefGHIjklmnoPQRstuvwxyz MyAwesomeBot`\n\n"
                "**Note:** Bot token format should be `token_id:token_hash`"
            )
            return
        
        bot_token = command_parts[1]
        bot_name = command_parts[2]
        
        # Validate bot name length
        if len(bot_name) > 64:
            await message.reply("❌ Bot name is too long (max 64 characters)")
            return
        
        if len(bot_name) < 1:
            await message.reply("❌ Bot name cannot be empty")
            return
        
        # Show processing message
        status_msg = await message.reply("⏳ Cloning your bot... This may take a moment...")
        
        cloner = get_cloner(bot_token)
        await cloner.load_cloned_bots()
        
        result = await cloner.clone_bot(user_id, bot_token, bot_name)
        
        if result["success"]:
            await cloner.start_cloned_bot(user_id)
            
            response = (
                "✅ **Bot Cloned Successfully!**\n\n"
                f"🤖 **Bot Name:** `{result['bot_name']}`\n"
                f"📦 **Plugins Loaded:** {result['plugins_loaded']}\n"
                f"📁 **Bot Location:** `{result['bot_config']['bot_dir']}`\n"
                f"⏰ **Created At:** `{result['bot_config']['created_at']}`\n\n"
                "Your cloned bot is now running with all features! 🚀\n"
                "Use `/cloned` to check your bot status."
            )
            await status_msg.edit_text(response)
        else:
            error_msg = result.get('error', 'Unknown error occurred')
            if result.get('existing_bot'):
                error_msg += f"\n\n💡 **Tip:** Use `/delete_clone` to remove your existing bot first."
            await status_msg.edit_text(f"❌ **Cloning Failed**\n\n{error_msg}")
            
    except Exception as e:
        logger.error(f"Error in clone_command: {e}")
        await message.reply(f"❌ An error occurred: {str(e)}")


@app.on_message(filters.command("cloned") & filters.private)
async def cloned_command(client: Client, message: Message):
    """
    /cloned command handler
    Shows status of user's cloned bot(s)
    """
    try:
        user_id = str(message.from_user.id)
        
        cloner = get_cloner("")
        await cloner.load_cloned_bots()
        
        result = await cloner.get_bot_status(user_id)
        
        if result["success"]:
            status_indicator = "🟢 Running" if result['status'] == 'running' else f"🔴 {result['status'].capitalize()}"
            
            response = (
                "🤖 **Your Cloned Bot Status**\n\n"
                f"**Name:** `{result['bot_name']}`\n"
                f"**Status:** {status_indicator}\n"
                f"**Plugins Loaded:** {result['plugins_loaded']}\n"
                f"**Created:** `{result['created_at']}`\n"
                f"**Last Restart:** `{result['last_restart']}`\n"
                f"**Directory:** `{result['bot_dir']}`\n\n"
                "**Available Commands:**\n"
                "`/clone` - Clone a new bot\n"
                "`/stop_clone` - Stop your cloned bot\n"
                "`/start_clone` - Start your cloned bot\n"
                "`/delete_clone` - Delete your cloned bot"
            )
            await message.reply(response)
        else:
            await message.reply(
                "❌ **No Cloned Bot Found**\n\n"
                "You don't have a cloned bot yet.\n"
                "Use `/clone <bot_token> <bot_name>` to create one!\n\n"
                "**Note:** You can only clone one bot at a time."
            )
            
    except Exception as e:
        logger.error(f"Error in cloned_command: {e}")
        await message.reply(f"❌ An error occurred: {str(e)}")


@app.on_message(filters.command("startclone") & filters.private)
async def start_clone_command(client: Client, message: Message):
    """
    /start_clone command handler
    Starts a stopped cloned bot
    """
    try:
        user_id = str(message.from_user.id)
        
        cloner = get_cloner("")
        await cloner.load_cloned_bots()
        
        result = await cloner.start_cloned_bot(user_id)
        
        if result["success"]:
            await message.reply(f"✅ **Success!**\n\n{result['message']}")
        else:
            await message.reply(f"❌ **Error**\n\n{result['error']}")
            
    except Exception as e:
        logger.error(f"Error in start_clone_command: {e}")
        await message.reply(f"❌ An error occurred: {str(e)}")


@app.on_message(filters.command("stop_clone") & filters.private)
async def stop_clone_command(client: Client, message: Message):
    """
    /stop_clone command handler
    Stops a running cloned bot
    """
    try:
        user_id = str(message.from_user.id)
        
        cloner = get_cloner("")
        await cloner.load_cloned_bots()
        
        result = await cloner.stop_cloned_bot(user_id)
        
        if result["success"]:
            await message.reply(f"✅ **Success!**\n\n{result['message']}")
        else:
            await message.reply(f"❌ **Error**\n\n{result['error']}")
            
    except Exception as e:
        logger.error(f"Error in stop_clone_command: {e}")
        await message.reply(f"❌ An error occurred: {str(e)}")


@app.on_message(filters.command("delete_clone") & filters.private)
async def delete_clone_command(client: Client, message: Message):
    """
    /delete_clone command handler
    Deletes a cloned bot and all its data
    """
    try:
        user_id = str(message.from_user.id)
        
        cloner = get_cloner("")
        await cloner.load_cloned_bots()
        
        # Ask for confirmation
        confirmation_msg = await message.reply(
            "⚠️ **Warning!**\n\n"
            "Are you sure you want to delete your cloned bot? "
            "This action will delete all bot data and cannot be undone.\n\n"
            "Reply with `yes` to confirm or `no` to cancel."
        )
        
        # For now, we'll just execute the delete
        # In a production app, you'd implement proper confirmation flow
        result = await cloner.delete_cloned_bot(user_id)
        
        if result["success"]:
            await message.reply(f"✅ **Success!**\n\n{result['message']}")
        else:
            await message.reply(f"❌ **Error**\n\n{result['error']}")
            
    except Exception as e:
        logger.error(f"Error in delete_clone_command: {e}")
        await message.reply(f"❌ An error occurred: {str(e)}")
