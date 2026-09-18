import asyncio






import json






import os






import random






import time






import tempfile






import urllib.request






import urllib.parse






import platform






import aiohttp






import telegram.error






from datetime import datetime, timedelta, timezone






from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, InputMediaVideo, InputMediaPhoto






from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler






from telegram.request import HTTPXRequest






import logging






from concurrent.futures import ThreadPoolExecutor






from typing import List













import subprocess






import re






import io













# Configure logging






logging.basicConfig(level=logging.INFO)






logger = logging.getLogger(__name__)













# Directory to store saved group profile pictures






PFP_DIR = os.path.join(os.path.dirname(__file__), "pfp_pool")






os.makedirs(PFP_DIR, exist_ok=True)













# Active PFP rotation tasks per chat (chat_id -> (task, stop_event))






pfp_tasks: dict[int, tuple[asyncio.Task, asyncio.Event]] = {}













# Global HTTP session and semaphore for efficient downloads






_http_session: aiohttp.ClientSession | None = None






DOWNLOAD_SEMAPHORE = asyncio.Semaphore(15)




















async def get_http_session() -> aiohttp.ClientSession:






    global _http_session






    if _http_session is None:






        _http_session = aiohttp.ClientSession()






    return _http_session













# ==================== MENU CONFIGURATION ====================




















class MenuConfig:






    """Configuration for each menu category with its own media"""













    def __init__(self):






        self.menus = {






            "main": {






                "title": "⛩️ 𝐑EBEL .⋆ · ᴀɴɪᴍᴇ ᴛᴇʀᴍɪɴᴀʟ ⛩️",






                "video": "https://files.catbox.moe/jpyae4.mp4",






                "type": "video",






                "caption": """🌸 ⊹ **𝐑 E B E L ·  A N I M E  T E R M I N A L** ⊹ 🌸

🕯️ ‧˚ **A T T A C K  M O D E S**
ʚ `⌜ attack ⌟`  ⊹  Destroy Them All

🎵 ‧˚ **M U S I C  S Y S T E M**
ʚ `⌜ music ⌟`  ⊹  Soul Melodies

⚙️ ‧˚ **S E T T I N G S**
ʚ `⌜ settings ⌟`  ⊹  Control Your Power

🛑 ‧˚ **S T O P  C M D S**
ʚ `⌜ stop ⌟`  ⊹  End The Battle

👑 ‧˚ **A D M I N  C T R L**
ʚ `⌜ admin ⌟`  ⊹  Rule The Realm

🫧 ‧˚ **U T I L I T Y**
ʚ `⌜ utility ⌟`  ⊹  Shinobi Tools

✧ *Powered by REBEL  Supremacy* ✧"""






            },






            "attack": {






                "title": "🗡️ ᴀᴛᴛᴀᴄᴋ ᴍᴏᴅᴇs",






                "video": "https://files.catbox.moe/gi4nm8.mp4",






                "type": "video",






                "caption": """🌸 ⊹ **A T T A C K  ·  D A R K  A R T S** ⊹ 🌸

🍨 ‧˚ **N A M E  C H A N G E R**
ʚ `~nc1 <name>`  ⊹  Raid Assault
ʚ `~nc2 <name>`  ⊹  God Mode
ʚ `~nc3 <name>`  ⊹  Time Shift
ʚ `~nc4 <name>`  ⊹  Custom Mix

🕯️ ‧˚ **S P A M  S T R I K E**
ʚ `~spamemo <text>`  ⊹  Emoji Spam
ʚ `~spam <text>`  ⊹  Text Spam
ʚ `~raidspam <name>`  ⊹  Raid Spam
ʚ `~swipe <target>`  ⊹  Swipe Attack
ʚ `~slidespam`  ⊹  Slide Spam

🫧 ‧˚ **S P E C I A L  A B I L I T I E S**
ʚ `~over <target>`  ⊹  Game Over
ʚ `~raidnc <name>`  ⊹  Raid NC

🍰 ‧˚ **E M E R G E N C Y**
ʚ `~stop`  ⊹  Abort Attack

✧ *Powered by REBEL  Supremacy* ✧"""






            },






            "music": {






                "title": "🎵 ᴍᴜsɪᴄ · sʜɪɴᴅᴇɴ",






                "video": "https://files.catbox.moe/jpyae4.mp4",






                "type": "video",






                "caption": """🌸 ⊹ **M U S I C  ·  S O U L  M E L O D I E S** ⊹ 🌸

🎵 ‧˚ **M U S I C  C O M M A N D S**
ʚ `~song <name>`  ⊹  Search & Download
ʚ `~spotify <name>`  ⊹  Spotify Search
ʚ `~yt <name>`  ⊹  YouTube Stream
ʚ `~playlist <url>`  ⊹  Play Playlist

🎭 ‧˚ **V O I C E  J U T S U**
ʚ `~tempest <text>`  ⊹  AI Voice
ʚ `~animevn <chars> <text>`  ⊹  Anime Voice
ʚ `~voices`  ⊹  List Voices
ʚ `~clonevn`  ⊹  Clone Voice

✧ *Powered by Rebel  & Tempest* ✧"""






            },






            "settings": {






                "title": "⚙️ sᴇᴛᴛɪɴɢs · ᴄᴏɴᴛʀᴏʟ",






                "video": "https://files.catbox.moe/gi4nm8.mp4",






                "type": "video",






                "caption": """🌸 ⊹ **S E T T I N G S  ·  C O N T R O L  P A N E L** ⊹ 🌸

⚡ ‧˚ **S P E E D  C O N T R O L**
ʚ `~speed <0-5>`  ⊹  Set Delay
ʚ `~delay <0.001-0.5>`  ⊹  Fine Tune
ʚ `~ncthreads <1-20>`  ⊹  NC Threads
ʚ `~spamthreads <20-50>`  ⊹  Spam Threads

🎬 ‧˚ **B O T  C O N F I G**
ʚ `~setprefix <p>`  ⊹  Change Prefix
ʚ `~setvideomain`  ⊹  Set Main Video
ʚ `~setvideoattack`  ⊹  Set Attack Video
ʚ `~setvideomusic`  ⊹  Set Music Video
ʚ `~setvideosettings`  ⊹  Settings Video
ʚ `~setvideosstop`  ⊹  Stop Video
ʚ `~setvideoadmin`  ⊹  Admin Video
ʚ `~setvideoutility`  ⊹  Utility Video
ʚ `~setvideostatus`  ⊹  Status Video
ʚ `~setvideoover`  ⊹  GameOver Video

✧ *Settings Apply Instantly* ✧"""






            },






            "stop": {






                "title": "🛑 sᴛᴏᴘ · ᴄᴏᴍᴍᴀɴᴅs",






                "video": "https://files.catbox.moe/jpyae4.mp4",






                "type": "video",






                "caption": """🌸 ⊹ **S T O P  ·  C E A S E F I R E** ⊹ 🌸

🕯️ ‧˚ **G L O B A L  S T O P S**
ʚ `~stop`  ⊹  Stop Current Action
ʚ `~stopall`  ⊹  Stop All Actions
ʚ `~stopspam`  ⊹  Halt Spam Engine
ʚ `~stopnc`  ⊹  Halt Name Changer

🎯 ‧˚ **S P E C I F I C  S T O P S**
ʚ `~stopraidnc`  ⊹  Halt Raid NC
ʚ `~stoprohitnc`  ⊹  Halt ROHIT  NC
ʚ `~stopswipe`  ⊹  Halt Swipe
ʚ `~stopphoto`  ⊹  Halt Photo Loop

🫧 ‧˚ **E M E R G E N C Y  E X I T**
ʚ `~bye`  ⊹  Quick Leave
ʚ `~leave`  ⊹  All Bots Leave

✧ *~stopall — Emergency Killswitch* ✧"""






            },






            "admin": {






                "title": "👑 ᴀᴅᴍɪɴ · ᴄᴏɴᴛʀᴏʟ",






                "video": "https://files.catbox.moe/gi4nm8.mp4",






                "type": "video",






                "caption": """🌸 ⊹ **A D M I N  ·  S H O G U N A T E** ⊹ 🌸

👑 ‧˚ **U S E R  M A N A G E M E N T**
ʚ `~entrust <id>`  ⊹  Grant Admin
ʚ `~revoke <id>`  ⊹  Remove Admin
ʚ `~list`  ⊹  List Admins
ʚ `~beta`  ⊹  Add Sudo User

🤖 ‧˚ **B O T  M A N A G E M E N T**
ʚ `~upall`  ⊹  Promote All Bots
ʚ `~addbot <u>`  ⊹  Add Bot
ʚ `~plus <u>`  ⊹  Invite Bot

📊 ‧˚ **S Y S T E M  C O N T R O L**
ʚ `~status`  ⊹  Bot Status
ʚ `~godmode`  ⊹  God Mode
ʚ `~threadstatus`  ⊹  Thread Status

✧ *Shogun-Only Commands* ✧"""






            },






            "utility": {






                "title": "🌀 ᴜᴛɪʟɪᴛʏ · sʜɪɴᴏʙɪ",






                "video": "https://files.catbox.moe/jpyae4.mp4",






                "type": "video",






                "caption": """🌸 ⊹ **U T I L I T Y  ·  R E B E L T O O L S** ⊹ 🌸

📸 ‧˚ **P H O T O  J U T S U**
ʚ `~savephoto`  ⊹  Save Group Photo
ʚ `~startphoto`  ⊹  Start Photo Loop
ʚ `~stopphoto`  ⊹  Stop Photo Loop
ʚ `~clearphotos`  ⊹  Clear Saved Photos

🎭 ‧˚ **S T I C K E R  J U T S U**
ʚ `~newsticker`  ⊹  Create Sticker
ʚ `~delsticker`  ⊹  Delete Sticker
ʚ `~multisticker`  ⊹  Multi Sticker
ʚ `~stickerstatus`  ⊹  Sticker Status

📊 ‧˚ **S T A T U S  S E N S O R**
ʚ `~status`  ⊹  Bot Status
ʚ `~active`  ⊹  Active Bots
ʚ `~ping`  ⊹  Latency Check
ʚ `~myid`  ⊹  Your User ID

✧ *All Utility Commands* ✧"""






            }






        }













    def get_menu(self, key):






        menu = self.menus.get(key, self.menus["main"]).copy()






        if 'bot_config' in globals():






            custom_media = bot_config.get(f"media_{key}")






            custom_type = bot_config.get(f"media_{key}_type")






            if custom_media and custom_type:






                menu["video"] = custom_media






                menu["type"] = custom_type






        return menu




















NC_TEMPLATES = {






    "nc1": "{base} {emo} 匚卄ㄩ卩 ᥅ꪖꪀᦔﺃᛕꫀ ᥇ꪖᥴᥴ𝙃ꫀ 𒈙⸻🩵𒈙⸻❤️𒈙⸻🩷𒈙⸻🧡𒈙⸻💛𒈙⸻💚𒈙⸻💙𒈙⸻💜𒈙⸻🖤𒈙⸻🩶𒈙⸻🤍𒈙⸻  {heart}",






    
    "nc2": " {base} {emo} 𝐃ᴇᴋʜ ᴀᴀᴊ ᴛᴇʀɪ 𝐌ᴀᴀ ᴋᴀ ɴᴀɴɢᴀ 𝐍𝐚𝐜𝐡 ᴅɪᴋʜᴀᴜ💙𒐫🌿𒐫💚𒐫🍃𒐫💜𒐫🌷𒐫🩵𒐫🌸𒐫🧡𒐫☘️𒐫💛𒐫🌻𒐫❤️𒐫🍀𒐫🩷𒐫🌼𒐫🤍𒐫🪴𒐫💙𒐫🌿𒐫💚𒐫🌸𒐫🩵𒐫🍃𒐫💜𒐫🌷𒐫🧡𒐫☘️𒐫💛𒐫🌻𒐫❤️𒐫🍀𒐫🩷𒐫🌼𒐫🤍𒐫🪴𒐫💙𒐫🌿𒐫",






    
    "nc3": "{emo}{base}⁀➷𝐓eʀʏ 𝐌ᴀᴀ 𝐊o 𝐂ʜᴜᴅɴe 𝐊ᴀ 𝐓ɪᴍe 𝐇6ɢʏᴀ⁀➷{time} {emo}",






    "nc4": "{base} 𓂃{pattern}"






}




















menu_config = MenuConfig()













# ==================== MENU KEYBOARD ====================




















def get_main_keyboard():






    keyboard = [






        [






            InlineKeyboardButton("🗡️ Attack", callback_data="menu_attack"),






            InlineKeyboardButton("🎵 Music", callback_data="menu_music"),






            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")






        ],






        [






            InlineKeyboardButton("🛑 Stop Cmds", callback_data="menu_stop"),






            InlineKeyboardButton("👑 Admin Ctrl", callback_data="menu_admin"),






            InlineKeyboardButton("🌀 Utility", callback_data="menu_utility")






        ],






        [






            InlineKeyboardButton("📊 Status", callback_data="status"),






            InlineKeyboardButton("📖 Full Help", callback_data="help_full")






        ]






    ]






    return InlineKeyboardMarkup(keyboard)




















def get_back_keyboard():






    keyboard = [






        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="menu_main")]






    ]






    return InlineKeyboardMarkup(keyboard)













# ==================== NC TEMPLATES ====================




















def escape_md(text):






    chars = r'_*[]()~`>#+-=|{}.!'






    return re.sub(f'([{re.escape(chars)}])', r'\\\1', text)




















try:






    import psutil






except ImportError:






    psutil = None













CHAT_ID = 8831661619






OWNER_ID = 8831661619





ADMIN_FILE = "rebel.json"






CONFIG_FILE = "rebel_config.json"













START_TIME = time.time()






TOTAL_MESSAGES_SENT = 0






TOTAL_NC_CHANGES = 0













def load_admins():






    if os.path.exists(ADMIN_FILE):






        try:






            with open(ADMIN_FILE, 'r') as f:






                return set(json.load(f))






        except:






            return set()






    return set()













def save_admins(admins):






    try:






        with open(ADMIN_FILE, 'w') as f:






            json.dump(list(admins), f)






    except:






        pass













admin_ids = load_admins()






admin_ids.add(OWNER_ID)






admin_ids.add(8831661619)













def is_admin(user_id):






    return user_id in admin_ids













def only_admin(func):






    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):






        if not update or not update.effective_user:






            return






        if not is_admin(update.effective_user.id):






            if update.message:






                await update.message.reply_text("❌ 𝐑ᴏʜɪᴛ ⋆ ˚｡⋆୨୧˚ 𝐑EBEL .⋆ ˚୨୧⋆｡˚ ⋆ 𝐒ᴇ 𝐒ᴜᴅᴏ 𝐋ᴇᴋᴇ 𝐀ᴀ😂")






            return






        return await func(update, context)






    return wrapper













def only_sudo(func):






    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):






        if not update or not update.effective_user:






            return






        uid = update.effective_user.id






        if uid == OWNER_ID or uid == 8831661619:






            return await func(update, context)






        if update.message:






            await update.message.reply_text("❌ 𝐑ᴏʜɪᴛ ⋆ ˚｡⋆୨୧˚ 𝐑EBEL .⋆ ˚୨୧⋆｡˚ ⋆ 𝐒ᴇ 𝐒ᴜᴅᴏ 𝐋ᴇᴋᴇ 𝐀ᴀ🤢")






        return






    return wrapper




















def load_config():






    if os.path.exists(CONFIG_FILE):






        try:






            with open(CONFIG_FILE, 'r') as f:






                return json.load(f)






        except:






            return {}






    return {}




















def save_config(cfg):






    try:






        with open(CONFIG_FILE, 'w') as f:






            json.dump(cfg, f)






    except:






        pass




















bot_config = load_config()






CMD_PREFIX = bot_config.get("prefix", "~")






DEFAULT_VIDEO_URL = bot_config.get(






    "video_url", "https://files.catbox.moe/gi4nm8.mp4")






DEFAULT_HELP_VIDEO_URL = bot_config.get(






    "help_video_url", "https://files.catbox.moe/jpyae4.mp4")






DEFAULT_GAMEOVER_VIDEO_URL = bot_config.get(






    "gameover_video_url", "https://files.catbox.moe/gi4nm8.mp4")













THREAD_POOL = ThreadPoolExecutor(max_workers=200)






MAX_CONCURRENT_TASKS = 500













CURRENT_DELAY = 0.0






BATCH_SIZE = 100




















def get_delay():






    global CURRENT_DELAY






    return CURRENT_DELAY




















def set_delay(value):






    global CURRENT_DELAY






    if 0 <= value <= 5:






        CURRENT_DELAY = value






        return True






    return False




















BOT_COOLDOWNS = {}




















async def safe_set_chat_title(bot, chat_id, title):






    global BOT_COOLDOWNS






    bot_id = getattr(bot, "id", None)













    if bot_id:






        now = time.time()






        cooldown_until = BOT_COOLDOWNS.get(bot_id, 0)






        if cooldown_until > now:






            wait = cooldown_until - now






            await asyncio.sleep(wait)






            return False













    safe_title = title[:128]






    try:






        await bot.set_chat_title(chat_id, safe_title)






        return True






    except telegram.error.RetryAfter as e:






        if bot_id:






            BOT_COOLDOWNS[bot_id] = time.time() + e.retry_after






        await asyncio.sleep(e.retry_after)






    except Exception:






        pass






    return False













def _load_tokens_from_env():
    """Load Telegram bot tokens from Railway environment variables only."""
    raw = (
        os.getenv("BOT_TOKENS")
        or os.getenv("BOT_TOKEN")
        or os.getenv("TELEGRAM_BOT_TOKENS")
        or os.getenv("TELEGRAM_BOT_TOKEN")
        or ""
    )
    return [token.strip() for token in re.split(r"[\s,]+", raw) if token.strip()]


TOKENS = _load_tokens_from_env()













NC_EMOJIS = ["🤡", "🥸", "😶‍🌫️", "🫠", "🥴", "🤑", "😈", "👿", "😵‍💫", "🤧", "🥲",






             "😬", "🫡", "🧑‍💻", "🤪", "😎", "🤓", "🧐", "🤯", "🥳", "😏", "😒", "😞", "😔", "😋"]






NC_HEARTS = ["🩷", "♥️", "❤️‍🩹", "💝", "🤍", "🩶", "🖤", "🤎", "💜", "💙", "🩵",






             "💚", "💛", "🧡", "❤️", "💗", "💔", "❣️", "💕", "💞", "💓", "💖", "💘", "💌"]






TIMENC_EMOJIS = ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"]






NC_PATTERNS = ["🎀", "🌸", "🌺", "🌷", "🌹", "💐", "✨", "⭐", "🌟",






               "💫", "⚡", "🔥", "💎", "🎪", "🎨", "🖌️", "🎭", "🎯", "🏆", "🎲"]






MAX_THREADS = 50






MIN_THREADS = 20













# ==================== SPAM TEXTS & EMOJIS ====================













RAID_TEXTS = [






    "×~🌷GAY🌷×~", "~×🌼BITCH🌼×~", "~×🌻LESBIAN🌻×~", "~×🌺CHAPRI🌺×~",






    "~×🌹TMKC🌹×~", "~×🏵️TMR🏵×~️", "~×🪷TMKB🪷×~", "~×💮CHUS💮×~",






    "~×🌸HAKLE🌸×~", "~×🌷GAREEB🌷×~", "~×🌼RANDY🌼×~", "~×🌻POOR🌻×~",






    "~×🌺TATTI🌺×~", "~×🌹CHOR🌹×~", "~×🏵️CHAMAR🏵️×~", "~×🪷SPERM COLLECTOR🪷×~",






    "~×💮CHUTI LULLI💮×~", "~×🌸KALWA🌸×~", "~×🌷CHUD🌷×~", "~×🌼CHUTKHOR🌼×~",






    "~×🌻BAUNA🌻×~", "~×🌺MOTE🌺×~", "~×🌹GHIN ARHA TUJHSE🌹×~", "~×🏵️CHI POOR🏵×~️",






    "~🪷PANTY CHOR🪷~", "~×💮LAND CHUS💮×~", "~×🌸MUH MAI LEGA🌸×~", "~×🌷GAND MARE 🌷×~",






    "~×🌼MOCHI WALE 🌼×~", "~×🌻GANDMARE 🌻×~", "~×🌺KIDDE 🌺×~", "~×🌹LAMO 🌹×~",






    "~×🏵️BHIKARI 🏵×~️", "~×🪷MULLE 🪷×~", "~×💮NAJAYESH LADKE 💮×~", "~×🌸GULAM 🌸×~",






    "~×🌷CHAMCHA🌷×~", "~×🌼EWW 🌼×~", "~×🌻CHOTE TATTE 🌻×~", "~×🌺SEX WORKER 🌺×~",






    "~×🌹CHINNAR MA KE LADKE 🌹×~"






]













CSWORD_TEXTS = [






    "TMKC", "TMKB", "TBKC", "TMR", "HAKLE", "CHUD NA", "LAND LE", "CHAL MA CHUDA",






    "GANDA CHUDEGA", "TERA BAAP FARMER", "SPEED BADHA", "GAREEB", "PREGENT HAI?",






    "CHI YAR CHUDA", "JNL", "KUTIYA", "CHUDDKAR", "GULAM", "BHAG YEHA SE",






    "BAAP BANA SAM KO", "TU MERA BETA", "OYE RANDY", "MAR GYA"






]













NCBRA_TEXTS = [






    "TERI बहन KI BRA 👙", "TERI  माँ KI BRA 👙", "TERI दादी KI BRA 👙", "TERI चाची KI BRA 👙",






    "TERE पिता KA BRA👙", "TERE भाई' KA BRA 👙", "TERE दादा KA BRA 👙", "TERE चाचा KA BRA 👙",






    "TERE मोसी KA BRA 👙", "TERE मोसा KA BRA 👙", "TERI पत्नी KI BRA 👙", "TERI सास KA BRA 👙",






    "TERE ससुर KA BRA 👙", "TERE खाला KA BRA 👙", "TERE सीता MA KA BRA 👙", "TERE फातिमा KA BRA 👙",






    "TERE mausi KA BRA 👙", "TERE dadi KA BRA 👙"






]













SWIPE_TEXTS = [






    "{target} TMKC", "{target} TMKL", "{target} TERI MA RANDY",






    "{target} TERI MA NANGI", "{target} BHAG MAT BHANGI",






    "{target} RANDY MA KI CHUT", "{target} CHUDWANE AYE",






    "{target} BHAGODEE", "{target} GANDI NAALI KE KEEDE",






    "{target} TMKB", "{target} TERI MA KI CHUT ME HATHI",






    "{target} TERI MA KA BHOSDA", "{target} RANDYA",






    "{target} CHAPRI MA KA LADKA", "{target} TERI MA CHUDGYI",






    "{target} TERI MA KA REAPE"






]













# ==================== SPAM STATE ====================













group_tasks = {}          # {chat_id: [tasks]}






spam_tasks = {}           # {chat_id: [tasks]}






swipe_tasks = {}          # {chat_id: {target: [tasks]}}






rishunc_tasks = {}          # {chat_id: [tasks]}






photo_tasks = {}          # {chat_id: task}






chat_photos = {}          # {chat_id: [file_ids]}






slide_targets = set()     # {user_id}






slidespam_targets = set()  # {user_id}













# ==================== SPAM LOOP FUNCTIONS ====================




















async def spam_loop(bot, chat_id, text, delay=0.5):






    """Generic spam loop"""






    while True:






        try:






            await bot.send_message(chat_id, text)






            await asyncio.sleep(delay)






        except telegram.error.RetryAfter as e:






            await asyncio.sleep(float(e.retry_after) + 1.0)






        except asyncio.CancelledError:






            return






        except Exception:






            await asyncio.sleep(1.0)




















async def raidspam_loop(bot, chat_id, name):






    """RAID SPAM with multipliers"""






    i = 0






    multipliers = [10, 20, 25]






    emojis = ["🐉", "🐲", "🔥"]






    patterns = [






        "𝐴𝐴𝑀 𝑇𝐻𝑂𝐷𝑈 𝐿𝐴𝑇𝐴𝐾 𝐿𝐴𝑇𝐴𝐾 𝐾𝐸 {name}  𝐾𝐼           𝑀𝐴𝐴 𝐾𝑂 𝐶𝐻𝑂𝐷𝑈 𝑃𝐴𝑇𝐴𝐾 𝑃𝐴𝑇𝐴𝐾 𝐾𝐸 {emo}__,____/𒀸",






        "𝑂𝑌𝐸 {name} 𝑇𝐸𝑅𝐼 𝑀𝐴𝐴 𝐾𝐼 𝐶𝐻𝑈𝑇 𝑀𝐸 𝑊𝐻𝐸𝐸𝐿 𝐶𝐻𝐴𝐼𝑅 {emo}⚔️",






        "𝑇𝐸𝑅𝐼 𝐵𝐸𝐻𝐸𝑁 𝐾𝐸 𝐵𝑅𝐴 𝑀𝐸 𝐶𝐻𝑈𝐻𝐴 𝐶𝐻𝑂𝐷𝐷 𝐷𝑈𝑁𝐺𝐴 {name} {emo}💀",






        "𝗥EBEL 𝐵𝑂𝑇 𝐾𝐸 𝐴𝐺𝐸 𝑇𝐸𝑅𝐼 𝑀𝐴𝐴 𝑁𝐴𝑁𝐺𝐼 {name} {emo}🔥"






    ]






    while True:






        try:






            mult = multipliers[i % len(multipliers)]






            emo = emojis[i % len(emojis)]






            pattern = patterns[i % len(patterns)]






            base_text = pattern.format(name=name, emo=emo)






            spam_text = (base_text + "\n") * mult






            await bot.send_message(chat_id, spam_text)






            i += 1






            await asyncio.sleep(0.5)






        except telegram.error.RetryAfter as e:






            await asyncio.sleep(float(e.retry_after) + 1.0)






        except asyncio.CancelledError:






            return






        except Exception:






            await asyncio.sleep(0.5)




















async def swipe_loop(bot, chat_id, target):






    """Swipe attack loop"""






    while True:






        try:






            text = random.choice(SWIPE_TEXTS).format(target=target)






            await bot.send_message(chat_id, text)






            await asyncio.sleep(0.5)






        except telegram.error.RetryAfter as e:






            await asyncio.sleep(float(e.retry_after) + 1.0)






        except asyncio.CancelledError:






            return






        except Exception:






            await asyncio.sleep(0.5)




















async def nc5_loop(bot, chat_id, base_text):






    """CSWORD name changer loop"""






    i = 0






    while True:






        try:






            text = CSWORD_TEXTS[i % len(CSWORD_TEXTS)]






            await safe_set_chat_title(bot, chat_id, f"{base_text} {text}")






            i += 1






            await asyncio.sleep(CURRENT_DELAY if CURRENT_DELAY > 0 else 0.001)






        except asyncio.CancelledError:






            return






        except Exception:






            await asyncio.sleep(0.5)




















async def nc6_loop(bot, chat_id, base_text):






    """NCBRA name changer loop"""






    i = 0






    while True:






        try:






            text = NCBRA_TEXTS[i % len(NCBRA_TEXTS)]






            await safe_set_chat_title(bot, chat_id, f"{base_text} {text}")






            i += 1






            await asyncio.sleep(CURRENT_DELAY if CURRENT_DELAY > 0 else 0.001)






        except asyncio.CancelledError:






            return






        except Exception:






            await asyncio.sleep(0.5)




















async def rebelnc_loop(bot, chat_id, base_text, delay=0.001):






    """rebelnc name changer loop"""






    i = 0






    rishunc_emojis = [






        "×🌼×", "×🌻×", "×🪻×", "×🏵️×", "×💮×", "×🌸×", "×🪷×", "×🌷×",






        "×🌺×", "×🥀×", "×🌹×", "×💐×", "×💋×", "×❤️‍🔥×", "×❤️‍🩹×", "×❣️×"






    ]






    while True:






        try:






            emo = rishunc_emojis[i % len(rishunc_emojis)]






            await safe_set_chat_title(bot, chat_id, f"{emo} {base_text} {emo}")






            i += 1






            await asyncio.sleep(delay)






        except asyncio.CancelledError:






            return






        except Exception:






            await asyncio.sleep(0.5)




















# Backward-compatible alias used by the existing rishunc commands.
rishunc_loop = rebelnc_loop


async def raidnc_loop(bot, chat_id, prefix):






    """RAID NC loop with hearts"""






    i = 0






    hearts = [






        "🩷", "♥️", "❤️‍🩹", "💝", "🤍", "🩶", "🖤", "🤎", "💜",






        "💙", "🩵", "💚", "💛", "🧡", "❤️", "💗", "💔"






    ]






    while True:






        try:






            emo = hearts[i % len(hearts)]






            title = f"{prefix} ᵗᵉʳⁱ ᵐᵃᵃᴄʜɪɴꫝʟ ({emo})"






            await safe_set_chat_title(bot, chat_id, title)






            i += 1






            await asyncio.sleep(CURRENT_DELAY if CURRENT_DELAY > 0 else 0.001)






        except asyncio.CancelledError:






            return






        except Exception:






            await asyncio.sleep(0.5)




















async def photo_loop(bot, chat_id, photos):






    """Photo changer loop"""






    while True:






        try:






            if chat_id not in chat_photos or not chat_photos[chat_id]:






                await asyncio.sleep(5.0)






                continue













            photos_list = chat_photos[chat_id]






            file_id = random.choice(photos_list)













            photo_file = await bot.get_file(file_id)






            buf = io.BytesIO()






            await photo_file.download_to_memory(buf)






            buf.seek(0)













            await bot.set_chat_photo(chat_id=chat_id, photo=buf)






            await asyncio.sleep(0.5)






        except telegram.error.RetryAfter as e:






            await asyncio.sleep(float(e.retry_after) + 1.0)






        except asyncio.CancelledError:






            return






        except Exception:






            await asyncio.sleep(5.0)













# ==================== SPAM COMMANDS ====================



























@only_admin






async def cmd_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Start text spam"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not context.args:






        await update.message.reply_text(f"⚠️ Usage: {CMD_PREFIX}spam <text>\nExample: {CMD_PREFIX}spam Hello World")






        return













    text = " ".join(context.args)






    chat_id = update.message.chat_id













    # Stop existing spam






    if chat_id in spam_tasks:






        for task in spam_tasks[chat_id]:






            task.cancel()













    tasks = []






    for bot in bots:






        task = asyncio.create_task(spam_loop(bot, chat_id, text))






        tasks.append(task)













    spam_tasks[chat_id] = tasks













    await update.message.reply_text(






        f"💥 *SPAM STARTED* 💥\n"






        f"📝 Text: `{text}`\n"






        f"🤖 Bots: `{len(bots)}`\n"






        f"🛑 Use `{CMD_PREFIX}stopspam` to stop"






    )




















@only_admin






async def cmd_raidspam(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Start RAID spam with multipliers"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not context.args:






        await update.message.reply_text(f"⚠️ Usage: {CMD_PREFIX}raidspam <name>\nExample: {CMD_PREFIX}raidspam test")






        return













    name = " ".join(context.args)






    chat_id = update.message.chat_id













    # Stop existing spam






    if chat_id in spam_tasks:






        for task in spam_tasks[chat_id]:






            task.cancel()













    tasks = []






    for bot in bots:






        task = asyncio.create_task(raidspam_loop(bot, chat_id, name))






        tasks.append(task)













    spam_tasks[chat_id] = tasks













    await update.message.reply_text(






        f"🔥 *RAID SPAM STARTED* 🔥\n"






        f"📝 Target: `{name}`\n"






        f"📊 Multipliers: x10, x20, x25\n"






        f"🤖 Bots: `{len(bots)}`\n"






        f"🛑 Use `{CMD_PREFIX}stopspam` to stop"






    )




















@only_admin






async def cmd_swipe(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Start swipe attack"""






    if context.bot.id != MAIN_BOT_ID:






        return













    target = " ".join(context.args) if context.args else ""






    chat_id = update.message.chat_id













    if chat_id not in swipe_tasks:






        swipe_tasks[chat_id] = {}













    if target in swipe_tasks[chat_id]:






        return await update.message.reply_text(f"⚠️ Swipe for {target} is already running!")













    tasks = []






    for bot in bots:






        task = asyncio.create_task(swipe_loop(bot, chat_id, target))






        tasks.append(task)













    swipe_tasks[chat_id][target] = tasks













    await update.message.reply_text(






        f"🔥 *SWIPE STARTED ON {target}* 🔥\n"






        f"🤖 Bots: `{len(bots)}`\n"






        f"🛑 Use `{CMD_PREFIX}stopswipe {target}` to stop"






    )




















@only_admin






async def cmd_stopswipe(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Stop swipe attack"""






    if context.bot.id != MAIN_BOT_ID:






        return













    chat_id = update.message.chat_id













    if not context.args:






        # Stop all swipes in this chat






        if chat_id in swipe_tasks:






            for target in list(swipe_tasks[chat_id].keys()):






                for task in swipe_tasks[chat_id][target]:






                    task.cancel()






            del swipe_tasks[chat_id]






            return await update.message.reply_text("🛑 **ALL SWIPES STOPPED** 🛑")






        return await update.message.reply_text("⚠️ No active swipes found.")













    target = " ".join(context.args)






    if chat_id in swipe_tasks and target in swipe_tasks[chat_id]:






        for task in swipe_tasks[chat_id][target]:






            task.cancel()






        del swipe_tasks[chat_id][target]






        await update.message.reply_text(f"🛑 **SWIPE STOPPED FOR {target}** 🛑")






    else:






        await update.message.reply_text(f"⚠️ No active swipe found for {target}.")




















@only_sudo






async def cmd_nc5(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Start nc5 name changer"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not context.args:






        await update.message.reply_text(f"⚠️ Usage: {CMD_PREFIX}nc5 <text>")






        return













    base_text = " ".join(context.args)






    chat_id = update.message.chat_id













    if chat_id in group_tasks:






        return await update.message.reply_text("⚠️ A loop is already running! Use `~stopnc` first.")













    tasks = []






    for bot in bots:






        task = asyncio.create_task(nc5_loop(bot, chat_id, base_text))






        tasks.append(task)













    group_tasks[chat_id] = tasks













    await update.message.reply_text(






        f"⚔️ *CSWORD LOOP STARTED* ⚔️\n"






        f"📝 Text: `{base_text}`\n"






        f"🤖 Bots: `{len(bots)}`\n"






        f"🛑 Use `{CMD_PREFIX}stopnc` to stop"






    )




















@only_sudo






async def cmd_nc6(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Start nc6 name changer"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not context.args:






        await update.message.reply_text(f"⚠️ Usage: {CMD_PREFIX}nc6 <text>")






        return













    base_text = " ".join(context.args)






    chat_id = update.message.chat_id













    if chat_id in group_tasks:






        return await update.message.reply_text("⚠️ A loop is already running! Use `~stopnc` first.")













    tasks = []






    for bot in bots:






        task = asyncio.create_task(nc6_loop(bot, chat_id, base_text))






        tasks.append(task)













    group_tasks[chat_id] = tasks













    await update.message.reply_text(






        f"👙 *NCBRA LOOP STARTED* 👙\n"






        f"📝 Text: `{base_text}`\n"






        f"🤖 Bots: `{len(bots)}`\n"






        f"🛑 Use `{CMD_PREFIX}stopnc` to stop"






    )




















@only_admin






async def cmd_raidnc(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Start RAID NC name changer"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not context.args:






        await update.message.reply_text(f"⚠️ Usage: {CMD_PREFIX}raidnc <name>")






        return













    prefix = " ".join(context.args)






    chat_id = update.message.chat_id













    if chat_id in group_tasks:






        for task in group_tasks[chat_id]:






            task.cancel()













    tasks = []






    for bot in bots:






        task = asyncio.create_task(raidnc_loop(bot, chat_id, prefix))






        tasks.append(task)













    group_tasks[chat_id] = tasks













    await update.message.reply_text(






        f"🔥 *RAID NC STARTED* 🔥\n"






        f"📝 Name: `{prefix}`\n"






        f"🤖 Bots: `{len(bots)}`\n"






        f"🛑 Use `{CMD_PREFIX}stopnc` to stop"






    )




















@only_admin






async def cmd_stopraidnc(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Stop RAID NC"""






    if context.bot.id != MAIN_BOT_ID:






        return













    chat_id = update.message.chat_id






    if chat_id in group_tasks:






        for task in group_tasks[chat_id]:






            task.cancel()






        del group_tasks[chat_id]






        await update.message.reply_text("🛑 RAID NC STOPPED")






    else:






        await update.message.reply_text("❌ No active RAID NC")




















@only_admin






async def cmd_rishunc(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Start rishunc name changer"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not context.args:






        await update.message.reply_text(f"⚠️ Usage: {CMD_PREFIX}rohitnc <name>")






        return













    base = " ".join(context.args)






    chat_id = update.message.chat_id













    if chat_id in rishunc_tasks:






        for task in rishunc_tasks[chat_id]:






            task.cancel()













    tasks = []






    for bot in bots:






        task = asyncio.create_task(rishunc_loop(bot, chat_id, base))






        tasks.append(task)













    rishunc_tasks[chat_id] = tasks













    await update.message.reply_text(






        f"💀 *𝐑ᴏʜɪᴛ .⋆NC ACTIVATED* 💀\n"






        f"📝 Name: `{base}`\n"






        f"🤖 Bots: `{len(bots)}`\n"






        f"🛑 Use `{CMD_PREFIX}stoprohitnc` to stop"






    )




















@only_admin






async def cmd_rishuncgodspeed(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Start rishunc GOD SPEED"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not context.args:






        await update.message.reply_text(f"⚠️ Usage: {CMD_PREFIX}rohitncgodspeed <name>")






        return













    base = " ".join(context.args)






    chat_id = update.message.chat_id













    if chat_id in rishunc_tasks:






        for task in rishunc_tasks[chat_id]:






            task.cancel()













    tasks = []






    for bot in bots:






        task = asyncio.create_task(






            rishunc_loop(bot, chat_id, base, delay=0.005))






        tasks.append(task)













    rishunc_tasks[chat_id] = tasks













    await update.message.reply_text(






        f"👑🔥 *𝐑ᴏʜɪᴛ .⋆NC GOD SPEED ACTIVATED* 🔥👑\n"






        f"📝 Name: `{base}`\n"






        f"⚡ Speed: ULTRA FAST (0.005s)\n"






        f"🤖 Bots: `{len(bots)}`\n"






        f"🛑 Use `{CMD_PREFIX}stoprohitnc` to stop"






    )




















@only_admin






async def cmd_stoprishunc(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Stop rishunc"""






    if context.bot.id != MAIN_BOT_ID:






        return













    chat_id = update.message.chat_id






    if chat_id in rishunc_tasks:






        for task in rishunc_tasks[chat_id]:






            task.cancel()






        del rishunc_tasks[chat_id]






        await update.message.reply_text("🛑 𝐑ᴏʜɪᴛ .⋆NC STOPPED")






    else:






        await update.message.reply_text("❌ No active rohitnc")




















@only_admin






async def cmd_stopnc(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Stop all name changer loops"""






    if context.bot.id != MAIN_BOT_ID:






        return













    chat_id = update.message.chat_id






    stopped = []













    # Stop group_tasks (nc1-4, nc5, nc6, raidnc)






    if chat_id in group_tasks:






        for task in group_tasks[chat_id]:






            task.cancel()






        del group_tasks[chat_id]






        stopped.append("NC")













    # Stop rishunc_tasks






    if chat_id in rishunc_tasks:






        for task in rishunc_tasks[chat_id]:






            task.cancel()






        del rishunc_tasks[chat_id]






        stopped.append("𝐑ᴏʜɪᴛ .⋆NC")













    if stopped:






        await update.message.reply_text(f"🛑 {', '.join(stopped)} STOPPED")






    else:






        await update.message.reply_text("❌ No active name changers")




















@only_admin






async def cmd_stopspam(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Stop spam"""






    if context.bot.id != MAIN_BOT_ID:






        return













    chat_id = update.message.chat_id






    if chat_id in spam_tasks:






        for task in spam_tasks[chat_id]:






            task.cancel()






        del spam_tasks[chat_id]






        await update.message.reply_text("🛑 SPAM STOPPED")






    else:






        await update.message.reply_text("❌ No active spam")













# ==================== SLIDE COMMANDS ====================




















@only_admin






async def cmd_targetslide(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Add user to slide targets"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not update.message.reply_to_message:






        return await update.message.reply_text("⚠️ Reply to a user's message")













    target_id = update.message.reply_to_message.from_user.id






    slide_targets.add(target_id)






    await update.message.reply_text(f"🎯 Target slide added: `{target_id}`")




















@only_admin






async def cmd_stopslide(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Remove user from slide targets"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not update.message.reply_to_message:






        return await update.message.reply_text("⚠️ Reply to a user's message")













    target_id = update.message.reply_to_message.from_user.id






    slide_targets.discard(target_id)






    await update.message.reply_text(f"🛑 Slide stopped: `{target_id}`")




















@only_admin






async def cmd_slidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Add user to slidespam targets"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not update.message.reply_to_message:






        return await update.message.reply_text("⚠️ Reply to a user's message")













    target_id = update.message.reply_to_message.from_user.id






    slidespam_targets.add(target_id)






    await update.message.reply_text(f"💥 Slide spam started: `{target_id}`")




















@only_admin






async def cmd_stopslidespam(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Remove user from slidespam targets"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not update.message.reply_to_message:






        return await update.message.reply_text("⚠️ Reply to a user's message")













    target_id = update.message.reply_to_message.from_user.id






    slidespam_targets.discard(target_id)






    await update.message.reply_text(f"🛑 Slide spam stopped: `{target_id}`")













# ==================== PHOTO COMMANDS ====================




















@only_admin






async def cmd_savephoto(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Save photo for loop"""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not update.message.reply_to_message or not update.message.reply_to_message.photo:






        return await update.message.reply_text("⚠️ Reply to a photo to save it!")













    chat_id = update.message.chat_id






    file_id = update.message.reply_to_message.photo[-1].file_id













    if chat_id not in chat_photos:






        chat_photos[chat_id] = []













    chat_photos[chat_id].append(file_id)






    await update.message.reply_text(f"✅ Photo saved! Total: {len(chat_photos[chat_id])}")




















@only_admin






async def cmd_startphoto(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Start photo loop"""






    if context.bot.id != MAIN_BOT_ID:






        return













    chat_id = update.message.chat_id






    if chat_id not in chat_photos or len(chat_photos[chat_id]) < 2:






        return await update.message.reply_text("⚠️ Save at least 2 photos first!")













    if chat_id in photo_tasks:






        photo_tasks[chat_id].cancel()













    tasks = []






    for bot in bots:






        task = asyncio.create_task(photo_loop(






            bot, chat_id, chat_photos[chat_id]))






        tasks.append(task)













    photo_tasks[chat_id] = tasks






    await update.message.reply_text("🔄 Photo loop started (0.5s speed)!")




















@only_admin






async def cmd_stopphoto(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Stop photo loop"""






    if context.bot.id != MAIN_BOT_ID:






        return













    chat_id = update.message.chat_id






    if chat_id in photo_tasks:






        for task in photo_tasks[chat_id]:






            task.cancel()






        del photo_tasks[chat_id]






        await update.message.reply_text("⏹ Photo loop stopped!")






    else:






        await update.message.reply_text("❌ No active photo loop")




















@only_admin






async def cmd_clearphotos(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Clear saved photos"""






    if context.bot.id != MAIN_BOT_ID:






        return













    chat_id = update.message.chat_id






    if chat_id in chat_photos:






        del chat_photos[chat_id]






        await update.message.reply_text("🗑 Saved photos cleared!")













# ==================== AUTO REPLY HANDLER ====================




















async def auto_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Handle auto-reactions and slide targets"""






    if not update.message or not update.message.from_user:






        return













    uid = update.message.from_user.id






    chat_id = update.message.chat_id













    # Handle slide targets






    if uid in slide_targets:






        for text in RAID_TEXTS[:3]:






            try:






                await update.message.reply_text(text)






                await asyncio.sleep(0.1)






            except Exception:






                pass













    # Handle slidespam targets






    if uid in slidespam_targets:






        for text in RAID_TEXTS:






            try:






                await update.message.reply_text(text)






                await asyncio.sleep(0.05)






            except Exception:






                pass













# ==================== MENU COMMANDS ====================




















@only_admin






async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Show main menu"""






    if context.bot.id != MAIN_BOT_ID:






        return













    menu = menu_config.get_menu("main")






    keyboard = get_main_keyboard()













    try:






        if menu.get("type") == "photo":






            await update.message.reply_photo(






                photo=menu["video"],






                caption=menu["caption"],






                parse_mode="Markdown",






                reply_markup=keyboard






            )






        else:






            await update.message.reply_video(






                video=menu["video"],






                caption=menu["caption"],






                parse_mode="Markdown",






                reply_markup=keyboard






            )






    except Exception as e:






        await update.message.reply_text(






            f"❌ Media error: {e}\n\n{menu['caption']}",






            parse_mode="Markdown",






            reply_markup=keyboard






        )




















async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Handle button callbacks"""






    query = update.callback_query






    await query.answer()













    if context.bot.id != MAIN_BOT_ID:






        await query.answer("❌ Only main bot handles this!", show_alert=True)






        return













    if not is_admin(query.from_user.id):






        await query.answer("❌ You are not admin!", show_alert=True)






        return













    data = query.data













    if data == "menu_main":






        menu = menu_config.get_menu("main")






        try:






            media_class = InputMediaPhoto if menu.get(






                "type") == "photo" else InputMediaVideo






            await query.message.edit_media(






                media_class(






                    media=menu["video"],






                    caption=menu["caption"],






                    parse_mode="Markdown"






                ),






                reply_markup=get_main_keyboard()






            )






        except Exception:






            await query.message.edit_text(






                menu["caption"],






                reply_markup=get_main_keyboard(),






                parse_mode="Markdown"






            )






        return













    if data.startswith("menu_"):






        category = data.replace("menu_", "")






        menu = menu_config.get_menu(category)













        keyboard = get_back_keyboard()













        try:






            media_class = InputMediaPhoto if menu.get(






                "type") == "photo" else InputMediaVideo






            await query.message.edit_media(






                media_class(






                    media=menu["video"],






                    caption=menu["caption"],






                    parse_mode="Markdown"






                ),






                reply_markup=keyboard






            )






        except Exception:






            await query.message.edit_text(






                menu["caption"],






                reply_markup=keyboard,






                parse_mode="Markdown"






            )






        return













    if data == "help_full":






        help_text = get_help_text()






        await query.message.edit_text(






            help_text,






            parse_mode="Markdown",






            reply_markup=get_back_keyboard()






        )






        return













    if data == "status":






        status_text = await get_status_text()






        await query.message.reply_text(status_text, parse_mode="Markdown")






        return













# ==================== HELP TEXT ====================




















def get_help_text():






    p = CMD_PREFIX






    help_text = f"""






🌸 ⊹ **T O S H I R O  N E T W O R K** ⊹ 🌸



🍨 ‧˚ **A T T A C K  M O D E S**

ʚ `{p}nc1 [name]`  ⊹  Raid Assault

ʚ `{p}nc2 [name]`  ⊹  God Mode

ʚ `{p}nc3 [name]`  ⊹  Time Shift

ʚ `{p}nc4 [name]`  ⊹  Custom Mix

ʚ `{p}nc5 [text]`  ⊹  CSWORD Loop

ʚ `{p}nc6 [text]`  ⊹  NCBRA Loop

ʚ `{p}spamemo [tgt]`  ⊹  Emoji Spam

ʚ `{p}spam [text]`  ⊹  Text Spam

ʚ `{p}raidspam [name]`  ⊹  Raid Spam

ʚ `{p}swipe [tgt]`  ⊹  Swipe Attack

ʚ `{p}raidnc [name]`  ⊹  Raid NC

ʚ `{p}rohitnc [name]`  ⊹  ROHIT  Loop

ʚ `{p}rohitncgodspeed [name]`  ⊹  God Speed

ʚ `{p}over [tgt]`  ⊹  Game Over



🎐 ‧˚ **A U D I O  P L A Y E R**

ʚ `{p}song [name]`  ⊹  Search & Play



🕯️ ‧˚ **S T O P  S Y S T E M S**

ʚ `{p}stop`  ⊹  Stop Current

ʚ `{p}stopall`  ⊹  Global Emergency Stop

ʚ `{p}stopnc`  ⊹  Halt Name Changer

ʚ `{p}stopspam`  ⊹  Halt Spam

ʚ `{p}stopswipe [tgt]`  ⊹  Halt Swipe

ʚ `{p}stoprohitnc`  ⊹  Halt ROHIT  Loop

ʚ `{p}stopphoto`  ⊹  Halt Photo Loop



🫧 ‧˚ **M E D I A  V A U L T**

ʚ `{p}savephoto`  ⊹  Save Media

ʚ `{p}startphoto`  ⊹  Begin Photo Loop

ʚ `{p}stopphoto`  ⊹  Stop Photo Loop

ʚ `{p}clearphotos`  ⊹  Purge Gallery



🍰 ‧˚ **C O N T R O L  &  C O N F I G**

ʚ `{p}status`  ⊹  System Health

ʚ `{p}leave`  ⊹  Bots Disconnect

ʚ `{p}bye`  ⊹  Instant Leave

ʚ `{p}speed [0-5]`  ⊹  Set Delay

ʚ `{p}setprefix`  ⊹  Change Prefix

ʚ `{p}ncthreads`  ⊹  NC Threads

ʚ `{p}spamthreads`  ⊹  Spam Threads



✧ *Powered by Rebel  Supremacy* ✧






"""






    return help_text













# Helper and decorator definitions moved to the top of the file













# ==================== NC STREAM FUNCTIONS ====================




















async def ultra_nc1_stream(bot, chat_id, target_name, stop_event, bot_id):






    while not stop_event.is_set():






        try:






            emo = random.choice(NC_EMOJIS)






            heart = random.choice(NC_HEARTS)






            title = NC_TEMPLATES["nc1"].format(base=target_name, emo=emo, heart=heart)






            await safe_set_chat_title(bot, chat_id, title)






        except Exception:






            pass






        await asyncio.sleep(CURRENT_DELAY if CURRENT_DELAY > 0 else 0.001)




















async def ultra_nc2_stream(bot, chat_id, target_name, stop_event, bot_id):






    while not stop_event.is_set():






        try:






            emo = random.choice(NC_EMOJIS)






            title = NC_TEMPLATES["nc2"].format(base=target_name, emo=emo)






            await safe_set_chat_title(bot, chat_id, title)






        except Exception:






            pass






        await asyncio.sleep(CURRENT_DELAY if CURRENT_DELAY > 0 else 0.001)




















async def ultra_nc3_stream(bot, chat_id, target_name, stop_event, bot_id):






    while not stop_event.is_set():






        try:






            emo = random.choice(NC_EMOJIS)






            current_time = datetime.now().strftime("%I:%M %p")






            title = NC_TEMPLATES["nc3"].format(base=target_name, emo=emo, time=current_time)






            await safe_set_chat_title(bot, chat_id, title)






        except Exception:






            pass






        await asyncio.sleep(CURRENT_DELAY if CURRENT_DELAY > 0 else 0.001)




















async def ultra_nc4_stream(bot, chat_id, target_name, stop_event, bot_id):






    while not stop_event.is_set():






        try:






            pattern = random.choice(NC_PATTERNS)






            title = NC_TEMPLATES["nc4"].format(base=target_name, pattern=pattern)






            await safe_set_chat_title(bot, chat_id, title)






        except Exception:






            pass






        await asyncio.sleep(CURRENT_DELAY if CURRENT_DELAY > 0 else 0.001)




















# ==================== EXISTING NC COMMANDS ====================




















@only_sudo






async def cmd_nc1(update: Update, context: ContextTypes.DEFAULT_TYPE):






    await cmd_nc(update, context, "nc1", ultra_nc1_stream, "Raid")




















@only_sudo






async def cmd_nc2(update: Update, context: ContextTypes.DEFAULT_TYPE):






    await cmd_nc(update, context, "nc2", ultra_nc2_stream, "God")




















@only_sudo






async def cmd_nc3(update: Update, context: ContextTypes.DEFAULT_TYPE):






    await cmd_nc(update, context, "nc3", ultra_nc3_stream, "Time")




















@only_sudo






async def cmd_nc4(update: Update, context: ContextTypes.DEFAULT_TYPE):






    await cmd_nc(update, context, "nc4", ultra_nc4_stream, "Custom")




















async def cmd_nc(update: Update, context: ContextTypes.DEFAULT_TYPE, nc_type: str, stream_func, name: str):






    if context.bot.id != MAIN_BOT_ID:






        return






    if not context.args:






        return await update.message.reply_text(f"⚠️ Usage: {CMD_PREFIX}{nc_type} <name>")













    base = " ".join(context.args)






    chat_id = update.message.chat_id













    controller.stop_attack(chat_id, nc_type)






    key = f"{chat_id}_{nc_type}"






    if key in active_attacks:






        for task in active_attacks[key]:






            task.cancel()






        del active_attacks[key]













    stop_event = controller.get_stop_event(chat_id, nc_type)






    stop_event.clear()













    tasks = []






    for bot in bots:






        task = asyncio.create_task(stream_func(bot, chat_id, base, stop_event, bot.id))






        tasks.append(task)













    active_attacks[key] = tasks













    await update.message.reply_text(






        f"☣️ *{nc_type.upper()} ACTIVATED* ☣️\n"






        f"📝 Name: `{base}`\n"






        f"🤖 Bots: `{len(bots)}`\n"






        f"⚡ Mode: `MAX SPEED`\n"






        f"🛑 Use `{CMD_PREFIX}stop` to stop"






    )













# ==================== SPAMEMO COMMANDS ====================













SPAMEMO_EMOJIS = ["🩷", "♥️", "❤️‍🩹", "💝", "🤍", "🩶", "🖤", "🤎", "💜", "💙",






                  "🩵", "💚", "💛", "🧡", "❤️", "💗", "💔", "❣️", "💕", "💞", "💓", "💖", "💘", "💌"]






DEFAULT_SPAMEMO_THREADS = 20




















def get_spamemo_message(target):






    upper_target = target.upper()






    target_tag = f"「 {upper_target} 」"






    emoji = SPAMEMO_EMOJIS[random.randint(0, len(SPAMEMO_EMOJIS) - 1)]






    line = f"{target_tag} 𝑻𝑹𝒀 𝑴𝑨𝑲𝑨 𝑲𝑨𝑳𝑨 𝑲𝑨𝑺𝑯𝑴𝑰𝑹𝑰 🅱︎🅾︎🆂︎🅳︎🅰︎ 🅿︎🅷︎🅰︎🆃︎ 𝑮𝒀𝑨 🧸🎐({emoji})𒀸"






    return "\n\n".join([line] * 10)




















async def spamemo_stream(bot, chat_id, target_text, stream_id, stop_event, bot_id):






    global TOTAL_MESSAGES_SENT






    while not stop_event.is_set():






        try:






            message = get_spamemo_message(target_text)






            await bot.send_message(chat_id, message)






            TOTAL_MESSAGES_SENT += 1






            await asyncio.sleep(0)






        except asyncio.CancelledError:






            break






        except Exception:






            await asyncio.sleep(0)




















async def spamemo_multi(bot, chat_id, target_text, num_streams, stop_event, bot_id):






    streams = []






    for i in range(num_streams):






        stream = asyncio.create_task(spamemo_stream(






            bot, chat_id, target_text, i, stop_event, bot_id))






        streams.append(stream)






    try:






        await stop_event.wait()






    finally:






        for s in streams:






            s.cancel()




















@only_admin






async def cmd_spamemo(update: Update, context: ContextTypes.DEFAULT_TYPE):






    if context.bot.id != MAIN_BOT_ID:






        return













    if not context.args:






        await update.message.reply_text(f"⚠️ Usage: {CMD_PREFIX}spamemo <text>\nExample: {CMD_PREFIX}spamemo 𝐑ᴏʜɪᴛ .⋆")






        return













    target = ' '.join(context.args)






    chat_id = update.message.chat_id






    attack_type = "spamemo"













    controller.stop_spamemo(chat_id)






    stop_event = controller.get_stop_event(chat_id, attack_type)






    stop_event.clear()













    tasks = []






    for bot in bots:






        task = asyncio.create_task(spamemo_multi(






            bot, chat_id, target, controller.spamemo_threads, stop_event, bot.id))






        tasks.append(task)













    active_attacks[f"{chat_id}_{attack_type}"] = tasks













    total_streams = len(bots) * controller.spamemo_threads













    await update.message.reply_text(






        f"🔱 *SPAMEMO ACTIVATED* 🔱\n"






        f"📝 Target: `{target}`\n"






        f"🤖 Bots: `{len(bots)}`\n"






        f"🧵 Threads/bot: `{controller.spamemo_threads}`\n"






        f"⚡ Total streams: `{total_streams}`\n"






        f"🛑 Use `{CMD_PREFIX}stopspam` to stop"






    )




















@only_admin






async def cmd_spamthreads(update: Update, context: ContextTypes.DEFAULT_TYPE):






    if context.bot.id != MAIN_BOT_ID:






        return













    if not context.args:






        await update.message.reply_text(






            f"📊 *Current spam threads:* `{controller.spamemo_threads}`\n"






            f"📝 Usage: `{CMD_PREFIX}spamthreads <20-50>`"






        )






        return













    try:






        threads = int(context.args[0])






        old = controller.spamemo_threads






        new = controller.set_spamemo_threads(threads)






        await update.message.reply_text(f"✅ Spam threads changed from `{old}` to `{new}`")






    except ValueError:






        await update.message.reply_text("❌ Invalid number! Use 20-50")




















@only_admin






async def cmd_threadstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):






    if context.bot.id != MAIN_BOT_ID:






        return













    total_streams = len(bots) * controller.spamemo_threads













    await update.message.reply_text(






        f"⚡ *THREAD STATUS* ⚡\n\n"






        f"📨 Spamemo Threads: `{controller.spamemo_threads}`\n"






        f"🤖 Total Bots: `{len(bots)}`\n"






        f"⚡ Total Streams: `{total_streams}`\n"






        f"🚀 Speed: `INSTANT`\n"






        f"💥 Use `{CMD_PREFIX}spamthreads` to change"






    )













# ==================== EXISTING COMMANDS ====================













# [Keep existing commands: cmd_over, cmd_upall, cmd_stop, cmd_stopall, cmd_speed, cmd_entrust, cmd_revoke, cmd_setprefix, cmd_status, cmd_help, cmd_start, cmd_leave, cmd_bye, cmd_list, cmd_setvideo, cmd_sethelpvideo, cmd_ncthreads]













# ==================== ATTACK CONTROLLER ====================




















class AttackController:






    def __init__(self):






        self.stop_events = {}






        self.active_tasks = {}






        self.nc_threads = 20






        self.spamemo_threads = DEFAULT_SPAMEMO_THREADS






        self.slide_threads = 10













    def set_spamemo_threads(self, threads):






        self.spamemo_threads = max(20, min(50, threads))






        return self.spamemo_threads













    def set_slide_threads(self, threads):






        self.slide_threads = max(5, min(30, threads))






        return self.slide_threads













    def stop_spamemo(self, chat_id):






        return self.stop_attack(chat_id, "spamemo")













    def stop_slide(self, chat_id):






        return self.stop_attack(chat_id, "slide")













    def get_stop_event(self, chat_id, attack_type):






        key = f"{chat_id}_{attack_type}"






        if key not in self.stop_events:






            self.stop_events[key] = asyncio.Event()






        return self.stop_events[key]













    def stop_attack(self, chat_id, attack_type):






        key = f"{chat_id}_{attack_type}"






        if key in self.stop_events:






            self.stop_events[key].set()






            self.stop_events[key] = asyncio.Event()






            return True






        return False













    def stop_all(self, chat_id=None):






        for key in list(self.stop_events.keys()):






            if chat_id is None or key.startswith(str(chat_id)):






                self.stop_events[key].set()






                self.stop_events[key] = asyncio.Event()






        return True




















controller = AttackController()






bots = []






apps = []






active_attacks = {}













# Flag to check if this is the main bot






MAIN_BOT_ID = None




















def get_cmd_name(text):






    if text.startswith(CMD_PREFIX):






        return text[len(CMD_PREFIX):].split()[0].lower()






    return None













# ==================== STATUS TEXT ====================




















async def get_status_text():






    uptime_seconds = int(time.time() - START_TIME)






    uptime_str = str(timedelta(seconds=uptime_seconds))













    async def ping_bot(bot):






        start = time.time()






        try:






            bot_info = await asyncio.wait_for(bot.get_me(), timeout=1.5)






            return bot_info.username, round((time.time() - start) * 1000)






        except Exception:






            try:






                username = getattr(bot, 'username', None) or str(






                    getattr(bot, 'id', 'Unknown'))






            except Exception:






                username = "Unknown"






            return username, -1













    pings = await asyncio.gather(*[ping_bot(bot) for bot in bots])













    bot_details = []






    online_count = 0






    for username, ping in pings:






        escaped_username = escape_md(username)






        if ping >= 0:






            bot_details.append(f"• @{escaped_username}: `{ping}ms` 🟢")






            online_count += 1






        else:






            bot_details.append(f"• @{escaped_username}: `Offline` 🔴")













    active_count = sum(1 for key in active_attacks if active_attacks[key])






    current_delay = get_delay()













    cpu_usage = "N/A"






    ram_usage = "N/A"






    if psutil:






        try:






            cpu_usage = f"{psutil.cpu_percent()}%"






            ram_usage = f"{psutil.virtual_memory().percent}%"






        except:






            pass













    system_info = f"💻 *OS:* `{platform.system()}` | *Py:* `{platform.python_version()}`"













    status_text = (






        f"🎀 *STATUS* 🎀\n\n"






        f"⏱️ `{uptime_str}` | 🤖 Bots: `{online_count}/{len(bots)}`\n"






        f"⚡ *Attacks:* `{active_count}`\n"






        f"📊 *CPU:* `{cpu_usage}` | *RAM:* `{ram_usage}`\n"






    )






    return status_text













# ==================== COMMAND HANDLER ====================




















# ==================== DUMMY COMMANDS ====================






async def dummy_reply(update, context):






    if update.message:






        await update.message.reply_text('⚠️ This command is currently under development or disabled.')




















@only_sudo






async def cmd_over(update, context):






    if context.bot.id != MAIN_BOT_ID:






        return













    target = " ".join(context.args) if context.args else "UNKNOWN"













    # Current IST date & time






    ist = timezone(timedelta(hours=5, minutes=30))






    now = datetime.now(ist)






    date_str = now.strftime("%d %B %Y")






    time_str = now.strftime("%I:%M:%S %p")













    caption = (






        f"💀『 *Ｇ Ａ Ｍ Ｅ  Ｏ Ｖ Ｅ Ｒ* 』💀\n"






        f"\n"






        f"⛩️ ᴛᴀʀɢᴇᴛ ᴇʟɪᴍɪɴᴀᴛᴇᴅ\n"






        f"\n"






        f"🎯 *ᴛᴀʀɢᴇᴛ:* `{target}`\n"






        f"☠️ *sᴛᴀᴛᴜs:* `ᴅᴇsᴛʀᴏʏᴇᴅ`\n"






        f"\n"






        f"📅 *ᴅᴀᴛᴇ:* `{date_str}`\n"






        f"🕐 *ᴛɪᴍᴇ:* `{time_str} IST`\n"






        f"\n"






        f"彡━━━━━━━━━━━━━━━━━━━━━彡\n"






        f"✨ *𝐑ᴏʜɪᴛ .⋆ sᴜᴘʀᴇᴍᴀᴄʏ — ɴᴏ ᴍᴇʀᴄʏ* ✨"






    )













    media_id = bot_config.get("media_over", DEFAULT_GAMEOVER_VIDEO_URL)






    media_type = bot_config.get("media_over_type", "video")













    if media_type == "photo":






        await update.message.reply_photo(photo=media_id, caption=caption, parse_mode="Markdown")






    else:






        await update.message.reply_video(video=media_id, caption=caption, parse_mode="Markdown")




















async def cmd_ncthreads(update, context):






    await dummy_reply(update, context)




















async def _get_soundcloud_client_id() -> str | None:






    """Dynamically fetch SoundCloud client_id from their JS bundles."""






    try:






        async with aiohttp.ClientSession() as session:






            async with session.get("https://soundcloud.com", headers={"User-Agent": "Mozilla/5.0"}) as resp:






                html = await resp.text()













            # Find JS bundle URLs






            script_urls = re.findall(






                r'<script[^>]+src="(https://a-v2\.sndcdn\.com/assets/[^"]+\.js)"', html






            )






            if not script_urls:






                script_urls = re.findall(r'src="(/assets/[^"]+\.js)"', html)






                script_urls = [f"https://soundcloud.com{u}" for u in script_urls]













            for url in reversed(script_urls[-5:]):






                try:






                    async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:






                        js = await resp.text()






                    match = re.search(r'client_id[=:"]+([a-zA-Z0-9]{32})', js)






                    if match:






                        return match.group(1)






                except Exception:






                    continue






    except Exception:






        pass






    return None




















@only_admin






async def cmd_song(update, context):






    """Search SoundCloud and send audio file."""






    if context.bot.id != MAIN_BOT_ID:






        return













    if not context.args:






        await update.message.reply_text(






            f"🎵 *Usage:* `{CMD_PREFIX}song <song name>`\n"






            f"_Example:_ `{CMD_PREFIX}song Believer Imagine Dragons`",






            parse_mode="Markdown"






        )






        return













    query = " ".join(context.args)






    status_msg = await update.message.reply_text(






        f"🔍 *Searching SoundCloud for:* `{query}`...",






        parse_mode="Markdown"






    )













    try:






        client_id = await _get_soundcloud_client_id()






        if not client_id:






            await status_msg.edit_text("❌ Could not fetch SoundCloud API credentials. Try again later.")






            return













        async with aiohttp.ClientSession() as session:






            # ── Step 1: Search for track ──────────────────────────






            search_url = (






                f"https://api-v2.soundcloud.com/search/tracks"






                f"?q={urllib.parse.quote(query)}&client_id={client_id}&limit=1&linked_partitioning=1"






            )






            async with session.get(search_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:






                if resp.status != 200:






                    await status_msg.edit_text("❌ SoundCloud search failed. Try again later.")






                    return






                data = await resp.json()













            collection = data.get("collection", [])






            if not collection:






                await status_msg.edit_text(f"❌ No tracks found for: `{query}`", parse_mode="Markdown")






                return













            track = collection[0]






            title    = track.get("title", "Unknown Title")






            artist   = track.get("user", {}).get("username", "Unknown Artist")






            dur_ms   = track.get("duration", 0)






            dur_str  = f"{dur_ms // 60000}:{(dur_ms % 60000) // 1000:02d}"






            genre    = track.get("genre", "") or "—"






            plays    = track.get("playback_count", 0)






            likes    = track.get("likes_count", 0)






            thumb_url = track.get("artwork_url", "")






            if thumb_url:






                thumb_url = thumb_url.replace("large", "t500x500")













            # ── Step 2: Find a progressive (MP3) stream ───────────






            transcodings = track.get("media", {}).get("transcodings", [])






            prog_url = None






            for t in transcodings:






                fmt = t.get("format", {})






                if fmt.get("protocol") == "progressive":






                    prog_url = t.get("url")






                    break






            # Fallback to hls if no progressive






            if not prog_url and transcodings:






                prog_url = transcodings[0].get("url")













            if not prog_url:






                await status_msg.edit_text("❌ No downloadable stream found for this track.")






                return













            # ── Step 3: Resolve the actual CDN URL ────────────────






            async with session.get(






                f"{prog_url}?client_id={client_id}",






                headers={"User-Agent": "Mozilla/5.0"}






            ) as resp:






                stream_data = await resp.json()













            actual_url = stream_data.get("url")






            if not actual_url:






                await status_msg.edit_text("❌ Could not resolve the audio stream URL.")






                return













            await status_msg.edit_text(






                f"⬇️ *Downloading:* `{title}`...",






                parse_mode="Markdown"






            )













            # ── Step 4: Download audio bytes ──────────────────────






            async with session.get(actual_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:






                if resp.status != 200:






                    await status_msg.edit_text("❌ Audio download failed.")






                    return






                audio_bytes = await resp.read()













        # ── Step 5: Write to temp file & send ─────────────────────






        tmp_path = os.path.join(tempfile.gettempdir(), f"sc_{update.message.message_id}.mp3")






        with open(tmp_path, "wb") as f:






            f.write(audio_bytes)













        caption = (






            f"🎵『 *{title}* 』\n"






            f"👤 *ᴀʀᴛɪsᴛ:* `{artist}`\n"






            f"⏱️ *ᴅᴜʀᴀᴛɪᴏɴ:* `{dur_str}`\n"






            f"🎼 *ɢᴇɴʀᴇ:* `{genre}`\n"






            f"▶️ *ᴘʟᴀʏs:* `{plays:,}` | ❤️ `{likes:,}`\n\n"






            f"彡━━━━━━━━━━━━━━━━━━━━━彡\n"






            f"✨ *ᴠɪᴀ SoundCloud × 𝐑ᴏʜɪᴛ .⋆*"






        )













        # Convert song title to small-caps for the audio player header






        _sc_map = str.maketrans(






            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",






            "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"






        )






        sc_title = title.translate(_sc_map)













        with open(tmp_path, "rb") as audio_file:






            await update.message.reply_audio(






                audio=audio_file,






                title=sc_title,






                performer="ᴏᴡɴᴇᴅ ʙʏ 𝐑ᴏʜɪᴛ .⋆",






                duration=dur_ms // 1000,






                caption=caption,






                parse_mode="Markdown",






            )













        await status_msg.delete()






        os.unlink(tmp_path)













    except Exception as e:






        logger.exception("cmd_song error")






        try:






            await status_msg.edit_text(f"❌ *Error:* `{e}`", parse_mode="Markdown")






        except Exception:






            pass



























@only_sudo






async def cmd_upall(update, context):






    """Promote all bots to admin in the group."""






    if context.bot.id != MAIN_BOT_ID:






        return






    chat_id = update.message.chat_id






    promoted = []






    failed = []






    for bot in bots:






        try:






            await context.bot.promote_chat_member(






                chat_id=chat_id,






                user_id=bot.id,






                can_change_info=True,






                can_delete_messages=True,






                can_invite_users=True,






                can_restrict_members=True,






                can_pin_messages=True,






                can_manage_chat=True,






            )






            info = await bot.get_me()






            promoted.append(f"@{info.username}")






        except Exception as e:






            failed.append(str(e))






    msg = (






        f"👑 *UPALL COMPLETE* 👑\n"






        f"✅ Promoted: `{len(promoted)}`\n"






        f"❌ Failed: `{len(failed)}`"






    )






    await update.message.reply_text(msg, parse_mode="Markdown")



























@only_sudo






async def cmd_leave(update, context):






    """All bots leave the current chat."""






    if context.bot.id != MAIN_BOT_ID:






        return






    chat_id = update.message.chat_id






    await update.message.reply_text("🏃 All bots leaving...")






    for bot in bots:






        try:






            await bot.leave_chat(chat_id)






        except Exception:






            pass



























@only_sudo






async def cmd_bye(update, context):






    if context.bot.id != MAIN_BOT_ID:






        return






    chat_id = update.message.chat_id






    await update.message.reply_text("👋 Bots leaving chat...")






    for bot in bots:






        try:






            await bot.leave_chat(chat_id)






        except Exception:






            pass




















@only_admin






async def cmd_stop(update, context):






    if context.bot.id != MAIN_BOT_ID:






        return






    chat_id = update.message.chat_id













    # Stop controller-tracked events for this chat






    controller.stop_all(chat_id)













    # Cancel active_attacks tasks for this chat






    keys_to_cancel = [k for k in list(active_attacks.keys()) if k.startswith(f"{chat_id}_")]






    for k in keys_to_cancel:






        for task in active_attacks[k]:






            task.cancel()






        del active_attacks[k]













    # Cancel group_tasks (nc loops) for this chat






    if chat_id in group_tasks:






        for task in group_tasks[chat_id]:






            task.cancel()






        del group_tasks[chat_id]













    # Cancel spam_tasks for this chat






    if chat_id in spam_tasks:






        for task in spam_tasks[chat_id]:






            task.cancel()






        del spam_tasks[chat_id]













    # Cancel swipe_tasks for this chat






    if chat_id in swipe_tasks:






        for target_tasks in swipe_tasks[chat_id].values():






            for task in target_tasks:






                task.cancel()






        del swipe_tasks[chat_id]













    # Cancel rishunc_tasks for this chat






    if chat_id in rishunc_tasks:






        for task in rishunc_tasks[chat_id]:






            task.cancel()






        del rishunc_tasks[chat_id]













    # Cancel photo_tasks for this chat






    if chat_id in photo_tasks:






        tasks_or_task = photo_tasks[chat_id]






        if isinstance(tasks_or_task, list):






            for task in tasks_or_task:






                task.cancel()






        else:






            tasks_or_task.cancel()






        del photo_tasks[chat_id]













    await update.message.reply_text("🛑 All attacks stopped in this chat.")




















@only_admin






async def cmd_stopall(update, context):






    if context.bot.id != MAIN_BOT_ID:






        return













    # Stop all controller-tracked events globally






    controller.stop_all()













    # Cancel all active_attacks tasks






    for key in list(active_attacks.keys()):






        for task in active_attacks[key]:






            task.cancel()






    active_attacks.clear()













    # Cancel all group_tasks (nc loops)






    for tasks in group_tasks.values():






        for task in tasks:






            task.cancel()






    group_tasks.clear()













    # Cancel all spam_tasks






    for tasks in spam_tasks.values():






        for task in tasks:






            task.cancel()






    spam_tasks.clear()













    # Cancel all swipe_tasks






    for chat_swipes in swipe_tasks.values():






        for target_tasks in chat_swipes.values():






            for task in target_tasks:






                task.cancel()






    swipe_tasks.clear()













    # Cancel all rishunc_tasks






    for tasks in rishunc_tasks.values():






        for task in tasks:






            task.cancel()






    rishunc_tasks.clear()













    # Cancel all photo_tasks






    for tasks_or_task in photo_tasks.values():






        if isinstance(tasks_or_task, list):






            for task in tasks_or_task:






                task.cancel()






        else:






            tasks_or_task.cancel()






    photo_tasks.clear()













    await update.message.reply_text("☢️ ALL attacks stopped globally!")




















@only_sudo






async def cmd_speed(update, context):






    """Set global NC/spam delay."""






    if context.bot.id != MAIN_BOT_ID:






        return






    if not context.args:






        await update.message.reply_text(






            f"⚡ *Current delay:* `{get_delay()}s`\n"






            f"📝 Usage: `{CMD_PREFIX}speed <0-5>`\n"






            f"_0 = instant, 5 = 5 second delay_",






            parse_mode="Markdown"






        )






        return






    try:






        val = float(context.args[0])






        if set_delay(val):






            bot_config["delay"] = val






            save_config(bot_config)






            await update.message.reply_text(






                f"✅ *Speed set!* Delay → `{val}s`", parse_mode="Markdown"






            )






        else:






            await update.message.reply_text("❌ Value must be between 0 and 5.")






    except ValueError:






        await update.message.reply_text("❌ Invalid number!")



























@only_sudo






async def cmd_entrust(update, context):






    """Grant admin rights to a user."""






    if context.bot.id != MAIN_BOT_ID:






        return






    if not context.args:






        await update.message.reply_text(f"📝 Usage: `{CMD_PREFIX}entrust <user_id>`", parse_mode="Markdown")






        return






    try:






        uid = int(context.args[0])






        admin_ids.add(uid)






        save_admins(admin_ids)






        await update.message.reply_text(f"✅ User `{uid}` granted admin!", parse_mode="Markdown")






    except ValueError:






        await update.message.reply_text("❌ Invalid user ID!")




















@only_sudo






async def cmd_revoke(update, context):






    """Remove admin rights from a user."""






    if context.bot.id != MAIN_BOT_ID:






        return






    if not context.args:






        await update.message.reply_text(f"📝 Usage: `{CMD_PREFIX}revoke <user_id>`", parse_mode="Markdown")






        return






    try:






        uid = int(context.args[0])






        if uid == OWNER_ID:






            await update.message.reply_text("❌ Cannot revoke the owner!")






            return






        admin_ids.discard(uid)






        save_admins(admin_ids)






        await update.message.reply_text(f"✅ Admin revoked from `{uid}`!", parse_mode="Markdown")






    except ValueError:






        await update.message.reply_text("❌ Invalid user ID!")



























# ==================== ADDBOT COMMAND ====================













@only_sudo






async def cmd_addbot(update: Update, context: ContextTypes.DEFAULT_TYPE):






    """Add a new bot to the list dynamically and start it."""






    if not context.args:






        await update.message.reply_text(f"⚠️ Usage: {CMD_PREFIX}addbot <token>")






        return













    token = context.args[0]






    import re






    if not re.match(r"^\d+:[\w-]+$", token):






        await update.message.reply_text("⚠️ Invalid token format. Expected <digits>:<string>.")






        return













    if token in TOKENS:






        await update.message.reply_text("⚠️ This bot is already running!")






        return













    try:






        app = build_app(token)






        await app.initialize()






        await app.start()






        






        bot_info = await app.bot.get_me()






        bots.append(app.bot)






        apps.append(app)






        TOKENS.append(token)






        






        # Save to config for persistence






        if "tokens" not in bot_config:






            bot_config["tokens"] = []






        if token not in bot_config["tokens"]:






            bot_config["tokens"].append(token)






            save_config(bot_config)






            






        await update.message.reply_text(






            f"✅ Bot @{bot_info.username} added and started successfully!\n"






            f"Total active bots: `{len(bots)}`",






            parse_mode="Markdown"






        )






    except Exception as e:






        logger.exception("Failed to add bot")






        await update.message.reply_text(f"❌ Failed to add bot: `{e}`", parse_mode="Markdown")




















@only_sudo






async def cmd_list(update, context):






    """List all admins."""






    if context.bot.id != MAIN_BOT_ID:






        return






    if not admin_ids:






        await update.message.reply_text("📋 No admins found.")






        return






    lines = [f"• `{uid}`" for uid in sorted(admin_ids)]






    await update.message.reply_text(






        f"👑 *Admin List* 👑\n\n" + "\n".join(lines),






        parse_mode="Markdown"






    )




















@only_sudo






async def cmd_setprefix(update, context):






    """Change the command prefix."""






    global CMD_PREFIX






    if context.bot.id != MAIN_BOT_ID:






        return






    if not context.args:






        await update.message.reply_text(






            f"📝 Current prefix: `{CMD_PREFIX}`\n"






            f"Usage: `{CMD_PREFIX}setprefix <new_prefix>`",






            parse_mode="Markdown"






        )






        return






    new_prefix = context.args[0]






    CMD_PREFIX = new_prefix






    bot_config["prefix"] = new_prefix






    save_config(bot_config)






    await update.message.reply_text(






        f"✅ Prefix changed to: `{new_prefix}`", parse_mode="Markdown"






    )



























@only_sudo






async def cmd_status(update, context):






    if context.bot.id != MAIN_BOT_ID:






        return






    status_text = await get_status_text()






    media_id = bot_config.get(






        "media_status", "https://files.catbox.moe/jpyae4.mp4")






    media_type = bot_config.get("media_status_type", "video")













    if media_type == "photo":






        await update.message.reply_photo(photo=media_id, caption=status_text, parse_mode="Markdown")






    else:






        await update.message.reply_video(video=media_id, caption=status_text, parse_mode="Markdown")




















async def cmd_help(update, context):






    await cmd_menu(update, context)




















async def cmd_helptext(update, context):






    await dummy_reply(update, context)




















async def _set_menu_media(update, context, menu_key):






    if context.bot.id != MAIN_BOT_ID:






        return






    if not update.message.reply_to_message:






        return await update.message.reply_text("⚠️ Please reply to a video or photo!")













    msg = update.message.reply_to_message






    media_id = None






    media_type = None






    if msg.video:






        media_id = msg.video.file_id






        media_type = "video"






    elif msg.photo:






        media_id = msg.photo[-1].file_id






        media_type = "photo"






    elif msg.animation:






        media_id = msg.animation.file_id






        media_type = "video"






    else:






        return await update.message.reply_text("⚠️ No video or photo found in replied message!")













    bot_config[f"media_{menu_key}"] = media_id






    bot_config[f"media_{menu_key}_type"] = media_type






    save_config(bot_config)













    await update.message.reply_text(f"✅ Media updated for {menu_key.upper()} menu!")




















@only_sudo






async def cmd_setvideo1(update, context): await _set_menu_media(






    update, context, "main")




















@only_sudo






async def cmd_setvideo2(update, context): await _set_menu_media(






    update, context, "attack")




















@only_sudo






async def cmd_setvideo3(update, context): await _set_menu_media(






    update, context, "music")




















@only_sudo






async def cmd_setvideo4(update, context): await _set_menu_media(






    update, context, "settings")




















@only_sudo






async def cmd_setvideo5(update, context): await _set_menu_media(






    update, context, "stop")




















@only_sudo






async def cmd_setvideo6(update, context): await _set_menu_media(






    update, context, "admin")




















@only_sudo






async def cmd_setvideo7(update, context): await _set_menu_media(






    update, context, "utility")













@only_sudo






async def cmd_setvideostatus(update, context):






    await _set_menu_media(update, context, "status")













@only_sudo






async def cmd_setvideoover(update, context):






    await _set_menu_media(update, context, "over")




















# ── Named setvideo aliases (used by cmd_map & CommandHandlers) ──────────────













@only_sudo






async def cmd_setvideo_main(update, context):






    await _set_menu_media(update, context, "main")




















@only_sudo






async def cmd_setvideo_attack(update, context):






    await _set_menu_media(update, context, "attack")




















@only_sudo






async def cmd_setvideo_music(update, context):






    await _set_menu_media(update, context, "music")




















@only_sudo






async def cmd_setvideo_settings(update, context):






    await _set_menu_media(update, context, "settings")




















@only_sudo






async def cmd_setvideo_stop(update, context):






    await _set_menu_media(update, context, "stop")




















@only_sudo






async def cmd_setvideo_admin(update, context):






    await _set_menu_media(update, context, "admin")




















@only_sudo






async def cmd_setvideo_utility(update, context):






    await _set_menu_media(update, context, "utility")




















@only_sudo






async def cmd_setvideo_status(update, context):






    await _set_menu_media(update, context, "status")




















@only_sudo






async def cmd_setvideo_over(update, context):






    await _set_menu_media(update, context, "over")




















async def cmd_sethelpvideo(update, context):






    await dummy_reply(update, context)




















async def cmd_start(update, context):






    await dummy_reply(update, context)













# Shortcut commands for menus






async def cmd_m1(update, context):






    # Attack menu






    menu = menu_config.get_menu("attack")






    await _send_menu(update, menu)













async def cmd_m2(update, context):






    # Music menu






    menu = menu_config.get_menu("music")






    await _send_menu(update, menu)













async def cmd_m3(update, context):






    # Settings menu






    menu = menu_config.get_menu("settings")






    await _send_menu(update, menu)













async def cmd_m4(update, context):






    # Stop commands menu






    menu = menu_config.get_menu("stop")






    await _send_menu(update, menu)













async def cmd_m5(update, context):






    # Admin control menu






    menu = menu_config.get_menu("admin")






    await _send_menu(update, menu)













async def cmd_m6(update, context):






    # Utility menu






    menu = menu_config.get_menu("utility")






    await _send_menu(update, menu)













async def cmd_m7(update, context):






    # Main menu






    menu = menu_config.get_menu("main")






    await _send_menu(update, menu)













async def cmd_m8(update, context):






    # Alias to attack menu (same as M1)






    await cmd_m1(update, context)













async def cmd_m9(update, context):






    # Alias to settings menu (same as M3)






    await cmd_m3(update, context)



























# Helper to send a menu (reused by shortcuts)






async def _send_menu(update, menu):






    try:






        if menu.get("type") == "photo":






            await update.message.reply_photo(photo=menu["video"], caption=menu["caption"], parse_mode="Markdown")






        else:






            await update.message.reply_video(video=menu["video"], caption=menu["caption"], parse_mode="Markdown")






    except Exception as e:






        await update.message.reply_text(f"❌ Media error: {e}\n\n{menu.get('caption', '')}", parse_mode="Markdown")




















async def handle_prefix_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):






    if not update.message or not update.message.text:






        return













    if context.bot.id != MAIN_BOT_ID:






        return













    text = update.message.text.strip()






    if not text.startswith(CMD_PREFIX):






        return













    parts = text.split()






    cmd_name = parts[0][len(CMD_PREFIX):].lower()






    context.args = parts[1:] if len(parts) > 1 else []













    cmd_map = {






        # NC Commands






        "nc1": cmd_nc1,






        "nc2": cmd_nc2,






        "nc3": cmd_nc3,






        "nc4": cmd_nc4,






        # Spam Commands






        "spam": cmd_spam,






        "raidspam": cmd_raidspam,






        "swipe": cmd_swipe,






        "stopswipe": cmd_stopswipe,






        "spamemo": cmd_spamemo,






        "spamthreads": cmd_spamthreads,






        "threadstatus": cmd_threadstatus,






        # Name Changer Commands






        "nc5": cmd_nc5,






        "nc6": cmd_nc6,






        "raidnc": cmd_raidnc,






        "stopraidnc": cmd_stopraidnc,






        "rishunc": cmd_rishunc,
        "rohitnc": cmd_rishunc,






        "rishuncgodspeed": cmd_rishuncgodspeed,
        "rohitncgodspeed": cmd_rishuncgodspeed,






        "stoprishunc": cmd_stoprishunc,
        "stoprohitnc": cmd_stoprishunc,






        "stopnc": cmd_stopnc,






        # Slide Commands






        "targetslide": cmd_targetslide,






        "stopslide": cmd_stopslide,






        "slidespam": cmd_slidespam,






        "stopslidespam": cmd_stopslidespam,






        # Photo Commands






        "savephoto": cmd_savephoto,






        "startphoto": cmd_startphoto,






        "stopphoto": cmd_stopphoto,






        "clearphotos": cmd_clearphotos,






        # Existing Commands






        "over": cmd_over,






        "ncthreads": cmd_ncthreads,






        "song": cmd_song,






        "stopspam": cmd_stopspam,






        "upall": cmd_upall,






        "leave": cmd_leave,






        "bye": cmd_bye,






        "stop": cmd_stop,






        "stopall": cmd_stopall,






        "speed": cmd_speed,






        "entrust": cmd_entrust,






        "revoke": cmd_revoke,






        "list": cmd_list,






        "setprefix": cmd_setprefix,






        "status": cmd_status,






        "help": cmd_help,






        "menu": cmd_menu,






        "vmenu": cmd_menu,






        "videomenu": cmd_menu,






        "helptext": cmd_helptext,






        "setvideomain": cmd_setvideo_main,






        "setvideoattack": cmd_setvideo_attack,






        "setvideomusic": cmd_setvideo_music,






        "setvideosettings": cmd_setvideo_settings,






        "setvideosstop": cmd_setvideo_stop,






        "setvideoadmin": cmd_setvideo_admin,






        "setvideoutility": cmd_setvideo_utility,






        "setvideostatus": cmd_setvideo_status,






        "setvideoover": cmd_setvideo_over,






        "sethelpvideo": cmd_sethelpvideo,






        "start": cmd_start,






        "m1": cmd_m1,






        "m2": cmd_m2,






        "m3": cmd_m3,






        "m4": cmd_m4,






        "m5": cmd_m5,






        "m6": cmd_m6,






        "m7": cmd_m7,






        "m8": cmd_m8,






        "m9": cmd_m9,






        "addbot": cmd_addbot,






    }













    if cmd_name in cmd_map:






        await cmd_map[cmd_name](update, context)


































def build_app(token):






    request = HTTPXRequest(






        connection_pool_size=200,






        connect_timeout=5,






        read_timeout=10,






        write_timeout=10,






        pool_timeout=5,






        http_version="1.1",






    )













    app = Application.builder().token(token).request(request).build()













    app.add_handler(CallbackQueryHandler(button_callback))






    app.add_handler(MessageHandler(






        filters.TEXT & ~filters.COMMAND, handle_prefix_commands))






    app.add_handler(MessageHandler(






        filters.ALL & ~filters.COMMAND, auto_replies), group=1)













    # NC Commands






    app.add_handler(CommandHandler("nc1", cmd_nc1))






    app.add_handler(CommandHandler("nc2", cmd_nc2))






    app.add_handler(CommandHandler("nc3", cmd_nc3))






    app.add_handler(CommandHandler("nc4", cmd_nc4))













    # Spam Commands






    app.add_handler(CommandHandler("spam", cmd_spam))






    app.add_handler(CommandHandler("raidspam", cmd_raidspam))






    app.add_handler(CommandHandler("swipe", cmd_swipe))






    app.add_handler(CommandHandler("stopswipe", cmd_stopswipe))






    app.add_handler(CommandHandler("spamemo", cmd_spamemo))






    app.add_handler(CommandHandler("spamthreads", cmd_spamthreads))






    app.add_handler(CommandHandler("threadstatus", cmd_threadstatus))













    # Name Changer Commands






    app.add_handler(CommandHandler("nc5", cmd_nc5))






    app.add_handler(CommandHandler("nc6", cmd_nc6))






    app.add_handler(CommandHandler("raidnc", cmd_raidnc))






    app.add_handler(CommandHandler("stopraidnc", cmd_stopraidnc))






    app.add_handler(CommandHandler("rishunc", cmd_rishunc))
    app.add_handler(CommandHandler("rohitnc", cmd_rishunc))






    app.add_handler(CommandHandler("rishuncgodspeed", cmd_rishuncgodspeed))
    app.add_handler(CommandHandler("rohitncgodspeed", cmd_rishuncgodspeed))






    app.add_handler(CommandHandler("stoprishunc", cmd_stoprishunc))
    app.add_handler(CommandHandler("stoprohitnc", cmd_stoprishunc))






    app.add_handler(CommandHandler("stopnc", cmd_stopnc))













    # Slide Commands






    app.add_handler(CommandHandler("targetslide", cmd_targetslide))






    app.add_handler(CommandHandler("stopslide", cmd_stopslide))






    app.add_handler(CommandHandler("slidespam", cmd_slidespam))






    app.add_handler(CommandHandler("stopslidespam", cmd_stopslidespam))













    # Photo Commands






    app.add_handler(CommandHandler("savephoto", cmd_savephoto))






    app.add_handler(CommandHandler("startphoto", cmd_startphoto))






    app.add_handler(CommandHandler("stopphoto", cmd_stopphoto))






    app.add_handler(CommandHandler("clearphotos", cmd_clearphotos))













    # Existing Commands






    app.add_handler(CommandHandler("over", cmd_over))






    app.add_handler(CommandHandler("ncthreads", cmd_ncthreads))






    app.add_handler(CommandHandler("song", cmd_song))






    app.add_handler(CommandHandler("stopspam", cmd_stopspam))






    app.add_handler(CommandHandler("upall", cmd_upall))






    # app.add_handler(CommandHandler("leave", cmd_leave))  # Disabled per user request






    app.add_handler(CommandHandler("bye", cmd_bye))






    app.add_handler(CommandHandler("stop", cmd_stop))






    app.add_handler(CommandHandler("stopall", cmd_stopall))






    app.add_handler(CommandHandler("speed", cmd_speed))






    app.add_handler(CommandHandler("entrust", cmd_entrust))






    app.add_handler(CommandHandler("revoke", cmd_revoke))






    app.add_handler(CommandHandler("list", cmd_list))






    app.add_handler(CommandHandler("setprefix", cmd_setprefix))






    app.add_handler(CommandHandler("status", cmd_status))






    app.add_handler(CommandHandler("help", cmd_help))






    app.add_handler(CommandHandler("menu", cmd_menu))






    app.add_handler(CommandHandler("vmenu", cmd_menu))






    app.add_handler(CommandHandler("videomenu", cmd_menu))






    app.add_handler(CommandHandler("helptext", cmd_helptext))






    # Set video commands for each menu






    app.add_handler(CommandHandler("setvideomain", cmd_setvideo_main))






    app.add_handler(CommandHandler("setvideoattack", cmd_setvideo_attack))






    app.add_handler(CommandHandler("setvideomusic", cmd_setvideo_music))






    app.add_handler(CommandHandler("setvideosettings", cmd_setvideo_settings))






    app.add_handler(CommandHandler("setvideosstop", cmd_setvideo_stop))






    app.add_handler(CommandHandler("setvideoadmin", cmd_setvideo_admin))






    app.add_handler(CommandHandler("setvideoutility", cmd_setvideo_utility))






    app.add_handler(CommandHandler("setvideostatus", cmd_setvideo_status))






    app.add_handler(CommandHandler("setvideoover", cmd_setvideo_over))






    # Existing help video command






    app.add_handler(CommandHandler("sethelpvideo", cmd_sethelpvideo))






    app.add_handler(CommandHandler("start", cmd_start))













    return app













# ==================== RUN ALL BOTS ====================




















async def run_all_bots():






    global bots, apps, MAIN_BOT_ID













    unique_tokens = list(set(t.strip() for t in TOKENS if t.strip()))
    if not unique_tokens:
        raise RuntimeError("No Telegram bot token configured. Set BOT_TOKEN or BOT_TOKENS in Railway Variables.")













    print("🎀 STARTING ⋆ ˚｡⋆👑˚𝐑ᴏʜɪᴛ .⋆˚👑⋆｡˚ ULTRA BOTS 🎀")






    print("=" * 60)






    print(f"📌 Command Prefix: `{CMD_PREFIX}`")






    print(f"🧵 Thread Pool: 200 workers")






    print(f"⚡ Max Concurrent: {MAX_CONCURRENT_TASKS}")






    print(f"🚀 Speed Mode: INSTANT (0 delay)")






    print("=" * 60)













    async def start_bot(token, is_main=False):






        try:






            app = build_app(token)






            await app.initialize()






            await app.start()






            if is_main:






                await app.updater.start_polling()






            bot_info = await app.bot.get_me()






            role = "MAIN" if is_main else "WORKER"






            print(f"✅ @{bot_info.username} - ONLINE ({role})")






            return app, app.bot






        except Exception as e:






            print(f"❌ Failed: {e}")






            return None, None













    results = await asyncio.gather(*[






        start_bot(token, is_main=(i == 0))






        for i, token in enumerate(unique_tokens)






    ])













    first_bot_set = False













    for app, bot in results:






        if app and bot:






            apps.append(app)






            bots.append(bot)






            if not first_bot_set:






                MAIN_BOT_ID = bot.id






                first_bot_set = True













    if not first_bot_set and bots:






        MAIN_BOT_ID = bots[0].id













    print("=" * 60)






    print(f"🎉 {len(bots)} BOTS ONLINE INSTANTLY 🎉")






    print(f"📌 All commands use: `{CMD_PREFIX}` as prefix")






    print(f"📌 Main bot ID: {MAIN_BOT_ID}")






    print(f"⚡ COMMANDS EXECUTE INSTANTLY - NO DELAYS")






    print("=" * 60)













    await asyncio.Event().wait()













if __name__ == "__main__":






    try:






        asyncio.run(run_all_bots())






    except KeyboardInterrupt:






        print("\n🛑 SHUTTING DOWN INSTANTLY...")






        for task_list in active_attacks.values():






            for task in task_list:






                task.cancel()






        THREAD_POOL.shutdown(wait=False)






        print("🎀 SHUTDOWN COMPLETE 🎀")






