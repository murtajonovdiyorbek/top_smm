import telebot
from telebot import types
import json
import os
from datetime import datetime
import requests
import re
from typing import Optional, Dict, Any
import logging
import time

# Logging sozlash (Windows uchun UTF-8)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Windows console uchun UTF-8
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# ===== KONFIGURATSIYA =====
BOT_TOKEN = "8326460288:AAGjU7OOrxH6ktDej5yhpcIGyt1h-Mo2jaQ"
ADMIN_ID = 2138780687
SMM_API_KEY = "b1c75de81f29e150b1f86aa0261d2eb2"
CARD_NUMBER = "4177 4901 5211 4726"
CARD_HOLDER = "ДИЁРБЕК М."
CANCEL_BTN = "❌ Отменить"


# Validation
if not all([BOT_TOKEN, ADMIN_ID, SMM_API_KEY, CARD_NUMBER]):
    raise ValueError("Ошибка конфигурации!")

bot = telebot.TeleBot(BOT_TOKEN)

# API ma'lumotlari
SMM_API_URL = "https://smmpanel.net/api/v2"

# Anti-spam
user_last_action = {}
ACTION_COOLDOWN = 3  # sekund

# Ma'lumotlar fayli
DATA_FILE = "bot_data.json"

# NARXLAR - RUSCHA
PRICES = {
    "instagram": {
        "followers": {
            "name": "👥 Подписчики",
            "options": [
                {"quantity": 100, "price": 45, "service_id": 2342},
                {"quantity": 200, "price": 85, "service_id": 2342},
                {"quantity": 300, "price": 125, "service_id": 2342},
                {"quantity": 500, "price": 165, "service_id": 2342},
                {"quantity": 1000, "price": 355, "service_id": 2342},
            ]
        },
        "likes": {
            "name": "❤️ Лайки",
            "options": [
                {"quantity": 100, "price": 30, "service_id": 847},
                {"quantity": 200, "price": 45, "service_id": 847},
                {"quantity": 500, "price": 95, "service_id": 847},
                {"quantity": 1000, "price": 155, "service_id": 847},
            ]
        },
        "video_views": {
            "name": "▶️ Просмотры видео / Reels",
            "options": [
                {"quantity": 1000, "price": 22, "service_id": 2550},
                {"quantity": 2000, "price": 40, "service_id": 2550},
                {"quantity": 5000, "price": 85, "service_id": 2550},
                {"quantity": 10000, "price": 180, "service_id": 2550},
            ]
        },
        "story_views": {
            "name": "👁 Просмотры сторис",
            "options": [
                {"quantity": 100, "price": 25, "service_id": 720},
                {"quantity": 200, "price": 35, "service_id": 720},
                {"quantity": 500, "price": 70, "service_id": 720},
                {"quantity": 1000, "price": 135, "service_id": 720},
            ]
        },

        # ✅ YANGI: comment likes
        "comment_likes": {
            "name": "👍 Лайки на комментарии",
            "options": [
                {"quantity": 50, "price": 50, "service_id": 1845},
                {"quantity": 100, "price": 100, "service_id": 1845},
                {"quantity": 200, "price": 205, "service_id": 1845},
                {"quantity": 500, "price": 505, "service_id": 1845},
            ]
        },

        # ✅ YANGI: saves
        "saves": {
            "name": "💾 Сохранения (Saves)",
            "options": [
                {"quantity": 50, "price": 15, "service_id": 267},
                {"quantity": 100, "price": 20, "service_id": 267},
                {"quantity": 200, "price": 25, "service_id": 267},
                {"quantity": 500, "price": 35, "service_id": 267},
                {"quantity": 1000, "price": 55, "service_id": 267},
            ]
        },

        # ✅ YANGI: shares
        "shares": {
            "name": "📤 Репосты / Shares",
            "options": [
                {"quantity": 100, "price": 35, "service_id": 2463},
                {"quantity": 200, "price": 45, "service_id": 2463},
                {"quantity": 500, "price": 75, "service_id": 2463},
                {"quantity": 1000, "price": 150, "service_id": 2463},
            ]
        },

        # ✅ YANGI: live views (daqiqa bo'yicha)
        "live_views": {
            "name": "🔴 Live Views (трансляция)",
            "options": [
                {"quantity": 100, "price": 100, "service_id": 548},  # 15 min
                {"quantity": 200, "price": 150, "service_id": 548},
                {"quantity": 100, "price": 130, "service_id": 662},  # 30 min
                {"quantity": 200, "price": 180, "service_id": 662},
                {"quantity": 100, "price": 150, "service_id": 831},  # 60 min
                {"quantity": 200, "price": 200, "service_id": 831},
            ]
        },
    },

    "tiktok": {
        "followers": {
            "name": "👥 Подписчики",
            "options": [
                {"quantity": 100, "price": 45, "service_id": 2516},
                {"quantity": 200, "price": 90, "service_id": 2516},
                {"quantity": 500, "price": 215, "service_id": 2516},
                {"quantity": 1000, "price": 355, "service_id": 2516},
            ]
        },

        # ⚠️ Eslatma: Senda views service_id=3019 bor edi. Panel ro'yxatingda uning rate ko'rinmadi.
        # Agar panelda 3019 mavjud bo'lsa, qoldiramiz.
        "video_views": {
            "name": "▶️ Просмотры видео",
            "options": [
                {"quantity": 1000, "price": 275, "service_id": 3006},
                {"quantity": 2000, "price": 500, "service_id": 3006},
                {"quantity": 5000, "price": 1150, "service_id": 3006},
                {"quantity": 10000, "price": 2500, "service_id": 3006},
            ]
        },

        "likes": {
            "name": "❤️ Лайки",
            "options": [
                {"quantity": 100, "price": 30, "service_id": 1794},
                {"quantity": 200, "price": 40, "service_id": 1794},
                {"quantity": 500, "price": 70, "service_id": 1794},
                {"quantity": 1000, "price": 130, "service_id": 1794},
            ]
        },

        # ✅ YANGI: shares
        "shares": {
            "name": "📤 Репосты / Shares",
            "options": [
                {"quantity": 100, "price": 20, "service_id": 2340},
                {"quantity": 200, "price": 25, "service_id": 2340},
                {"quantity": 500, "price": 45, "service_id": 2340},
                {"quantity": 1000, "price": 85, "service_id": 2340},
            ]
        },

        # ✅ YANGI: saves
        "saves": {
            "name": "💾 Сохранения (Saves)",
            "options": [
                {"quantity": 100, "price": 15, "service_id": 2703},
                {"quantity": 200, "price": 20, "service_id": 2703},
                {"quantity": 500, "price": 25, "service_id": 2703},
                {"quantity": 1000, "price": 45, "service_id": 2703},
            ]
        },

        # ✅ YANGI: views retention (ko'proq sifatli ko'rish)
        "views_retention": {
            "name": "⏱ Просмотры с удержанием (Retention)",
            "options": [
                {"quantity": 1000, "price": 250, "service_id": 3005},  # 30 sec
                {"quantity": 2000, "price": 350, "service_id": 3005},
                {"quantity": 5000, "price": 700, "service_id": 3005},

                {"quantity": 1000, "price": 300, "service_id": 3006},  # 60 sec
                {"quantity": 2000, "price": 580, "service_id": 3006},
            ]
        },

        # ✅ YANGI: comments
        "comments_custom": {
            "name": "💬 Комментарии (CUSTOM)",
            "options": [
                {"quantity": 10, "price": 15, "service_id": 347},
                {"quantity": 20, "price": 22, "service_id": 347},
                {"quantity": 50, "price": 55, "service_id": 347},
                {"quantity": 100, "price": 120, "service_id": 347},
            ]
        },

        # ✅ YANGI: live likes
        "live_likes": {
            "name": "🔴 LiveStream Likes",
            "options": [
                {"quantity": 100, "price": 15, "service_id": 87},
                {"quantity": 500, "price": 35, "service_id": 87},
                {"quantity": 1000, "price": 95, "service_id": 87},

                {"quantity": 100, "price": 35, "service_id": 3052},  # REAL
                {"quantity": 500, "price": 65, "service_id": 3052},
            ]
        },
    },

    "telegram": {
        "members": {
            "name": "👥 Участники канала",
            "options": [
                {"quantity": 100, "price": 45, "service_id": 1868},
                {"quantity": 200, "price": 55, "service_id": 1868},
                {"quantity": 500, "price": 85, "service_id": 1868},
                {"quantity": 1000, "price": 155, "service_id": 1868}
            ]
        },
        "views": {
            "name": "👁 Просмотры постов",
            "options": [
                {"quantity": 1000, "price": 19, "service_id": 2308},
                {"quantity": 2000, "price": 30, "service_id": 2308},
                {"quantity": 5000, "price": 50, "service_id": 2308},
                {"quantity": 10000, "price": 105, "service_id": 2308}
            ]
        }
    },

    # ✅ YANGI PLATFORM: YouTube
    "youtube": {
        "views": {
            "name": "👁 Просмотры видео",
            "options": [
                {"quantity": 100, "price": 25, "service_id": 403},
                {"quantity": 500, "price": 50, "service_id": 403},
                {"quantity": 1000, "price": 105, "service_id": 668},
                {"quantity": 2000, "price": 255, "service_id": 303},
                {"quantity": 5000, "price": 535, "service_id": 2609},
                {"quantity": 10000, "price": 955, "service_id": 2995},
                {"quantity": 100000, "price": 9550, "service_id": 2994},
            ]
        },
        "subscribers": {
            "name": "👥 Подписчики (Subscribers)",
            "options": [
                {"quantity": 50, "price": 90, "service_id": 2999},
                {"quantity": 100, "price": 170, "service_id": 2999},
                {"quantity": 500, "price": 770, "service_id": 3027},
                {"quantity": 1000, "price": 1550, "service_id": 3027},
            ]
        },
        "likes": {
            "name": "❤️ Лайки",
            "options": [
                {"quantity": 10, "price": 5, "service_id": 2451},
                {"quantity": 50, "price": 20, "service_id": 2451},
                {"quantity": 100, "price": 35, "service_id": 2451},
                {"quantity": 500, "price": 95, "service_id": 2451},
            ]
        },
        "shorts_views": {
            "name": "📱 Shorts - Просмотры",
            "options": [
                {"quantity": 100, "price": 55, "service_id": 1941},
                {"quantity": 500, "price": 170, "service_id": 1941},
                {"quantity": 1000, "price": 250, "service_id": 1941},
            ]
        },
        "shorts_likes": {
            "name": "📱 Shorts - Лайки",
            "options": [
                {"quantity": 10, "price": 8, "service_id": 2689},
                {"quantity": 50, "price": 35, "service_id": 2689},
                {"quantity": 100, "price": 70, "service_id": 2689},
            ]
        },
        "comment_likes": {
            "name": "👍 Лайки на комментарии (UPVOTES)",
            "options": [
                {"quantity": 10, "price": 15, "service_id": 2331},
                {"quantity": 50, "price": 35, "service_id": 2331},
                {"quantity": 100, "price": 65, "service_id": 2331},
            ]
        },
        "watch_hours": {
            "name": "⏱ Watch Hours",
            "options": [
                {"quantity": 100, "price": 100, "service_id": 537},
                {"quantity": 100, "price": 170, "service_id": 3151},
                {"quantity": 100, "price": 200, "service_id": 3152},
            ]
        }
    }
}


# ===== UTILITY FUNCTIONS =====

def load_data() -> Dict[str, Any]:
    """Ma'lumotlarni yuklash"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ma'lumot yuklashda xato: {e}")

    return {"users": {}, "orders": [], "pending_payments": [], "bans": []}


def is_banned(user_id: int) -> bool:
    data = load_data()
    return data["users"].get(str(user_id), {}).get("is_banned", False)



def save_data(data: Dict[str, Any]) -> bool:
    """Ma'lumotlarni saqlash"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ma'lumot saqlashda xato: {e}")
        return False


def check_rate_limit(user_id: int) -> bool:
    """Spam oldini olish"""
    now = datetime.now()
    if user_id in user_last_action:
        time_passed = (now - user_last_action[user_id]).total_seconds()
        if time_passed < ACTION_COOLDOWN:
            return False

    user_last_action[user_id] = now
    return True


def validate_link(platform: str, link: str) -> Optional[str]:
    patterns = {
        "instagram": r'(https?://)?(www\.)?instagram\.com/[A-Za-z0-9_.]+/?',
        "tiktok": r'(https?://)?(www\.)?(tiktok\.com|vm\.tiktok\.com)/[@A-Za-z0-9_.]+/?',
        "telegram": r'(https?://)?(www\.)?(t\.me|telegram\.me)/[A-Za-z0-9_]+/?',
        "youtube": r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
    }

    if platform not in patterns:
        return None

    if re.match(patterns[platform], link):
        return link
    return None


def get_user_balance(user_id: int) -> int:
    """Foydalanuvchi balansini olish"""
    data = load_data()
    return data["users"].get(str(user_id), {}).get("balance", 0)


def update_balance(user_id: int, amount: int) -> bool:
    """Balansni yangilash"""
    try:
        data = load_data()
        user_id_str = str(user_id)

        if user_id_str not in data["users"]:
            data["users"][user_id_str] = {"balance": 0, "orders": []}

        data["users"][user_id_str]["balance"] += amount

        logger.info(
            f"Balans yangilandi: User {user_id}, amount {amount}, new balance {data['users'][user_id_str]['balance']}")

        return save_data(data)
    except Exception as e:
        logger.error(f"Balans yangilashda xato: {e}")
        return False




@bot.message_handler(commands=['broadcast'])
def broadcast_start(message):
    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(
        message.chat.id,
        "📣 *Рассылка*\n\n"
        "Hamma foydalanuvchilarga yuboriladigan xabarni yozing.\n"
        "Bekor qilish: /cancel",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, broadcast_send)



def broadcast_send(message):
    if message.from_user.id != ADMIN_ID:
        return

    text = (message.text or "").strip()

    if text.lower() == "/cancel":
        bot.send_message(message.chat.id, "❌ Рассылка отменена.", reply_markup=create_main_menu())
        return

    data = load_data()
    user_ids = list(data.get("users", {}).keys())  # string id lar

    sent = 0
    failed = 0

    bot.send_message(message.chat.id, f"⏳ Рассылка boshlandi. Jami: {len(user_ids)} ta")

    for uid_str in user_ids:
        try:
            uid = int(uid_str)
            bot.send_message(uid, text)
            sent += 1
            time.sleep(0.05)  # ✅ Telegram limitdan oshmaslik uchun kichik pauza
        except Exception as e:
            failed += 1
            logger.warning(f"Broadcast failed to {uid_str}: {e}")

    bot.send_message(
        message.chat.id,
        f"✅ Рассылка yakunlandi!\n"
        f"📨 Yuborildi: {sent}\n"
        f"⚠️ Bormadi: {failed}",
        reply_markup=create_main_menu()
    )




def create_main_menu() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📸 Instagram", "🎵 TikTok")
    markup.row("✈️ Telegram", "▶️ YouTube")
    markup.row("💰 Баланс")
    markup.row("💳 Пополнить", "📊 Заказы")
    return markup



# ===== SMM API FUNCTIONS =====

def send_smm_order(service_id: str, link: str, quantity: int) -> Dict[str, Any]:
    """SMM Panel API ga buyurtma yuborish"""
    try:
        payload = {
            'key': SMM_API_KEY,
            'action': 'add',
            'service': service_id,
            'link': link,
            'quantity': quantity
        }

        logger.info(f"SMM so'rov: service={service_id}, link={link}, quantity={quantity}")

        response = requests.post(SMM_API_URL, data=payload, timeout=10)
        result = response.json()

        logger.info(f"SMM javob: {result}")

        if 'order' in result:
            return {"success": True, "order_id": result['order']}
        else:
            return {"success": False, "error": result.get('error', 'Неизвестная ошибка')}

    except requests.exceptions.Timeout:
        logger.error("SMM API timeout")
        return {"success": False, "error": "API не отвечает"}
    except Exception as e:
        logger.error(f"SMM xato: {e}")
        return {"success": False, "error": str(e)}


# ===== BOT HANDLERS =====

@bot.message_handler(commands=['start'])
def start(message):
    """Start komandasi"""
    user_id = message.from_user.id
    data = load_data()

    if str(user_id) not in data["users"]:
        data["users"][str(user_id)] = {
            "balance": 0,
            "orders": [],
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_data(data)
        logger.info(f"Yangi foydalanuvchi: {user_id}")

    bot.send_message(
        message.chat.id,
        f"👋 Здравствуйте, {message.from_user.first_name}!\n\n"
        "🚀 Добро пожаловать в SMM Bot!\n\n"
        "📱 Услуги накрутки для:\n"
        "• Instagram - подписчики, лайки, просмотры\n"
        "• TikTok - подписчики, лайки, просмотры\n"
        "• Telegram - участники, просмотры\n\n"
        "✅ Быстро и безопасно\n"
        "💰 Выгодные цены\n\n"
        "Выберите платформу:",
        reply_markup=create_main_menu()
    )


@bot.message_handler(commands=["id"])
def my_id(message):
    bot.send_message(
        message.chat.id,
        f"🆔 Ваш ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )



@bot.message_handler(func=lambda message: message.text == "💰 Баланс")
def check_balance(message):
    """Balansni ko'rish"""
    balance = get_user_balance(message.from_user.id)
    data = load_data()
    user_orders = len(data["users"].get(str(message.from_user.id), {}).get("orders", []))

    bot.send_message(
        message.chat.id,
        f"💰 *Ваш баланс:* {balance} сом\n"
        f"📦 *Заказов:* {user_orders}\n\n"
        "💳 Для пополнения нажмите 'Пополнить'",
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda message: message.text == "📊 Заказы")
def my_orders(message):
    """Foydalanuvchi buyurtmalarini ko'rsatish"""
    user_id = str(message.from_user.id)
    data = load_data()

    user_order_ids = data["users"].get(user_id, {}).get("orders", [])

    if not user_order_ids:
        bot.send_message(
            message.chat.id,
            "📦 У вас пока нет заказов.\n\n"
            "Выберите услугу из меню ниже.",
            reply_markup=create_main_menu()
        )
        return

    # Oxirgi 10 ta buyurtmani ko'rsatish
    recent_orders = [o for o in data["orders"] if o["id"] in user_order_ids[-10:]]

    message_text = "📊 *Ваши последние заказы:*\n\n"

    for order in reversed(recent_orders):
        status_emoji = "✅" if order["status"] == "processing" else "❌"
        status_text = "В работе" if order["status"] == "processing" else "Ошибка"

        message_text += (
            f"{status_emoji} *Заказ #{order['id']}*\n"
            f"📱 Платформа: {order['platform'].upper()}\n"
            f"📝 Услуга: {order['service']}\n"
            f"🔢 Количество: {order['quantity']}\n"
            f"💰 Цена: {order['price']} сом\n"
            f"📅 Дата: {order['date']}\n"
            f"Статус: {status_text}\n\n"
        )

    bot.send_message(
        message.chat.id,
        message_text,
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda message: message.text == "💳 Пополнить")
def add_balance(message):
    """Balans to'ldirish"""
    msg = bot.send_message(
        message.chat.id,
        "💰 *Пополнение баланса*\n\n"
        "Минимальная сумма: 10 сом\n"
        "Максимальная сумма: 100,000 сом\n\n"
        "Введите сумму пополнения (только цифры):",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_amount_input)


def process_amount_input(message):
    """To'lov summasini qabul qilish"""
    try:
        amount = int(message.text)

        if amount < 10:
            bot.send_message(
                message.chat.id,
                "❌ Минимальная сумма 10 сом!",
                reply_markup=create_main_menu()
            )
            return

        if amount > 100000:
            bot.send_message(
                message.chat.id,
                "❌ Максимальная сумма 100,000 сом!",
                reply_markup=create_main_menu()
            )
            return

        # To'lov ma'lumotlarini ko'rsatish
        bot.send_message(
            message.chat.id,
            f"💳 *Реквизиты для оплаты*\n\n"
            f"💰 Сумма: {amount} сом\n\n"
            f"📱 Номер карты: `{CARD_NUMBER}`\n"
            f"👤 Владелец карты: {CARD_HOLDER}\n\n"
            f"⚠️ *Важно:*\n"
            f"• Переведите ровно {amount} сом\n"
            f"• После оплаты отправьте скриншот чека\n"
            f"• Неверная сумма или поддельный чек будут отклонены",
            parse_mode="Markdown"
        )

        # QR kodni yuborish
        # QR kodniBni yuborish (fayl bo'sh bo'lsa yubormaymiz)
        qr_path = "qr_code.jpg"
        if os.path.exists(qr_path):
            try:
                if os.path.getsize(qr_path) > 0:
                    with open(qr_path, "rb") as photo:
                        bot.send_photo(message.chat.id, photo)
                else:
                    logger.warning("qr_code.jpg fayli bo'sh (0 KB), yuborilmadi.")
            except Exception as e:
                logger.error(f"QR kod yuklashda xato: {e}")

        msg = bot.send_message(
            message.chat.id,
            "📸 *Отправьте скриншот чека об оплате*\n\n"
            f"Сумма оплаты: *{amount} сом*",
            parse_mode="Markdown"
        )

        bot.register_next_step_handler(msg, lambda m: handle_payment_receipt(m, amount))

    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Введите только цифры!",
            reply_markup=create_main_menu()
        )


@bot.message_handler(content_types=['photo'])
def handle_payment_receipt(message, expected_amount=None):
    """To'lov chekini qabul qilish"""
    if expected_amount is None:
        bot.send_message(
            message.chat.id,
            "❌ Сначала нажмите 'Пополнить'!",
            reply_markup=create_main_menu()
        )
        return

    user_id = message.from_user.id
    username = message.from_user.username or "Нет"
    first_name = message.from_user.first_name

    data = load_data()
    payment_id = len(data["pending_payments"]) + 1

    payment = {
        "id": payment_id,
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "photo_id": message.photo[-1].file_id,
        "expected_amount": expected_amount,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending"
    }

    data["pending_payments"].append(payment)
    save_data(data)

    bot.send_message(
        message.chat.id,
        "✅ *Чек принят!*\n\n"
        f"💰 Сумма: {expected_amount} сом\n"
        "⏳ Администратор проверяет платеж...\n\n"
        "После подтверждения баланс будет пополнен.\n"
        "Обычно это занимает 5-30 минут.",
        parse_mode="Markdown",
        reply_markup=create_main_menu()
    )

    # Adminga xabar
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{payment_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{payment_id}")
    )

    try:
        bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=f"💳 <b>Новый платеж #{payment_id}</b>\n\n"
                    f"👤 Пользователь: {first_name}\n"
                    f"🆔 Username: @{username}\n"
                    f"🆔 User ID: <code>{user_id}</code>\n"
                    f"💰 Ожидаемая сумма: {expected_amount} сом\n"
                    f"📅 Дата: {payment['date']}",
            parse_mode="HTML",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Adminga xabar yuborishda xato: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_payment_decision(call):
    """Admin to'lovni tasdiqlash/rad etish"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ У вас нет доступа!")
        return

    action, payment_id = call.data.split("_")
    payment_id = int(payment_id)

    data = load_data()
    payment = next((p for p in data["pending_payments"] if p["id"] == payment_id), None)

    if not payment or payment["status"] != "pending":
        bot.answer_callback_query(call.id, "❌ Платеж не найден или уже обработан!")
        return

    if action == "approve":
        expected = payment.get("expected_amount", 0)

        msg = bot.send_message(
            ADMIN_ID,
            f"💳 Платеж #{payment_id}\n\n"
            f"💰 Пользователь запросил: {expected} сом\n\n"
            f"Сколько денег на чеке?\n"
            f"Введите сумму (только цифры):",
        )
        bot.register_next_step_handler(msg, lambda m: process_payment_approval(m, payment_id))

    else:  # reject
        payment["status"] = "rejected"
        save_data(data)

        bot.send_message(
            payment["user_id"],
            "❌ *Платеж отклонен*\n\n"
            "Причина: Неверный чек или сумма\n\n"
            "Пожалуйста, отправьте корректный чек.",
            parse_mode="Markdown"
        )

        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + "\n\n❌ <b>ОТКЛОНЕНО</b>",
            parse_mode="HTML"
        )


def process_payment_approval(message, payment_id):
    """To'lovni tasdiqlash jarayoni"""
    try:
        actual_amount = int(message.text)

        data = load_data()
        payment = next((p for p in data["pending_payments"] if p["id"] == payment_id), None)
        if not payment:
            bot.send_message(ADMIN_ID, "❌ Платеж не найден!")
            return

        expected_amount = int(payment.get("expected_amount", 0))
        user_id = payment["user_id"]
        user_id_str = str(user_id)

        if actual_amount < expected_amount:
            payment["status"] = "rejected"
            payment["actual_amount"] = actual_amount
            save_data(data)

            bot.send_message(
                user_id,
                f"⚠️ *Платеж отклонен!*\n\n"
                f"Вы запросили: {expected_amount} сом\n"
                f"На чеке: {actual_amount} сом\n\n"
                f"❌ Неверная сумма!",
                parse_mode="Markdown"
            )
            bot.send_message(ADMIN_ID, f"✅ Платеж #{payment_id} отклонен")
            return

        # ✅ Balansni shu data ichida yangilaymiz (update_balance chaqirmaymiz)
        if user_id_str not in data["users"]:
            data["users"][user_id_str] = {"balance": 0, "orders": []}

        data["users"][user_id_str]["balance"] += expected_amount
        new_balance = data["users"][user_id_str]["balance"]

        # Payment statusni ham shu yerda yangilaymiz
        payment["status"] = "approved"
        payment["actual_amount"] = actual_amount

        # ✅ Hammasini 1 marta saqlaymiz
        if not save_data(data):
            bot.send_message(ADMIN_ID, "❌ Ошибка при сохранении данных!")
            return

        logger.info(f"Payment approved: user={user_id}, amount={expected_amount}, new_balance={new_balance}")

        bot.send_message(
            user_id,
            f"✅ *Платеж подтвержден!*\n\n"
            f"💰 Ваш баланс: {new_balance} сом\n\n"
            f"Теперь вы можете заказывать услуги!",
            parse_mode="Markdown"
        )

        bot.send_message(
            ADMIN_ID,
            f"✅ Платеж #{payment_id} подтвержден!\n"
            f"💰 Добавлено: {expected_amount} сом\n"
            f"💳 Новый баланс: {new_balance} сом"
        )

    except ValueError:
        bot.send_message(ADMIN_ID, "❌ Введите только цифры!")
    except Exception as e:
        logger.error(f"Payment approval error: {e}")
        bot.send_message(ADMIN_ID, f"❌ Ошибка: {e}")



# ===== PLATFORM MENUS =====

@bot.message_handler(func=lambda message: message.text == "📸 Instagram")
def instagram_menu(message):
    markup = types.InlineKeyboardMarkup()
    for key, service in PRICES["instagram"].items():
        markup.add(types.InlineKeyboardButton(
            f"{service['name']}",
            callback_data=f"instagram_{key}"
        ))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))

    bot.send_message(
        message.chat.id,
        "📸 *Instagram - Накрутка*\n\n"
        "Выберите услугу:",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "🎵 TikTok")
def tiktok_menu(message):
    markup = types.InlineKeyboardMarkup()
    for key, service in PRICES["tiktok"].items():
        markup.add(types.InlineKeyboardButton(
            f"{service['name']}",
            callback_data=f"tiktok_{key}"
        ))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))

    bot.send_message(
        message.chat.id,
        "🎵 *TikTok - Накрутка*\n\n"
        "Выберите услугу:",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "✈️ Telegram")
def telegram_menu(message):
    markup = types.InlineKeyboardMarkup()
    for key, service in PRICES["telegram"].items():
        markup.add(types.InlineKeyboardButton(
            f"{service['name']}",
            callback_data=f"telegram_{key}"
        ))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))

    bot.send_message(
        message.chat.id,
        "✈️ *Telegram - Накрутка*\n\n"
        "Выберите услугу:",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "▶️ YouTube")
def youtube_menu(message):
    markup = types.InlineKeyboardMarkup()
    for key, service in PRICES["youtube"].items():
        markup.add(types.InlineKeyboardButton(
            f"{service['name']}",
            callback_data=f"youtube_{key}"
        ))
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_main"))

    bot.send_message(
        message.chat.id,
        "▶️ *YouTube - Накрутка*\n\nВыберите услугу:",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "❌ Отменить")
def cancel_order(message):
    bot.send_message(
        message.chat.id,
        "❌ Заказ отменён.",
        reply_markup=create_main_menu()
    )




@bot.callback_query_handler(func=lambda call: call.data.startswith("instagram_") or
                                              call.data.startswith("tiktok_") or
                                              call.data.startswith("telegram_") or
                                              call.data.startswith("youtube_"))
def handle_service_selection(call):
    """Xizmat tanlash"""
    parts = call.data.split("_")

    # platform = birinchi bo'lak, service_key = qolgan hammasi (story_views, video_views)
    platform = parts[0]
    service_key = "_".join(parts[1:])

    if platform in PRICES and service_key in PRICES[platform]:
        service = PRICES[platform][service_key]

        markup = types.InlineKeyboardMarkup()
        for option in service["options"]:
            markup.add(types.InlineKeyboardButton(
                f"{option['quantity']} шт - {option['price']} сом",
                callback_data=f"order_{platform}_{service_key}_{option['quantity']}_{option['price']}_{option['service_id']}"
            ))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data=f"back_{platform}"))

        bot.edit_message_text(
            f"📝 *{service['name']}*\n\n"
            f"💰 Ваш баланс: {get_user_balance(call.from_user.id)} сом\n\n"
            f"Выберите количество:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.answer_callback_query(call.id, "❌ Услуга не найдена!", show_alert=True)



@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def handle_order_placement(call):
    """Buyurtma berish"""
    if not check_rate_limit(call.from_user.id):
        bot.answer_callback_query(call.id, "⏳ Пожалуйста, подождите...")
        return

    parts = call.data.split("_")
    platform = parts[1]

    # Oxirgi 3 ta doim: quantity, price, service_id
    quantity = int(parts[-3])
    price = int(parts[-2])
    service_id = parts[-1]

    # service_key o'rtadagi qismi (platformdan keyin, quantitydan oldin)
    service_key = "_".join(parts[2:-3])

    # himoya (xato bo'lsa)
    if platform not in PRICES or service_key not in PRICES[platform]:
        bot.answer_callback_query(call.id, "❌ Услуга не найдена!", show_alert=True)
        return

    service_name = PRICES[platform][service_key]["name"]
    user_balance = get_user_balance(call.from_user.id)

    if user_balance < price:
        bot.answer_callback_query(
            call.id,
            f"❌ Недостаточно средств!\nНужно: {price} сом",
            show_alert=True
        )
        return

    # Har bir platforma + xizmat uchun link misollar
    LINK_EXAMPLES = {
        "instagram": {
            "default": "Пример: https://instagram.com/username",
            "followers": "Пример (профиль): https://instagram.com/username",
            "likes": "Пример (пост/remember/reel): https://www.instagram.com/p/POST_ID/  yoki  https://www.instagram.com/reel/REEL_ID/",
            "video_views": "Пример (reel/video): https://www.instagram.com/reel/REEL_ID/  yoki  https://www.instagram.com/p/POST_ID/",
            "story_views": "Пример (профиль для сторис): https://instagram.com/username",
            "comment_likes": "Пример (ссылка на пост/reel где есть комментарий): https://www.instagram.com/p/POST_ID/  yoki  https://www.instagram.com/reel/REEL_ID/",
            "saves": "Пример (пост/reel): https://www.instagram.com/p/POST_ID/  yoki  https://www.instagram.com/reel/REEL_ID/",
            "shares": "Пример (пост/reel): https://www.instagram.com/p/POST_ID/  yoki  https://www.instagram.com/reel/REEL_ID/",
            "live_views": "Пример (ссылка на LIVE или профиль): https://instagram.com/username  (LIVE должен быть запущен)"
        },

        "tiktok": {
            "default": "Пример: https://www.tiktok.com/@username",
            "followers": "Пример (профиль): https://www.tiktok.com/@username",
            "likes": "Пример (видео): https://www.tiktok.com/@username/video/VIDEO_ID",
            "video_views": "Пример (видео): https://www.tiktok.com/@username/video/VIDEO_ID",
            "shares": "Пример (видео): https://www.tiktok.com/@username/video/VIDEO_ID",
            "saves": "Пример (видео): https://www.tiktok.com/@username/video/VIDEO_ID",
            "views_retention": "Пример (видео): https://www.tiktok.com/@username/video/VIDEO_ID",
            "comments_custom": "Пример (видео, где будет комментарий): https://www.tiktok.com/@username/video/VIDEO_ID",
            "live_likes": "Пример (LIVE ссылка или профиль): https://www.tiktok.com/@username  (LIVE должен быть запущен)"
        },

        "telegram": {
            "default": "Пример: https://t.me/channel_name",
            "members": "Пример (канал/группа): https://t.me/channel_name",
            "views": "Пример (пост): https://t.me/channel_name/123"
        },

        "youtube": {
            "default": "Пример: https://www.youtube.com/watch?v=VIDEO_ID",
            "views": "Пример (видео): https://www.youtube.com/watch?v=VIDEO_ID  или  https://youtu.be/VIDEO_ID",
            "likes": "Пример (видео): https://www.youtube.com/watch?v=VIDEO_ID",
            "subscribers": "Пример (канал): https://www.youtube.com/@channelname  или  https://www.youtube.com/channel/CHANNEL_ID",
            "shorts_views": "Пример (Shorts): https://www.youtube.com/shorts/SHORTS_ID",
            "shorts_likes": "Пример (Shorts): https://www.youtube.com/shorts/SHORTS_ID",
            "comment_likes": "Пример (видео, где есть комментарий): https://www.youtube.com/watch?v=VIDEO_ID",
            "watch_hours": "Пример (видео): https://www.youtube.com/watch?v=VIDEO_ID  (длина видео должна подходить под услугу)"
        }
    }

    def get_link_example(platform: str, service_key: str) -> str:
        """Platforma + xizmatga mos link misol qaytaradi"""
        p = LINK_EXAMPLES.get(platform, {})
        return p.get(service_key) or p.get("default") or "Отправьте корректную ссылку."

    example_text = get_link_example(platform, service_key)  # agar sen shu funksiyani qo‘shgan bo‘lsang
    # yoki eski link_examples ishlatsang ham bo‘ladi:
    # example_text = link_examples.get(platform, "")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(CANCEL_BTN)

    bot.send_message(
        call.message.chat.id,
        "📝 <b>{}</b>\n\n"
        "🔢 Количество: {}\n"
        "💰 Цена: {} сом\n\n"
        "📎 Отправьте ссылку:\n"
        "<code>{}</code>\n\n"
        "Чтобы отменить — нажмите <b>❌ Отменить</b>.".format(service_name, quantity, price, example_text),
        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler_by_chat_id(
        call.message.chat.id,
        lambda m: process_order(m, platform, service_key, service_name, quantity, price, service_id)
    )

    bot.register_next_step_handler_by_chat_id(
        call.message.chat.id,
        lambda m: process_order(m, platform, service_key, service_name, quantity, price, service_id)
    )


def process_order(message, platform, service_key, service_name, quantity, price, service_id):
    text = (message.text or "").strip()

    # ✅ Cancel bosilsa
    if text == CANCEL_BTN:
        bot.send_message(
            message.chat.id,
            "✅ <b>Заказ отменён.</b>\n\nВы вернулись в главное меню.",
            parse_mode="HTML",
            reply_markup=create_main_menu()
        )
        return

    link = text
    user_id = message.from_user.id

    # Link validatsiya
    if not validate_link(platform, link):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(CANCEL_BTN)

        bot.send_message(
            message.chat.id,
            f"❌ <b>Неверная ссылка на {platform.upper()}!</b>\n\n"
            f"Отправьте корректную ссылку.\n\n"
            f"Чтобы отменить — нажмите <b>{CANCEL_BTN}</b>.",
            parse_mode="HTML",
            reply_markup=markup
        )
        # ❗ Shu yerda qaytib ketamiz, foydalanuvchi yana link yuboradi
        bot.register_next_step_handler(
            message,
            lambda m: process_order(m, platform, service_key, service_name, quantity, price, service_id)
        )
        return


    # Balansdan yechish
    if not update_balance(user_id, -price):
        bot.send_message(
            message.chat.id,
            "❌ Ошибка! Попробуйте снова.",
            reply_markup=create_main_menu()
        )
        return

    # SMM Panel ga yuborish
    result = send_smm_order(service_id, link, quantity)

    # Buyurtmani saqlash
    data = load_data()
    order = {
        "id": len(data["orders"]) + 1,
        "user_id": user_id,
        "platform": platform,
        "service": service_name,
        "link": link,
        "price": price,
        "quantity": quantity,
        "service_id": service_id,
        "smm_order_id": result.get("order_id", "N/A") if result["success"] else "FAILED",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "processing" if result["success"] else "failed"
    }

    data["orders"].append(order)
    if str(user_id) in data["users"]:
        data["users"][str(user_id)]["orders"].append(order["id"])
    save_data(data)

    if result["success"]:
        bot.send_message(
            message.chat.id,
            f"✅ *Заказ принят!*\n\n"
            f"📋 ID заказа: {order['id']}\n"
            f"📱 Платформа: {platform.upper()}\n"
            f"📝 Услуга: {service_name}\n"
            f"🔢 Количество: {quantity}\n"
            f"💰 Цена: {price} сом\n\n"
            f"✅ Заказ в работе...\n"
            f"💳 Баланс: {get_user_balance(user_id)} сом",
            parse_mode="Markdown",
            reply_markup=create_main_menu()
        )

        try:
            bot.send_message(
                ADMIN_ID,
                f"✅ Новый заказ #{order['id']}\n"
                f"👤 {message.from_user.first_name}\n"
                f"📱 {platform.upper()}\n"
                f"💰 {price} сом"
            )
        except:
            pass

    else:
        update_balance(user_id, price)

        bot.send_message(
            message.chat.id,
            f"❌ *Ошибка!*\n\n"
            f"Заказ не выполнен.\n"
            f"Средства возвращены: {price} сом\n\n"
            f"Ошибка: {result.get('error', 'Неизвестная')}",
            parse_mode="Markdown",
            reply_markup=create_main_menu()
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("back_"))
def handle_back(call):
    """Ortga qaytish"""
    if call.data == "back_main":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Главное меню:", reply_markup=create_main_menu())
    elif call.data == "back_instagram":
        instagram_menu(call.message)
    elif call.data == "back_tiktok":
        tiktok_menu(call.message)
    elif call.data == "back_telegram":
        telegram_menu(call.message)
    elif call.data == "back_youtube":
        youtube_menu(call.message)


# ===== ADMIN =====
# =========================
# ===== ADMIN CLEAN =======
# =========================

ADMIN_MENU_BTN_BROADCAST = "📢 Рассылка"
ADMIN_MENU_BTN_GIVE = "➕ Give balance"
ADMIN_MENU_BTN_FIND = "🆔 Find user ID"
ADMIN_MENU_BTN_BACK = "🔙 Главное меню"


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def create_admin_menu() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(ADMIN_MENU_BTN_BROADCAST, ADMIN_MENU_BTN_GIVE)
    markup.row(ADMIN_MENU_BTN_FIND, ADMIN_MENU_BTN_BACK)
    return markup


def admin_inline_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👥 Users", callback_data="adm_users"),
        types.InlineKeyboardButton("⏳ Pending", callback_data="adm_pending"),
    )
    kb.add(
        types.InlineKeyboardButton("📊 Orders", callback_data="adm_orders"),
        types.InlineKeyboardButton("📣 Broadcast", callback_data="adm_broadcast"),
    )
    kb.add(
        types.InlineKeyboardButton("➕ Give balance", callback_data="adm_give"),
        types.InlineKeyboardButton("➖ Take balance", callback_data="adm_take"),
    )
    kb.add(
        types.InlineKeyboardButton("🚫 Ban", callback_data="adm_ban"),
        types.InlineKeyboardButton("✅ Unban", callback_data="adm_unban"),
    )
    kb.add(types.InlineKeyboardButton("💾 Export backup", callback_data="adm_export"))
    return kb


def build_admin_stats_text(data: dict) -> str:
    total_users = len(data.get("users", {}))
    total_orders = len(data.get("orders", []))
    pending = len([p for p in data.get("pending_payments", []) if p.get("status") == "pending"])

    total_balance = sum(u.get("balance", 0) for u in data.get("users", {}).values())
    completed = [o for o in data.get("orders", []) if o.get("status") == "processing"]
    total_revenue = sum(o.get("price", 0) for o in completed)

    text = (
        "👨‍💼 <b>Админ Панель</b>\n\n"
        "📊 <b>Статистика:</b>\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"📦 Заказов: <b>{total_orders}</b>\n"
        f"✅ Выполнено: <b>{len(completed)}</b>\n"
        f"⏳ Ожидает: <b>{pending}</b>\n\n"
        "💰 <b>Финансы:</b>\n"
        f"💳 Балансы: <b>{total_balance}</b> сом\n"
        f"💵 Доход: <b>{total_revenue}</b> сом\n\n"
        "🆔 Чтобы узнать user_id: нажмите «Find user ID»"
    )
    return text


@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        return

    data = load_data()
    bot.send_message(
        message.chat.id,
        build_admin_stats_text(data),
        parse_mode="HTML",
        reply_markup=create_admin_menu()
    )

    # ixtiyoriy: inline panel ham ko‘rsatish
    bot.send_message(
        message.chat.id,
        "⚙️ <b>Быстрые действия:</b>",
        parse_mode="HTML",
        reply_markup=admin_inline_kb()
    )


# ---------- INLINE CALLBACKS (adm_...) ----------

@bot.callback_query_handler(func=lambda c: (c.data or "").startswith("adm_"))
def admin_actions(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Нет доступа!", show_alert=True)
        return

    data = load_data()
    cmd = call.data

    if cmd == "adm_users":
        total = len(data.get("users", {}))
        banned = sum(1 for u in data.get("users", {}).values() if u.get("is_banned"))
        total_balance = sum(u.get("balance", 0) for u in data.get("users", {}).values())

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=(
                "👥 <b>Users</b>\n\n"
                f"👤 Всего: <b>{total}</b>\n"
                f"🚫 Забанено: <b>{banned}</b>\n"
                f"💳 Сумма балансов: <b>{total_balance}</b> сом"
            ),
            parse_mode="HTML",
            reply_markup=admin_inline_kb()
        )
        bot.answer_callback_query(call.id)
        return

    if cmd == "adm_pending":
        pending_list = [p for p in data.get("pending_payments", []) if p.get("status") == "pending"]
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=(
                "⏳ <b>Pending payments</b>\n\n"
                f"Всего ожидает: <b>{len(pending_list)}</b>\n\n"
                "Проверка — через кнопки ✅/❌ под чеком."
            ),
            parse_mode="HTML",
            reply_markup=admin_inline_kb()
        )
        bot.answer_callback_query(call.id)
        return

    if cmd == "adm_orders":
        orders = data.get("orders", [])
        last = orders[-5:] if len(orders) > 5 else orders
        if not last:
            text = "📊 <b>Orders</b>\n\nПока заказов нет."
        else:
            lines = ["📊 <b>Последние заказы</b>\n"]
            for o in reversed(last):
                st = "✅" if o.get("status") == "processing" else "❌"
                lines.append(
                    f"{st} <b>#{o.get('id')}</b> | {str(o.get('platform','')).upper()} | "
                    f"{o.get('price',0)} сом"
                )
            text = "\n".join(lines)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            parse_mode="HTML",
            reply_markup=admin_inline_kb()
        )
        bot.answer_callback_query(call.id)
        return

    if cmd == "adm_broadcast":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "📣 Отправь текст рассылки (или /cancel):")
        bot.register_next_step_handler(msg, admin_broadcast_step)
        return

    if cmd == "adm_give":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "➕ Формат: <code>user_id сумма</code>\nНапр: <code>123 50</code>", parse_mode="HTML")
        bot.register_next_step_handler(msg, admin_give_step)
        return

    if cmd == "adm_take":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "➖ Формат: <code>user_id сумма</code>\nНапр: <code>123 50</code>", parse_mode="HTML")
        bot.register_next_step_handler(msg, admin_take_step)
        return

    if cmd == "adm_ban":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "🚫 Отправь <code>user_id</code>:", parse_mode="HTML")
        bot.register_next_step_handler(msg, admin_ban_step)
        return

    if cmd == "adm_unban":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "✅ Отправь <code>user_id</code>:", parse_mode="HTML")
        bot.register_next_step_handler(msg, admin_unban_step)
        return

    if cmd == "adm_export":
        bot.answer_callback_query(call.id)
        backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(backup_name, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            with open(backup_name, "rb") as f:
                bot.send_document(call.message.chat.id, f)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Ошибка backup: {e}")
        return


# ---------- REPLY MENU (faqat admin ko‘radi) ----------

@bot.message_handler(func=lambda m: (m.text or "").strip() == ADMIN_MENU_BTN_BROADCAST)
def admin_broadcast_start(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.send_message(message.chat.id, "📣 Отправь текст рассылки (или /cancel):", reply_markup=create_admin_menu())
    bot.register_next_step_handler(msg, admin_broadcast_step)


def admin_broadcast_step(message):
    if not is_admin(message.from_user.id):
        return

    text = (message.text or "").strip()
    if text.lower() == "/cancel":
        bot.send_message(message.chat.id, "❌ Рассылка отменена.", reply_markup=create_admin_menu())
        return

    data = load_data()
    user_ids = list(data.get("users", {}).keys())

    sent = 0
    failed = 0

    bot.send_message(message.chat.id, f"⏳ Рассылка boshlandi. Jami: {len(user_ids)} ta", reply_markup=create_admin_menu())

    for uid_str in user_ids:
        try:
            uid = int(uid_str)
            bot.send_message(uid, text)
            sent += 1
            time.sleep(0.05)
        except Exception as e:
            failed += 1
            logger.warning(f"Broadcast failed to {uid_str}: {e}")

    bot.send_message(
        message.chat.id,
        f"✅ Рассылка yakunlandi!\n📨 Yuborildi: {sent}\n⚠️ Bormadi: {failed}",
        reply_markup=create_admin_menu()
    )


@bot.message_handler(func=lambda m: (m.text or "").strip() == ADMIN_MENU_BTN_GIVE)
def admin_give_start(message):
    if not is_admin(message.from_user.id):
        return
    msg = bot.send_message(message.chat.id, "➕ Формат: <code>user_id сумма</code>", parse_mode="HTML", reply_markup=create_admin_menu())
    bot.register_next_step_handler(msg, admin_give_step)


def admin_give_step(message):
    if not is_admin(message.from_user.id):
        return
    try:
        uid, amount = (message.text or "").split()
        update_balance(int(uid), int(amount))
        bot.send_message(message.chat.id, "✅ Готово", reply_markup=create_admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ Формат: user_id сумма\nНапр: 123 50", reply_markup=create_admin_menu())


def admin_take_step(message):
    if not is_admin(message.from_user.id):
        return
    try:
        uid, amount = (message.text or "").split()
        update_balance(int(uid), -int(amount))
        bot.send_message(message.chat.id, "✅ Готово", reply_markup=create_admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ Формат: user_id сумма\nНапр: 123 50", reply_markup=create_admin_menu())


def admin_ban_step(message):
    if not is_admin(message.from_user.id):
        return
    try:
        uid = int((message.text or "").strip())
        data = load_data()
        if str(uid) not in data["users"]:
            bot.send_message(message.chat.id, "❌ Пользователь не найден в базе.", reply_markup=create_admin_menu())
            return
        data["users"][str(uid)]["is_banned"] = True
        save_data(data)
        bot.send_message(message.chat.id, "🚫 Забанен", reply_markup=create_admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ Отправь только user_id цифрами.", reply_markup=create_admin_menu())


def admin_unban_step(message):
    if not is_admin(message.from_user.id):
        return
    try:
        uid = int((message.text or "").strip())
        data = load_data()
        if str(uid) not in data["users"]:
            bot.send_message(message.chat.id, "❌ Пользователь не найден в базе.", reply_markup=create_admin_menu())
            return
        data["users"][str(uid)]["is_banned"] = False
        save_data(data)
        bot.send_message(message.chat.id, "✅ Разбанен", reply_markup=create_admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ Отправь только user_id цифрами.", reply_markup=create_admin_menu())


@bot.message_handler(func=lambda m: (m.text or "").strip() == ADMIN_MENU_BTN_FIND)
def admin_find_user_id_start(message):
    if not is_admin(message.from_user.id):
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 <b>Find user ID</b>\n\n"
        "Отправьте:\n"
        "1) <code>@username</code> (например: <code>@diyorbek_muratjonov</code>)\n"
        "или\n"
        "2) Перешлите сообщение пользователя (forward)\n\n"
        "Отмена: /cancel",
        parse_mode="HTML",
        reply_markup=create_admin_menu()
    )
    bot.register_next_step_handler(msg, admin_find_user_id_process)


def admin_find_user_id_process(message):
    if not is_admin(message.from_user.id):
        return

    text = (message.text or "").strip()

    if text.lower() == "/cancel":
        bot.send_message(message.chat.id, "❌ Отменено.", reply_markup=create_admin_menu())
        return

    # 1) Forward bo‘lsa
    if message.forward_from:
        u = message.forward_from
        username = f"@{u.username}" if u.username else "нет"
        bot.send_message(
            message.chat.id,
            "✅ <b>Найдено по forward</b>\n\n"
            f"🆔 ID: <code>{u.id}</code>\n"
            f"👤 Имя: {u.first_name}\n"
            f"🔗 Username: {username}",
            parse_mode="HTML",
            reply_markup=create_admin_menu()
        )
        return

    # 2) Username bo‘lsa
    if text.startswith("@"):
        username_in = text[1:].lower()
        data = load_data()

        for uid_str, info in data.get("users", {}).items():
            if (info.get("username") or "").lower() == username_in:
                bot.send_message(
                    message.chat.id,
                    "✅ <b>Найдено по username</b>\n\n"
                    f"🆔 ID: <code>{uid_str}</code>\n"
                    f"👤 Имя: {info.get('first_name','')}\n"
                    f"🔗 Username: @{info.get('username','')}",
                    parse_mode="HTML",
                    reply_markup=create_admin_menu()
                )
                return

        bot.send_message(
            message.chat.id,
            "❌ Не найдено.\n\nВозможно пользователь ещё не нажимал /start в боте.",
            reply_markup=create_admin_menu()
        )
        return

    bot.send_message(
        message.chat.id,
        "❌ Неверный формат.\nОтправьте @username или forward сообщения пользователя.",
        reply_markup=create_admin_menu()
    )


@bot.message_handler(func=lambda m: (m.text or "").strip() == ADMIN_MENU_BTN_BACK)
def back_to_user_menu(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=create_main_menu())



@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    # ✅ Cancel bosilganda bu handler umuman aralashmasin
    if (message.text or "").strip() == CANCEL_BTN:
        return

    bot.send_message(
        message.chat.id,
        "❓ Неизвестная команда.\n\n"
        "Используйте меню ниже:",
        reply_markup=create_main_menu()
    )



if __name__ == "__main__":
    print("=" * 50)
    print("Bot ishga tushdi!")
    print("To'xtatish uchun: Ctrl+C")
    print("=" * 50)
    logger.info("Bot ishga tushdi")
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi (Ctrl+C)")
        print("\nBot to'xtatildi!")
    except Exception as e:
        logger.error(f"Bot to'xtadi: {e}")