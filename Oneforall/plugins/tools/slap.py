import requests
from pyrogram import filters


def setup(app):

    sfw_actions = [
        "waifu",
        "neko",
        "shinobu",
        "bully",
        "cry",
        "hug",
        "kiss",
        "lick",
        "pat",
        "smug",
        "highfive",
        "nom",
        "bite",
        "slap",
        "wink",
        "poke",
        "dance",
        "cringe",
        "blush",
        "happy",
        "kick",
    ]

    for action in sfw_actions:

        @app.on_message(filters.command(action))
        async def send_action_image(
            client,
            message,
            action=action
        ):

            try:

                response = requests.get(
                    f"https://api.waifu.pics/sfw/{action}"
                )

                response.raise_for_status()

                image_url = response.json().get("url")

                if not image_url:

                    return await message.reply_text(
                        "❌ ɴᴏ ɪᴍᴀɢᴇ ғᴏᴜɴᴅ !"
                    )

                file_extension = (
                    image_url.split(".")[-1]
                    .lower()
                )

                if file_extension == "gif":

                    await client.send_animation(
                        chat_id=message.chat.id,
                        animation=image_url
                    )

                else:

                    await client.send_photo(
                        chat_id=message.chat.id,
                        photo=image_url
                    )

            except requests.RequestException as e:

                await message.reply_text(
                    f"❌ API Error:\n`{str(e)}`"
                )

            except Exception as e:

                await message.reply_text(
                    f"❌ Error:\n`{str(e)}`"
                )
