import asyncio
import html
import json
import os
import re
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8233812855:AAGqeVF2tfot9N9rzqKBxpJJgx_UOifjhBY"  # Apna token daalo

# SUPER ADMIN (SUDO) - Sirf ye owner hai
SUDO_ID = 6089214006  # Tumhari ID

# SARE ADMIN IDs
ADMIN_IDS = [6089214006, 8323739248, 6877796325, 8441236350, 8327866462, 8364503066]

# Developer Username (SAHI SE FIX KAR DIYA)
DEV_USERNAME = "@ll_YOUR_ASHISH_BRO_ll"  # Apna username yahan sahi se likho

# Start image (sent with spoiler in /start and on every "found" message)
START_IMAGE = "https://i.ibb.co/JW2GCVPx/image.jpg"

# Auto-delete every bot message after this many seconds
AUTO_DELETE_SECONDS = 120

# Startup loading UI
GREET = [
    "<b>🌸 ʜʟᴏ ʙᴀʙʏ...</b>",
    "<b>✨ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ...</b>",
    "<b>🌌 ᴛʜᴇ ᴍᴀɢɪᴄᴀʟ ᴡᴏʀʟᴅ...</b>",
    "<b>🖤 ᴀsʜɪsʜ x ᴀɴɪᴍᴇ...</b>",
    "<b>💫 ʟᴏᴀᴅɪɴɢ...</b>",
]

# Database files
ANIME_FILE = "anime_data.json"
MOVIE_FILE = "movie_data.json"
KDRAMA_FILE = "kdrama_data.json"
ADMIN_FILE = "admin_ids.json"
SUDO_FILE = "sudo_ids.json"
USERS_FILE = "users.json"

# ==================== DATABASE FUNCTIONS ====================
def load_data(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_admins():
    if os.path.exists(ADMIN_FILE):
        try:
            with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return ADMIN_IDS
    return ADMIN_IDS

def save_admins(admins):
    with open(ADMIN_FILE, 'w', encoding='utf-8') as f:
        json.dump(admins, f, indent=4)

def load_sudo():
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return [SUDO_ID]
    return [SUDO_ID]

def save_sudo(sudo_list):
    with open(SUDO_FILE, 'w', encoding='utf-8') as f:
        json.dump(sudo_list, f, indent=4)

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_users(users_list):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_list, f, indent=4)

def remember_user(user_id):
    if user_id not in USER_IDS:
        USER_IDS.append(user_id)
        save_users(USER_IDS)

# Load all data
anime_data = load_data(ANIME_FILE)
movie_data = load_data(MOVIE_FILE)
kdrama_data = load_data(KDRAMA_FILE)
ADMIN_IDS = load_admins()
SUDO_IDS = load_sudo()
USER_IDS = load_users()

# ==================== AUTO-DELETE (every bot message disappears after 2 mins) ====================
async def _auto_delete_message(bot, chat_id, message_id, delay):
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

def _schedule_delete(bot, message):
    if not message:
        return
    try:
        chat_id = message.chat_id
        message_id = message.message_id
    except Exception:
        return
    try:
        asyncio.create_task(_auto_delete_message(bot, chat_id, message_id, AUTO_DELETE_SECONDS))
    except RuntimeError:
        # No running loop (e.g. during startup) — skip
        pass

def _wrap_with_auto_delete(method_name):
    original = getattr(Bot, method_name)
    async def wrapper(self, *args, **kwargs):
        msg = await original(self, *args, **kwargs)
        _schedule_delete(self, msg)
        return msg
    wrapper.__name__ = method_name
    setattr(Bot, method_name, wrapper)

for _m in ("send_message", "send_photo", "send_video", "send_document", "send_audio",
           "send_animation", "send_voice", "send_sticker", "send_media_group"):
    if hasattr(Bot, _m):
        _wrap_with_auto_delete(_m)

# ==================== CHECK PERMISSIONS ====================
def is_sudo(user_id):
    return user_id in SUDO_IDS

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ==================== STYLISH TEXT ====================
def normalize_text(text):
    stylish_map = {
        'ᴀ': 'a', 'ʙ': 'b', 'ᴄ': 'c', 'ᴅ': 'd', 'ᴇ': 'e', 'ғ': 'f', 'ɢ': 'g', 'ʜ': 'h', 'ɪ': 'i',
        'ᴊ': 'j', 'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ɴ': 'n', 'ᴏ': 'o', 'ᴘ': 'p', 'ǫ': 'q', 'ʀ': 'r',
        's': 's', 'ᴛ': 't', 'ᴜ': 'u', 'ᴠ': 'v', 'ᴡ': 'w', 'x': 'x', 'ʏ': 'y', 'ᴢ': 'z'
    }
    result = ''
    for char in text:
        result += stylish_map.get(char, char)
    return result

# ==================== MAIN MENU ====================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🍥 ᴀɴɪᴍᴇ", callback_data="anime_menu"), InlineKeyboardButton("🎬 ᴍᴏᴠɪᴇs", callback_data="movie_menu")],
        [InlineKeyboardButton("🇰 ᴋ-ᴅʀᴀᴍᴀ", callback_data="kdrama_menu"), InlineKeyboardButton("🔍 sᴇᴀʀᴄʜ ᴀʟʟ", callback_data="search_all")],
        [InlineKeyboardButton("📊 sᴛᴀᴛs", callback_data="stats"), InlineKeyboardButton("👑 ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ", callback_data="admin_panel")],
        [InlineKeyboardButton("❓ ʜᴇʟᴘ", callback_data="help"), InlineKeyboardButton("ℹ️ ᴀʙᴏᴜᴛ", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        "<b>🌸 ʜʟᴏ ʙᴀʙʏ...</b>\n"
        "<b>✨ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴇɴᴛᴇʀᴛᴀɪɴᴍᴇɴᴛ ᴡᴏʀʟᴅ !</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎬 <b>ᴍᴀɪɴ ᴍᴇɴᴜ</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "▸ ᴄʜᴏᴏsᴇ ᴀɴʏ ᴄᴀᴛᴇɢᴏʀʏ\n"
        "▸ ᴏʀ ᴛʏᴘᴇ ɴᴀᴍᴇ ᴅɪʀᴇᴄᴛʟʏ !\n\n"
        f"⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {html.escape(DEV_USERNAME)} ⚡"
    )

    await update.message.reply_photo(
        photo=START_IMAGE,
        caption=caption,
        parse_mode='HTML',
        has_spoiler=True,
        reply_markup=reply_markup,
    )

# ==================== ANIME MENU ====================
async def anime_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 ᴀɴɪᴍᴇ ʟɪsᴛ", callback_data="anime_list")],
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴀɴɪᴍᴇ", callback_data="add_anime_admin"), InlineKeyboardButton("❌ ᴅᴇʟᴇᴛᴇ", callback_data="delete_anime_admin")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    total = len(anime_data)
    msg = "🍥 **ᴀɴɪᴍᴇ ᴍᴇɴᴜ** 🍥\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📊 ᴛᴏᴛᴀʟ ᴀɴɪᴍᴇs: {total}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "▸ ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ\n\n"
    msg += f"⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

# ==================== MOVIE MENU ====================
async def movie_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 ᴍᴏᴠɪᴇ ʟɪsᴛ", callback_data="movie_list")],
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴍᴏᴠɪᴇ", callback_data="add_movie_admin"), InlineKeyboardButton("❌ ᴅᴇʟᴇᴛᴇ", callback_data="delete_movie_admin")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    total = len(movie_data)
    msg = "🎬 **ᴍᴏᴠɪᴇ ᴍᴇɴᴜ** 🎬\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📊 ᴛᴏᴛᴀʟ ᴍᴏᴠɪᴇs: {total}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "▸ ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ\n\n"
    msg += f"⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

# ==================== K-DRAMA MENU ====================
async def kdrama_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 ᴋ-ᴅʀᴀᴍᴀ ʟɪsᴛ", callback_data="kdrama_list")],
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴋ-ᴅʀᴀᴍᴀ", callback_data="add_kdrama_admin"), InlineKeyboardButton("❌ ᴅᴇʟᴇᴛᴇ", callback_data="delete_kdrama_admin")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    total = len(kdrama_data)
    msg = "🇰 **ᴋ-ᴅʀᴀᴍᴀ ᴍᴇɴᴜ** 🇰\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📊 ᴛᴏᴛᴀʟ ᴋ-ᴅʀᴀᴍᴀs: {total}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "▸ ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ\n\n"
    msg += f"⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

# ==================== SUDO/ADMIN MANAGEMENT ====================
async def add_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_sudo(user_id):
        await update.message.reply_text("❌ ᴏɴʟʏ sᴜᴅᴏ ᴜsᴇʀ ᴄᴀɴ ᴀᴅᴅ sᴜᴅᴏ !")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ᴜsᴀɢᴇ: /add_sudo <ɪᴅ>")
        return

    try:
        new_sudo = int(context.args[0])
    except:
        await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ɪᴅ !")
        return

    if new_sudo not in SUDO_IDS:
        SUDO_IDS.append(new_sudo)
        save_sudo(SUDO_IDS)
        await update.message.reply_text(f"✅ sᴜᴅᴏ ᴜsᴇʀ ᴀᴅᴅᴇᴅ: `{new_sudo}`", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ ᴀʟʀᴇᴀᴅʏ ᴀ sᴜᴅᴏ ᴜsᴇʀ !")

async def remove_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_sudo(user_id):
        await update.message.reply_text("❌ ᴏɴʟʏ sᴜᴅᴏ ᴜsᴇʀ ᴄᴀɴ ʀᴇᴍᴏᴠᴇ sᴜᴅᴏ !")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ᴜsᴀɢᴇ: /remove_sudo <ɪᴅ>")
        return

    try:
        remove_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ɪᴅ !")
        return

    if remove_id in SUDO_IDS and remove_id != SUDO_IDS[0]:
        SUDO_IDS.remove(remove_id)
        save_sudo(SUDO_IDS)
        await update.message.reply_text(f"✅ sᴜᴅᴏ ᴜsᴇʀ ʀᴇᴍᴏᴠᴇᴅ: `{remove_id}`", parse_mode='Markdown')
    elif remove_id == SUDO_IDS[0]:
        await update.message.reply_text("❌ ᴄᴀɴɴᴏᴛ ʀᴇᴍᴏᴠᴇ ᴍᴀɪɴ sᴜᴅᴏ !")
    else:
        await update.message.reply_text("❌ ɴᴏᴛ ᴀ sᴜᴅᴏ ᴜsᴇʀ !")

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_sudo(user_id):
        await update.message.reply_text("❌ ᴏɴʟʏ sᴜᴅᴏ ᴜsᴇʀ ᴄᴀɴ ᴀᴅᴅ ᴀᴅᴍɪɴs !")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ᴜsᴀɢᴇ: /add_admin <ɪᴅ>")
        return

    try:
        new_admin = int(context.args[0])
    except:
        await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ɪᴅ !")
        return

    if new_admin not in ADMIN_IDS:
        ADMIN_IDS.append(new_admin)
        save_admins(ADMIN_IDS)
        await update.message.reply_text(f"✅ ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ: `{new_admin}`", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ !")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_sudo(user_id):
        await update.message.reply_text("❌ ᴏɴʟʏ sᴜᴅᴏ ᴜsᴇʀ ᴄᴀɴ ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴs !")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ᴜsᴀɢᴇ: /remove_admin <ɪᴅ>")
        return

    try:
        remove_id = int(context.args[0])
    except:
        await update.message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ɪᴅ !")
        return

    if remove_id in ADMIN_IDS and remove_id not in SUDO_IDS:
        ADMIN_IDS.remove(remove_id)
        save_admins(ADMIN_IDS)
        await update.message.reply_text(f"✅ ᴀᴅᴍɪɴ ʀᴇᴍᴏᴠᴇᴅ: `{remove_id}`", parse_mode='Markdown')
    elif remove_id in SUDO_IDS:
        await update.message.reply_text("❌ ᴄᴀɴɴᴏᴛ ʀᴇᴍᴏᴠᴇ sᴜᴅᴏ ᴜsᴇʀ ғʀᴏᴍ ᴀᴅᴍɪɴ !")
    else:
        await update.message.reply_text("❌ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ !")

async def list_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        await update.message.reply_text("❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ !")
        return

    msg = "👑 **sᴜᴅᴏ (ᴏᴡɴᴇʀ) ʟɪsᴛ** 👑\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, sudo in enumerate(SUDO_IDS, 1):
        if sudo == SUDO_IDS[0]:
            msg += f"▸ `{i}.` {sudo} (ᴍᴀɪɴ sᴜᴅᴏ)\n"
        else:
            msg += f"▸ `{i}.` {sudo}\n"
    msg += f"\n⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ !")
        return

    msg = "👑 **ᴀᴅᴍɪɴ ʟɪsᴛ** 👑\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    for i, admin in enumerate(ADMIN_IDS, 1):
        if admin in SUDO_IDS:
            msg += f"▸ `{i}.` {admin} (sᴜᴅᴏ/ᴏᴡɴᴇʀ)\n"
        else:
            msg += f"▸ `{i}.` {admin}\n"
    msg += f"\n⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, parse_mode='Markdown')

# ==================== LIST DISPLAYS ====================
async def show_anime_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not anime_data:
        await update.message.reply_text(f"📭 ɴᴏ ᴀɴɪᴍᴇ ᴀᴠᴀɪʟᴀʙʟᴇ ʏᴇᴛ !\n\n⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡", parse_mode='Markdown')
        return

    total = len(anime_data)
    msg = "🍥 **ᴀɴɪᴍᴇ ʟɪsᴛ** 🍥\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"✨ ᴛᴏᴛᴀʟ: {total}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, name in enumerate(list(anime_data.keys())[:25], 1):
        msg += f"▸ {i:02d}. {name}\n"

    if total > 25:
        msg += f"\n▸ + {total - 25} ᴍᴏʀᴇ...\n"

    msg += f"\n💡 ᴛʏᴘᴇ ᴛʜᴇ ɴᴀᴍᴇ ᴛᴏ ɢᴇᴛ ʟɪɴᴋ !\n⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def show_movie_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not movie_data:
        await update.message.reply_text(f"📭 ɴᴏ ᴍᴏᴠɪᴇs ᴀᴠᴀɪʟᴀʙʟᴇ ʏᴇᴛ !\n\n⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡", parse_mode='Markdown')
        return

    total = len(movie_data)
    msg = "🎬 **ᴍᴏᴠɪᴇ ʟɪsᴛ** 🎬\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"✨ ᴛᴏᴛᴀʟ: {total}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, name in enumerate(list(movie_data.keys())[:25], 1):
        msg += f"▸ {i:02d}. {name}\n"

    if total > 25:
        msg += f"\n▸ + {total - 25} ᴍᴏʀᴇ...\n"

    msg += f"\n💡 ᴛʏᴘᴇ ᴛʜᴇ ɴᴀᴍᴇ ᴛᴏ ɢᴇᴛ ʟɪɴᴋ !\n⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def show_kdrama_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not kdrama_data:
        await update.message.reply_text(f"📭 ɴᴏ ᴋ-ᴅʀᴀᴍᴀs ᴀᴠᴀɪʟᴀʙʟᴇ ʏᴇᴛ !\n\n⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡", parse_mode='Markdown')
        return

    total = len(kdrama_data)
    msg = "🇰 **ᴋ-ᴅʀᴀᴍᴀ ʟɪsᴛ** 🇰\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"✨ ᴛᴏᴛᴀʟ: {total}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, name in enumerate(list(kdrama_data.keys())[:25], 1):
        msg += f"▸ {i:02d}. {name}\n"

    if total > 25:
        msg += f"\n▸ + {total - 25} ᴍᴏʀᴇ...\n"

    msg += f"\n💡 ᴛʏᴘᴇ ᴛʜᴇ ɴᴀᴍᴇ ᴛᴏ ɢᴇᴛ ʟɪɴᴋ !\n⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, parse_mode='Markdown')

# ==================== STATS ====================
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime_total = len(anime_data)
    movie_total = len(movie_data)
    kdrama_total = len(kdrama_data)
    total = anime_total + movie_total + kdrama_total

    msg = "📊 **ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs** 📊\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🍥 ᴀɴɪᴍᴇs: {anime_total}\n"
    msg += f"🎬 ᴍᴏᴠɪᴇs: {movie_total}\n"
    msg += f"🇰 ᴋ-ᴅʀᴀᴍᴀs: {kdrama_total}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📊 ᴛᴏᴛᴀʟ ᴄᴏɴᴛᴇɴᴛ: {total}\n"
    msg += f"👑 sᴜᴅᴏ ᴏᴡɴᴇʀs: {len(SUDO_IDS)}\n"
    msg += f"👥 ᴀᴅᴍɪɴs: {len(ADMIN_IDS)}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, parse_mode='Markdown')

# ==================== HELP ====================
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📖 **ʜᴇʟᴘ ᴍᴇɴᴜ** 📖\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🎬 **ᴜsᴇʀ ᴄᴏᴍᴍᴀɴᴅs:**\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "/start - sᴛᴀʀᴛ ʙᴏᴛ\n"
    msg += "/help - sʜᴏᴡ ᴛʜɪs ᴍᴇssᴀɢᴇ\n"
    msg += "/menu - sʜᴏᴡ ᴍᴀɪɴ ᴍᴇɴᴜ\n"
    msg += "/stats - sʜᴏᴡ ʙᴏᴛ sᴛᴀᴛs\n\n"
    msg += "🎯 **ʜᴏᴡ ᴛᴏ ɢᴇᴛ ʟɪɴᴋ?**\n"
    msg += "▸ ʙᴀs ᴀɴʏ ɴᴀᴍᴇ ʟɪᴋʜᴏ\n"
    msg += "▸ ᴇx: ɴᴀʀᴜᴛᴏ, ᴋɢꜰ, ᴅᴇsᴄᴇɴᴅᴀɴᴛs ᴏғ ᴛʜᴇ sᴜɴ\n\n"
    msg += "👑 **sᴜᴅᴏ/ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:**\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "/add_anime ɴᴀᴍᴇ | ʟɪɴᴋ\n"
    msg += "/add_movie ɴᴀᴍᴇ | ʟɪɴᴋ\n"
    msg += "/add_kdrama ɴᴀᴍᴇ | ʟɪɴᴋ\n"
    msg += "/delete_anime ɴᴀᴍᴇ\n"
    msg += "/delete_movie ɴᴀᴍᴇ\n"
    msg += "/delete_kdrama ɴᴀᴍᴇ\n"
    msg += "/add_admin <ɪᴅ> - ᴀᴅᴅ ᴀᴅᴍɪɴ\n"
    msg += "/remove_admin <ɪᴅ> - ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ\n"
    msg += "/admins - ʟɪsᴛ ᴀʟʟ ᴀᴅᴍɪɴs\n"
    msg += "/add_sudo <ɪᴅ> - ᴀᴅᴅ sᴜᴅᴏ ᴏᴡɴᴇʀ\n"
    msg += "/remove_sudo <ɪᴅ> - ʀᴇᴍᴏᴠᴇ sᴜᴅᴏ\n"
    msg += "/sudo - ʟɪsᴛ ᴀʟʟ sᴜᴅᴏ ᴏᴡɴᴇʀs\n"
    msg += "/broadcast <ᴍsɢ> - sᴇɴᴅ ᴛᴏ ᴀʟʟ ᴜsᴇʀs\n\n"
    msg += f"⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, parse_mode='Markdown')

# ==================== ABOUT ====================
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"ℹ️ **ᴀʙᴏᴜᴛ ᴛʜɪs ʙᴏᴛ** ℹ️\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🎬 ɴᴀᴍᴇ: ᴇɴᴛᴇʀᴛᴀɪɴᴍᴇɴᴛ ʙᴏᴛ\n"
    msg += "📝 ᴠᴇʀsɪᴏɴ: 4.0\n"
    msg += f"👨‍💻 ᴅᴇᴠᴇʟᴏᴘᴇʀ: {DEV_USERNAME}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "📌 **ғᴇᴀᴛᴜʀᴇs:**\n"
    msg += "▸ ᴀɴɪᴍᴇ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋs\n"
    msg += "▸ ᴍᴏᴠɪᴇ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋs\n"
    msg += "▸ ᴋ-ᴅʀᴀᴍᴀ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋs\n"
    msg += "▸ sᴍᴀʀᴛ ᴀᴜᴛᴏ-ᴅᴇᴛᴇᴄᴛ\n"
    msg += "▸ sᴜᴅᴏ/ᴀᴅᴍɪɴ ʀᴏʟᴇ sʏsᴛᴇᴍ\n"
    msg += "▸ ᴍᴜʟᴛɪ ᴄᴀᴛᴇɢᴏʀʏ sᴜᴘᴘᴏʀᴛ\n\n"
    msg += f"⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"

    await update.message.reply_text(msg, parse_mode='Markdown')

# ==================== AUTO DETECT ====================
async def auto_detect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.strip()

    if message_text.startswith('/'):
        return

    normalized_msg = normalize_text(message_text.lower())

    # Check in Anime
    for name, link in anime_data.items():
        if normalize_text(name.lower()) in normalized_msg or name.lower() in message_text.lower():
            await _send_found(update, name, link, category="ᴀɴɪᴍᴇ", emoji="🍥", header="ᴀɴɪᴍᴇ ғᴏᴜɴᴅ")
            return

    # Check in Movies
    for name, link in movie_data.items():
        if normalize_text(name.lower()) in normalized_msg or name.lower() in message_text.lower():
            await _send_found(update, name, link, category="ᴍᴏᴠɪᴇ", emoji="🎬", header="ᴍᴏᴠɪᴇ ғᴏᴜɴᴅ")
            return

    # Check in K-Drama
    for name, link in kdrama_data.items():
        if normalize_text(name.lower()) in normalized_msg or name.lower() in message_text.lower():
            await _send_found(update, name, link, category="ᴋ-ᴅʀᴀᴍᴀ", emoji="📺", header="ᴋ-ᴅʀᴀᴍᴀ ғᴏᴜɴᴅ")
            return


async def _send_found(update: Update, name: str, link: str, category: str, emoji: str, header: str):
    safe_name = html.escape(name)
    safe_link = html.escape(link)
    caption = (
        f"🎯 <b>{header} !</b> 🎯\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{emoji} ɴᴀᴍᴇ: {safe_name}\n"
        f"📂 ᴄᴀᴛᴇɢᴏʀʏ: {category}\n"
        f"✅ sᴛᴀᴛᴜs: ᴀᴠᴀɪʟᴀʙʟᴇ\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 <b>ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ:</b>\n"
        f"📥 <tg-spoiler>{safe_link}</tg-spoiler>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {html.escape(DEV_USERNAME)} ⚡"
    )
    await update.message.reply_photo(
        photo=START_IMAGE,
        caption=caption,
        parse_mode='HTML',
        has_spoiler=True,
    )

# ==================== ADMIN ADD/DELETE CONTENT ====================
async def add_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ !")
        return

    if len(context.args) < 2 or "|" not in " ".join(context.args):
        await update.message.reply_text("⚠️ ғᴏʀᴍᴀᴛ: /add_anime ɴᴀᴍᴇ | ʟɪɴᴋ")
        return

    full = " ".join(context.args)
    name, link = full.split("|", 1)
    anime_data[name.strip()] = link.strip()
    save_data(ANIME_FILE, anime_data)
    await update.message.reply_text(f"✅ ᴀɴɪᴍᴇ ᴀᴅᴅᴇᴅ: {name.strip()}")

async def add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ !")
        return

    if len(context.args) < 2 or "|" not in " ".join(context.args):
        await update.message.reply_text("⚠️ ғᴏʀᴍᴀᴛ: /add_movie ɴᴀᴍᴇ | ʟɪɴᴋ")
        return

    full = " ".join(context.args)
    name, link = full.split("|", 1)
    movie_data[name.strip()] = link.strip()
    save_data(MOVIE_FILE, movie_data)
    await update.message.reply_text(f"✅ ᴍᴏᴠɪᴇ ᴀᴅᴅᴇᴅ: {name.strip()}")

async def add_kdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ !")
        return

    if len(context.args) < 2 or "|" not in " ".join(context.args):
        await update.message.reply_text("⚠️ ғᴏʀᴍᴀᴛ: /add_kdrama ɴᴀᴍᴇ | ʟɪɴᴋ")
        return

    full = " ".join(context.args)
    name, link = full.split("|", 1)
    kdrama_data[name.strip()] = link.strip()
    save_data(KDRAMA_FILE, kdrama_data)
    await update.message.reply_text(f"✅ ᴋ-ᴅʀᴀᴍᴀ ᴀᴅᴅᴇᴅ: {name.strip()}")

async def delete_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ !")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ᴜsᴀɢᴇ: /delete_anime <ɴᴀᴍᴇ>")
        return

    name = " ".join(context.args)
    if name in anime_data:
        del anime_data[name]
        save_data(ANIME_FILE, anime_data)
        await update.message.reply_text(f"✅ ᴅᴇʟᴇᴛᴇᴅ: {name}")
    else:
        await update.message.reply_text(f"❌ ɴᴏᴛ ғᴏᴜɴᴅ: {name}")

async def delete_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ !")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ᴜsᴀɢᴇ: /delete_movie <ɴᴀᴍᴇ>")
        return

    name = " ".join(context.args)
    if name in movie_data:
        del movie_data[name]
        save_data(MOVIE_FILE, movie_data)
        await update.message.reply_text(f"✅ ᴅᴇʟᴇᴛᴇᴅ: {name}")
    else:
        await update.message.reply_text(f"❌ ɴᴏᴛ ғᴏᴜɴᴅ: {name}")

async def delete_kdrama(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ !")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ᴜsᴀɢᴇ: /delete_kdrama <ɴᴀᴍᴇ>")
        return

    name = " ".join(context.args)
    if name in kdrama_data:
        del kdrama_data[name]
        save_data(KDRAMA_FILE, kdrama_data)
        await update.message.reply_text(f"✅ ᴅᴇʟᴇᴛᴇᴅ: {name}")
    else:
        await update.message.reply_text(f"❌ ɴᴏᴛ ғᴏᴜɴᴅ: {name}")

# ==================== BUTTON CALLBACK ====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back":
        await main_menu(query, context)
        await query.delete_message()

    elif data == "anime_menu":
        await anime_menu(query, context)
        await query.delete_message()

    elif data == "movie_menu":
        await movie_menu(query, context)
        await query.delete_message()

    elif data == "kdrama_menu":
        await kdrama_menu(query, context)
        await query.delete_message()

    elif data == "anime_list":
        await show_anime_list(query, context)

    elif data == "movie_list":
        await show_movie_list(query, context)

    elif data == "kdrama_list":
        await show_kdrama_list(query, context)

    elif data == "stats":
        await show_stats(query, context)

    elif data == "help":
        await help_menu(query, context)

    elif data == "about":
        await about(query, context)

    elif data == "admin_panel":
        if not is_admin(query.from_user.id):
            await query.edit_message_text("❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ !")
            return

        keyboard = [
            [InlineKeyboardButton("🍥 ᴀɴɪᴍᴇ", callback_data="anime_menu"), InlineKeyboardButton("🎬 ᴍᴏᴠɪᴇs", callback_data="movie_menu")],
            [InlineKeyboardButton("🇰 ᴋ-ᴅʀᴀᴍᴀ", callback_data="kdrama_menu")],
            [InlineKeyboardButton("👑 ᴀᴅᴍɪɴ ʟɪsᴛ", callback_data="admin_list")],
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back")]
        ]
        await query.edit_message_text("👑 **ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ** 👑\n\n▸ ᴄʜᴏᴏsᴇ ᴀ ᴄᴀᴛᴇɢᴏʀʏ", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    elif data == "admin_list":
        if not is_admin(query.from_user.id):
            await query.edit_message_text("❌ ᴀᴄᴄᴇss ᴅᴇɴɪᴇᴅ !")
            return

        msg = "👑 **ᴀᴅᴍɪɴ ʟɪsᴛ** 👑\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        for i, admin in enumerate(ADMIN_IDS, 1):
            if admin in SUDO_IDS:
                msg += f"▸ `{i}.` {admin} (sᴜᴅᴏ)\n"
            else:
                msg += f"▸ `{i}.` {admin}\n"
        msg += f"\n⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME} ⚡"
        await query.edit_message_text(msg, parse_mode='Markdown')

    elif data == "add_anime_admin":
        await query.edit_message_text("➕ ғᴏʀᴍᴀᴛ: /add_anime ɴᴀᴍᴇ | ʟɪɴᴋ\n📝 ᴇx: /add_anime ɴᴀʀᴜᴛᴏ | https://example.com")

    elif data == "delete_anime_admin":
        await query.edit_message_text("❌ ғᴏʀᴍᴀᴛ: /delete_anime ɴᴀᴍᴇ\n📝 ᴇx: /delete_anime ɴᴀʀᴜᴛᴏ")

    elif data == "add_movie_admin":
        await query.edit_message_text("➕ ғᴏʀᴍᴀᴛ: /add_movie ɴᴀᴍᴇ | ʟɪɴᴋ\n📝 ᴇx: /add_movie ᴋɢꜰ | https://example.com")

    elif data == "delete_movie_admin":
        await query.edit_message_text("❌ ғᴏʀᴍᴀᴛ: /delete_movie ɴᴀᴍᴇ\n📝 ᴇx: /delete_movie ᴋɢꜰ")

    elif data == "add_kdrama_admin":
        await query.edit_message_text("➕ ғᴏʀᴍᴀᴛ: /add_kdrama ɴᴀᴍᴇ | ʟɪɴᴋ\n📝 ᴇx: /add_kdrama ᴅᴇsᴄᴇɴᴅᴀɴᴛs ᴏғ ᴛʜᴇ sᴜɴ | https://example.com")

    elif data == "delete_kdrama_admin":
        await query.edit_message_text("❌ ғᴏʀᴍᴀᴛ: /delete_kdrama ɴᴀᴍᴇ\n📝 ᴇx: /delete_kdrama ᴅᴇsᴄᴇɴᴅᴀɴᴛs ᴏғ ᴛʜᴇ sᴜɴ")

    elif data == "search_all":
        await query.edit_message_text("🔍 **sᴇᴀʀᴄʜ ɪɴ ᴀʟʟ ᴄᴀᴛᴇɢᴏʀɪᴇs**\n\n▸ ʙᴀs ᴛʏᴘᴇ ᴛʜᴇ ɴᴀᴍᴇ ᴏғ ᴀɴʏ ᴀɴɪᴍᴇ/ᴍᴏᴠɪᴇ/ᴋᴅʀᴀᴍᴀ\n▸ ʙᴏᴛ ᴡɪʟʟ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ғɪɴᴅ ᴀɴᴅ sᴇɴᴅ ᴛʜᴇ ʟɪɴᴋ !\n\n⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ @ll_YOUR_ASHISH_BRO_ll", parse_mode='Markdown')

# ==================== START COMMAND ====================
async def _play_greet_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show GREET lines one-by-one in the chat, then delete before the real menu."""
    chat_id = update.effective_chat.id
    try:
        loading = await context.bot.send_message(
            chat_id=chat_id, text=GREET[0], parse_mode='HTML'
        )
    except Exception:
        return
    for line in GREET[1:]:
        await asyncio.sleep(0.7)
        try:
            await loading.edit_text(line, parse_mode='HTML')
        except Exception:
            pass
    await asyncio.sleep(0.7)
    try:
        await loading.delete()
    except Exception:
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        remember_user(update.effective_user.id)
    await _play_greet_animation(update, context)
    await main_menu(update, context)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        remember_user(update.effective_user.id)
    await main_menu(update, context)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_stats(update, context)

# ==================== BROADCAST (sudo + admin) ====================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not (is_sudo(user_id) or is_admin(user_id)):
        await update.message.reply_text("❌ ᴏɴʟʏ ᴏᴡɴᴇʀ / sᴜᴅᴏ / ᴀᴅᴍɪɴ ᴄᴀɴ ʙʀᴏᴀᴅᴄᴀsᴛ !")
        return

    # Allow either: /broadcast <text>   OR   reply to a message with /broadcast
    text = " ".join(context.args).strip()
    reply_target = update.message.reply_to_message
    if not text and not reply_target:
        await update.message.reply_text(
            "⚠️ ᴜsᴀɢᴇ:\n"
            "▸ /broadcast <ʏᴏᴜʀ ᴍᴇssᴀɢᴇ>\n"
            "▸ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ /broadcast"
        )
        return

    targets = list(USER_IDS)
    status = await update.message.reply_text(
        f"📢 sᴛᴀʀᴛɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ {len(targets)} ᴜsᴇʀs..."
    )

    sent = 0
    failed = 0
    blocked_users = []
    for uid in targets:
        try:
            if reply_target:
                await context.bot.copy_message(
                    chat_id=uid,
                    from_chat_id=reply_target.chat_id,
                    message_id=reply_target.message_id,
                )
            else:
                await context.bot.send_message(chat_id=uid, text=text)
            sent += 1
        except Exception:
            failed += 1
            blocked_users.append(uid)
        # gentle pace — Telegram allows ~30 msg/sec but be safe
        await asyncio.sleep(0.05)

    # Auto-prune users who blocked the bot
    if blocked_users:
        for uid in blocked_users:
            if uid in USER_IDS:
                USER_IDS.remove(uid)
        save_users(USER_IDS)

    summary = (
        "📢 <b>ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ sᴇɴᴛ: {sent}\n"
        f"❌ ғᴀɪʟᴇᴅ: {failed}\n"
        f"👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs: {len(targets)}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {html.escape(DEV_USERNAME)} ⚡"
    )
    await update.message.reply_text(summary, parse_mode='HTML')

# ==================== MAIN ====================
def main():
    print("🤖 ʙᴏᴛ sᴛᴀʀᴛɪɴɢ...")
    print(f"⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ {DEV_USERNAME}")
    print(f"🍥 ᴀɴɪᴍᴇs: {len(anime_data)}")
    print(f"🎬 ᴍᴏᴠɪᴇs: {len(movie_data)}")
    print(f"🇰 ᴋ-ᴅʀᴀᴍᴀs: {len(kdrama_data)}")
    print(f"👑 sᴜᴅᴏ ᴏᴡɴᴇʀs: {len(SUDO_IDS)}")
    print(f"👥 ᴀᴅᴍɪɴs: {len(ADMIN_IDS)}")
    print(f"👤 ᴋɴᴏᴡɴ ᴜsᴇʀs: {len(USER_IDS)}")
    print(f"⏳ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ: {AUTO_DELETE_SECONDS}s")

    app = Application.builder().token(BOT_TOKEN).build()

    # User commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("help", help_menu))
    app.add_handler(CommandHandler("stats", stats_command))

    # Admin commands
    app.add_handler(CommandHandler("add_anime", add_anime))
    app.add_handler(CommandHandler("add_movie", add_movie))
    app.add_handler(CommandHandler("add_kdrama", add_kdrama))
    app.add_handler(CommandHandler("delete_anime", delete_anime))
    app.add_handler(CommandHandler("delete_movie", delete_movie))
    app.add_handler(CommandHandler("delete_kdrama", delete_kdrama))

    # SUDO commands
    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(CommandHandler("remove_admin", remove_admin))
    app.add_handler(CommandHandler("admins", list_admins))
    app.add_handler(CommandHandler("add_sudo", add_sudo))
    app.add_handler(CommandHandler("remove_sudo", remove_sudo))
    app.add_handler(CommandHandler("sudo", list_sudo))

    # Broadcast (sudo + admin)
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Button callback
    app.add_handler(CallbackQueryHandler(button_callback))

    # Auto detect
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_detect))

    print("🚀 ʙᴏᴛ ɪs ʀᴜɴɴɪɴɢ...")
    app.run_polling()

if __name__ == "__main__":
    main()
