import logging
import asyncio  # Import asyncio
from telethon import TelegramClient, events
from telethon import Button

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)

API_ID = '10711540'
API_HASH = 'a4892a544176899feab0ac136561f73c'
BOT_TOKEN = '8099888095:AAHnI8ChSMevwG3a2nIFn5SQUiE57Cw5UdA'

# Initialize the client
client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

users = {}
matches = {}
waiting_for_match = {}  # Menyimpan pengguna yang sedang menunggu untuk mencocokkan
waiting_timeout = 20  # Waktu tunggu dalam detik

available_interests = ['Komik', 'Olahraga', 'Lukis', 'Musik', 'Manga', 'Anime', 'Game']

async def register_user(user_id, username):
    if user_id not in users:
        users[user_id] = {'username': username, 'interests': []}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user = event.sender_id
    username = event.sender.username or f"User {user}"
    await register_user(user, username)
    await event.respond("Selamat datang! Gunakan /setinterests untuk menetapkan minat.")

@client.on(events.NewMessage(pattern='/setinterests'))
async def set_interests(event):
    user = event.sender_id
    await event.respond(
        "Pilih minat Anda dari pilihan berikut:",
        buttons=[
            [Button.inline(interest) for interest in available_interests],
            [Button.inline("Simpan")]
        ]
    )

@client.on(events.CallbackQuery)
async def button_callback(event):
    user = event.sender_id
    if user not in users:
        await event.answer("Silakan mendaftar terlebih dahulu dengan /start.")
        return

    if event.data.decode() in available_interests:
        selected_interest = event.data.decode()
        if selected_interest not in users[user]['interests']:
            users[user]['interests'].append(selected_interest)
            await event.answer(f"Minat '{selected_interest}' telah ditambahkan.")
        else:
            await event.answer(f"Anda sudah memilih minat '{selected_interest}'.")

    elif event.data.decode() == "Simpan":
        if users[user]['interests']:
            await event.answer(f"Minat Anda telah disimpan: {', '.join(users[user]['interests'])}. Gunakan /match untuk mencari teman bicara.")
        else:
            await event.answer("Anda belum memilih minat. Silakan pilih terlebih dahulu.")

    return

@client.on(events.NewMessage(pattern='/match'))
async def match(event):
    user = event.sender_id
    if user not in users:
        await event.respond("Silakan mendaftar terlebih dahulu dengan /start.")
        return

    # Jika pengguna sudah dalam antrian pencocokan
    if user in waiting_for_match:
        await event.respond("Anda sedang menunggu pencocokan. Silakan tunggu.")
        return

    waiting_for_match[user] = asyncio.get_event_loop().time()  # Menyimpan waktu saat pengguna menggunakan /match
    await event.respond("Menunggu pengguna lain untuk mencocokkan...")

    # Tunggu hingga 20 detik secara asinkron
    await asyncio.sleep(waiting_timeout)

    # Cek apakah pengguna lain juga dalam antrian
    matched_user = None
    for uid in waiting_for_match:
        if uid != user:  # Pastikan bukan pengguna itu sendiri
            matched_user = uid
            break

    if matched_user:
        matches[user] = matched_user
        matches[matched_user] = user
        del waiting_for_match[user]  # Hapus dari antrian
        del waiting_for_match[matched_user]  # Hapus dari antrian
        await event.respond(f"Anda terhubung dengan {users[matched_user]['username']}!")
        await client.send_message(matched_user, f"{users[user]['username']} telah terhubung dengan Anda!")
    else:
        await event.respond("Tidak ada pengguna lain yang cocok dalam waktu 20 detik.")
        del waiting_for_match[user]  # Hapus dari antrian

@client.on(events.NewMessage(pattern='/disconnect'))
async def disconnect(event):
    user = event.sender_id
    if user in matches:
        matched_user_id = matches.pop(user)  # Mengambil user yang match
        matches.pop(matched_user_id, None)  # Hapus pasangan dari match dict
        await event.respond("Anda telah terputus dari teman bicara.")
        await client.send_message(matched_user_id, "Teman bicara Anda telah memutuskan koneksi.")
    else:
        await event.respond("Anda tidak terhubung dengan siapa pun.")

@client.on(events.NewMessage(incoming=True))
async def chat(event):
    if event.is_private and not event.message.message.startswith('/'):
        user = event.sender_id
        if user in matches:
            matched_user_id = matches[user]
            await client.send_message(matched_user_id, event.message.message)
            await event.respond("Pesan telah dikirim.")
        else:
            await event.respond("Anda belum terhubung dengan siapa pun. Gunakan /match untuk mencari teman bicara.")
    else:
        await event.respond("Silakan kirim pesan biasa, bukan perintah.")

async def main():
    await client.start()
    logging.info("Bot sedang berjalan...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
