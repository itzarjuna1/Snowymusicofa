from pyrogram import Client, idle
import sys

BOT_TOKEN = sys.argv[1]

app = Client(
    name=f"clone_{BOT_TOKEN[:10]}",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(
        root="Oneforall/plugins"
    )
)

app.start()

print("Clone bot started")

idle()

app.stop()
