import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import requests
import urllib.parse
import time
import json
import logging
from datetime import datetime, timedelta
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Получение токена бота и API-ключей из переменных окружения
BOT_TOKEN = '8150509696:AAEIRTQR7Ddk3euhgqVSlv3CxubX6oH4b3o'
API_KEY_SOLAR = 'SLR-104F9883D4800B7A8DE213D5614386F678996FD8FE84F8396D9D1D9D80E12B8C72285EBFC1A37F70BD12CB59CD1360E6E386DCBC9F85DA7925644433902D659C-hasty'
CHANNEL_USERNAME = '@HastyScripts'

# Ваш ID пользователя (администратора)
ADMIN_USER_ID = 840219189

USER_DATA_FILE = 'user_data.json'
LANGUAGE_DATA_FILE = 'language_data.json'

# Загрузка данных из файла
try:
    if os.path.exists(USER_DATA_FILE) and os.path.getsize(USER_DATA_FILE) > 0:
        with open(USER_DATA_FILE, 'r') as f:
            user_data = json.load(f)
            # Преобразуем строки обратно в datetime объекты
            for user_id, time_str in user_data.items():
                user_data[user_id] = datetime.fromisoformat(time_str)
    else:
        user_data = {}
except FileNotFoundError:
    user_data = {}
except json.JSONDecodeError:
    user_data = {}

# Загрузка языковых настроек
try:
    if os.path.exists(LANGUAGE_DATA_FILE) and os.path.getsize(LANGUAGE_DATA_FILE) > 0:
        with open(LANGUAGE_DATA_FILE, 'r') as f:
            language_data = json.load(f)
    else:
        language_data = {}
except (FileNotFoundError, json.JSONDecodeError):
    language_data = {}

# Функция для сохранения данных в файл
def save_user_data():
    try:
        user_data_serializable = {user_id: time.isoformat() for user_id, time in user_data.items()}
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(user_data_serializable, f)
        logging.info("User data saved to file.")
    except Exception as e:
        logging.error(f"Error saving user data: {e}")

# Функция для сохранения языковых настроек
def save_language_data():
    try:
        with open(LANGUAGE_DATA_FILE, 'w') as f:
            json.dump(language_data, f)
        logging.info("Language data saved to file.")
    except Exception as e:
        logging.error(f"Error saving language data: {e}")

# Функция для получения языка пользователя
def get_user_language(user_id):
    return language_data.get(str(user_id), 'ru')  # По умолчанию русский

# Тексты на разных языках
TEXTS = {
    'ru': {
        'start': "👋<b>Приветствую,</b> @{username}!\n🤖<b>Данный бот был создан красавчиками с канала - </b><a href='https://t.me/hastyscripts'>HastyScripts</a>\n\n🛡<b>Бот способен обходить различные переходники, а также ключ-системы эксплойтов</b>\n\n✏️<b>Список доступных команд:</b>\n\n<b>/bypass [ссылка] - обход ключ системы</b>\n<b>/settings - настройки</b>\n<b>/status - статус обходимых сайтов</b>\n<b>/install - установка эксплоудера</b>\n<b>/tutorial - инструкция по получению ключа</b>\n\n🔥<b>Я очень надеюсь, что наш бот сможет вам помочь!</b>\n\n<b>Спонсоры Бота: @rondichscripts @cheats_robl0x @Hastyscripts</b>",
        'subscribe': f"<b>Пожалуйста, подпишитесь на канал {CHANNEL_USERNAME}, мы представляем вам бота бесплатно и ничего не требуем кроме подписки в замен!❤</b>",
        'invalid_url': "Пожалуйста, отправьте корректную ссылку.\n\nПример: https://bit.ly/4fvIPQB",
        'bypass_started': "<b>Обход начался...</b>",
        'bypass_results': "✅Результаты обхода:\nС кэшем:\n{0}\nБез кэша:\n{1}\n⌛Время: {2:.2f} сек.",
        'bypass_failed': "❌Не удалось обойти ссылку с помощью обоих вариантов.\n⌛Время: {0:.2f} сек.",
        'status': "✅<b>Bypass Status: Работает</b>\n\n<b>❤Список сайтов, которые обходит наш бот:</b>\n\n{0}",
        'tutorial': "<b>Как получить ключ от дельта?\n>1. Скачайте дельту, если она у вас не скачана - <a href='https://t.me/Hastyscripts/2525'>кликни чтобы скачать</a>\n>2. Зайдите в роблокс и нажмите получить ссылку[Receive Key]\n>3. Включите VPN, если грузит без него, то не включайте\n>4. Зайдите в бота и напишите /bypass ссылка</b>",
        'download_cheats': "<b>👉Все читы здесь!</b>\n<a href='https://t.me/Hastyscripts/2525'>ЧИТЫ НА ТЕЛЕФОН И НА ПК В ЭТОМ СООБЩЕНИИ!</a>",
        'stats_admin': "<b>Эта команда доступна только администратору.</b>",
        'stats': "<b>Статистика пользователей:</b>\n\nСегодня: {0}\nВчера: {1}\nЗа неделю: {2}\nЗа месяц: {3}",
        'settings': "⚙️ <b>Настройки</b>\n\nВыберите язык:",
        'language_changed': "<b>Язык успешно изменен на русский!</b>",
        'bypass_usage': "<b>♨️ Вы Забыли Указать Ссылку Для Обхода🔹\nОтправьте По Данной Форме 👇</b>\n\n<code>/bypass [ссылка]</code>"
    },
    'en': {
        'start': "<b>Hello,</b> @{username}!\n🤖<b>This bot was created by the beauties from the channel - </b><a href='https://t.me/hastyscripts'>HastyScripts</a>\n\n🛡<b>The bot is able to bypass various adapters, as well as exploit key systems</b>\n\n✏️<b>List of available commands:</b>\n\n<b>/bypass [link] - bypass system key</b>\n<b>/settings - settings</b>\n<b>/status - status of crawled sites</b>\n<b>/install - installation the explorer</b>\n<b>/tutorial - instructions for obtaining the key</b>\n\n🔥<b>I really hope our bot can help you!</b>\n\n<b>Bot Sponsors: @rondichscripts @cheats_robl0x @Hastyscripts</b>",
        'subscribe': f"<b>Please subscribe to the channel {CHANNEL_USERNAME}, we provide you with the bot for free and ask nothing in return except a subscription!❤</b>",
        'invalid_url': "<b>Please send a valid link.</b>\n\n<b>Example: https://bit.ly/4fvIPQB</b>",
        'bypass_started': "<b>Bypass started...</b>",
        'bypass_results': "✅<b>Bypass results:</b>\n<b>With cache:</b>\n{0}\n<b>Without cache:</b>\n{1}\n⏳<b>Time: <b>{2:.2f} <b>sec.</b>",
        'bypass_failed': "❌<b>Failed to bypass the link using both methods.</b>\n⏳<b>Time: </b>{0:.2f} <b>sec.</b>",
        'status': "✅<b>Bypass Status: Working</b>\n\n<b>❤List of sites our bot can bypass:</b>\n\n{0}",
        'tutorial': "<b>How to get Delta key?\n>1. Download Delta if you don't have it - <a href='https://t.me/Hastyscripts/2525'>click to download</a>\n>2. Go to Roblox and click get link[Receive Key]\n>3. Enable VPN if it loads without it, then don't enable\n>4. Go to the bot and type /bypass link</b>",
        'download_cheats': "<b>👉All cheats here!</b>\n<a href='https://t.me/Hastyscripts/2525'>CHEATS FOR PHONE AND PC IN THIS MESSAGE!</a>",
        'stats_admin': "<b>This command is available only for administrator.</b>",
        'stats': "<b>User statistics:</b>\n\nToday: {0}\nYesterday: {1}\nLast week: {2}\nLast month: {3}",
        'settings': "⚙️ <b>Settings</b>\n\nChoose language:",
        'language_changed': "<b>Language successfully changed to English!</b>",
        'bypass_usage': "<b>♨️ You Forgot To Provide A Link To Bypass🔹\n Send Using This Form 👇</b>\n\n<code>/bypass [link]</code>"
    }
}

async def start(update, context):
    user_id = update.effective_user.id
    user = update.effective_user
    username = user.username if user.username else user.first_name
    user_data.setdefault(user_id, datetime.now())
    save_user_data()
    logging.info(f"User {user_id} started the bot. User data: {user_data}")
    
    lang = get_user_language(user_id)
    photo_path = 'banner.png'
    
    # Формируем текст с подстановкой username
    start_text = TEXTS[lang]['start'].format(username=username)
    
    try:
        with open(photo_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=photo, 
                caption=start_text,
                parse_mode=telegram.constants.ParseMode.HTML
            )
    except FileNotFoundError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=start_text,
            parse_mode=telegram.constants.ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"Error in start command: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка при выполнении команды.",
            parse_mode=telegram.constants.ParseMode.HTML
        )

async def bypass_command(update, context):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS[lang]['bypass_usage'],
            parse_mode=telegram.constants.ParseMode.HTML
        )
        return
    
    url = ' '.join(context.args)
    if not url.startswith(('http://', 'https://')):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS[lang]['invalid_url'],
            parse_mode=telegram.constants.ParseMode.HTML
        )
        return

    if not await check_subscription(context, user_id):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS[lang]['subscribe'],
            parse_mode=telegram.constants.ParseMode.HTML
        )
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=TEXTS[lang]['bypass_started'],
        parse_mode=telegram.constants.ParseMode.HTML
    )
    
    start_time = time.time()
    results = await try_bypass(url)
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    if results:
        cached_results = "\n".join([f"{i}) {result}" for i, result in enumerate(results['cached'], 1)])
        refreshed_results = "\n".join([f"{i}) {result}" for i, result in enumerate(results['refreshed'], 1)])
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS[lang]['bypass_results'].format(cached_results, refreshed_results, elapsed_time),
            parse_mode=telegram.constants.ParseMode.HTML
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS[lang]['bypass_failed'].format(elapsed_time),
            parse_mode=telegram.constants.ParseMode.HTML
        )

async def handle_message(update, context):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    user_data.setdefault(user_id, datetime.now())
    save_user_data()
    logging.info(f"User {user_id} sent a message. User data: {user_data}")
    
    if not await check_subscription(context, user_id):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS[lang]['subscribe'],
            parse_mode=telegram.constants.ParseMode.HTML
        )
        return

    url = update.message.text
    if not url.startswith(('http://', 'https://')):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS[lang]['invalid_url'],
            parse_mode=telegram.constants.ParseMode.HTML
        )
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=TEXTS[lang]['bypass_started'],
        parse_mode=telegram.constants.ParseMode.HTML
    )
    
    start_time = time.time()
    results = await try_bypass(url)
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    if results:
        cached_results = "\n".join([f"{i}) {result}" for i, result in enumerate(results['cached'], 1)])
        refreshed_results = "\n".join([f"{i}) {result}" for i, result in enumerate(results['refreshed'], 1)])
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS[lang]['bypass_results'].format(cached_results, refreshed_results, elapsed_time),
            parse_mode=telegram.constants.ParseMode.HTML
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS[lang]['bypass_failed'].format(elapsed_time),
            parse_mode=telegram.constants.ParseMode.HTML
        )

async def settings(update, context):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang_ru'),
            InlineKeyboardButton("🇬🇧 English", callback_data='set_lang_en')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=TEXTS[lang]['settings'],
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.HTML
    )

async def language_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang = query.data.split('_')[-1]  # Получаем 'ru' или 'en' из callback_data
    
    language_data[str(user_id)] = lang
    save_language_data()
    
    await query.edit_message_text(
        text=TEXTS[lang]['language_changed'],
        parse_mode=telegram.constants.ParseMode.HTML
    )

async def check_subscription(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        logging.info(f"User {user_id} membership status in channel {CHANNEL_USERNAME}: {member.status}")
        return member.status in ['member', 'administrator', 'creator']
    except telegram.error.BadRequest:
        logging.warning(f"Channel {CHANNEL_USERNAME} not found.")
        return False
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
        return False

async def try_bypass(url):
    encoded_url = urllib.parse.quote(url)
    solar_cached = []
    solar_refreshed = []

    # Solar-X (cached)
    api_url_solar = f"https://api.solar-x.top/api/v3/premium/bypass?url={encoded_url}&apikey={API_KEY_SOLAR}"
    try:
        response_solar = requests.get(api_url_solar)
        response_solar.raise_for_status()
        data_solar = response_solar.json()
        if data_solar.get('status') == 'success' and 'result' in data_solar:
            solar_cached.append(data_solar['result'])
    except requests.exceptions.RequestException as e:
        logging.error(f"Solar-X error (cached): {e}")
    except json.JSONDecodeError as e:
        logging.error(f"Solar-X JSON decode error (cached): {e}")
    except Exception as e:
        logging.error(f"Unknown Solar-X error (cached): {e}")

    # Solar-X (refreshed)
    api_url_solar_refresh = f"https://api.solar-x.top/api/v3/premium/refresh?url={encoded_url}&apikey={API_KEY_SOLAR}"
    try:
        response_solar_refresh = requests.get(api_url_solar_refresh)
        response_solar_refresh.raise_for_status()
        data_solar_refresh = response_solar_refresh.json()
        if data_solar_refresh.get('status') == 'success' and 'result' in data_solar_refresh:
            solar_refreshed.append(data_solar_refresh['result'])
    except requests.exceptions.RequestException as e:
        logging.error(f"Solar-X error (refreshed): {e}")
    except json.JSONDecodeError as e:
        logging.error(f"Solar-X JSON decode error (refreshed): {e}")
    except Exception as e:
        logging.error(f"Unknown Solar-X error (refreshed): {e}")

    if solar_cached or solar_refreshed:
        return {'cached': solar_cached, 'refreshed': solar_refreshed}
    return None

async def status(update, context):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    photo_path = 'banner2.png'
    api_status_url = "https://api.solar-x.top/api/v3/status"
    
    supported_bypasses = {
        'ru': "<blockquote>>Codex - Android - IOS\n\n>Vega X[soon]\n\nKeyRBLX\n\n>Linkvertise\n\n>Lootlabs/Admaven\n\n>Mediafire (direct download)\n\n>Pasting services:\n >pastebin\n >pastedrop\n >justpaste\n >pastecanyon\n >goldpaster\n\n>discord (gets raw content of pastes)\n\n>Link lockers\n >mboost\n >rekonise\n >socialwolvez\n >sub2get\n >sub2unlock (.com, .net)\n >sub4unlock.com\n >adfoc.us\n >unlocknow.net\n >bstlar\n >ldnesfspublic.org\n\n>RelzHub\n\n>Trigon Evo (Whitelist Key System + Auto Renew)\n\n>Delta X - Android - IOS</blockquote>",
        'en': "<blockquote>>Codex - Android - IOS\n\n>Vega X[soon]\n\nKeyRBLX\n\n>Linkvertise\n\n>Lootlabs/Admaven\n\n>Mediafire (direct download)\n\n>Pasting services:\n >pastebin\n >pastedrop\n >justpaste\n >pastecanyon\n >goldpaster\n\n>discord (gets raw content of pastes)\n\n>Link lockers\n >mboost\n >rekonise\n >socialwolvez\n >sub2get\n >sub2unlock (.com, .net)\n >sub4unlock.com\n >adfoc.us\n >unlocknow.net\n >bstlar\n >ldnesfspublic.org\n\n>RelzHub\n\n>Trigon Evo (Whitelist Key System + Auto Renew)\n\n>Delta X - Android - IOS</blockquote>"
    }
    
    try:
        response = requests.get(api_status_url)
        response.raise_for_status()
        if response.status_code == 200:
            status_text = TEXTS[lang]['status'].format(supported_bypasses[lang])
            try:
                with open(photo_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=status_text,
                        parse_mode=telegram.constants.ParseMode.HTML
                    )
            except FileNotFoundError:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=status_text,
                    parse_mode=telegram.constants.ParseMode.HTML
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌API status error.",
                parse_mode=telegram.constants.ParseMode.HTML
            )
    except requests.exceptions.RequestException as e:
        logging.error(f"API status error: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌Could not get API status.",
            parse_mode=telegram.constants.ParseMode.HTML
        )
    except Exception as e:
        logging.error(f"Unknown status error: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌Could not get status: {e}",
            parse_mode=telegram.constants.ParseMode.HTML
        )

async def tutorial(update, context):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=TEXTS[lang]['tutorial'],
        parse_mode=telegram.constants.ParseMode.HTML
    )

async def download_cheats(update, context):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=TEXTS[lang]['download_cheats'],
        parse_mode=telegram.constants.ParseMode.HTML
    )

async def stats(update, context):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS[lang]['stats_admin'],
            parse_mode=telegram.constants.ParseMode.HTML
        )
        return

    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(weeks=1)
    month_ago = today - timedelta(days=30)

    today_users = sum(1 for user_time in user_data.values() if user_time >= today)
    yesterday_users = sum(1 for user_time in user_data.values() if yesterday <= user_time < today)
    week_users = sum(1 for user_time in user_data.values() if week_ago <= user_time < today)
    month_users = sum(1 for user_time in user_data.values() if month_ago <= user_time < today)

    stats_message = TEXTS[lang]['stats'].format(today_users, yesterday_users, week_users, month_users)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=stats_message,
        parse_mode=telegram.constants.ParseMode.HTML
    )

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('bypass', bypass_command))
    application.add_handler(CommandHandler('install', download_cheats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('tutorial', tutorial))
    application.add_handler(CommandHandler('stats', stats))
    application.add_handler(CommandHandler('settings', settings))
    application.add_handler(CallbackQueryHandler(language_callback, pattern='^set_lang_'))

    application.run_polling()

if __name__ == '__main__':
    main()
