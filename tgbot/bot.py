import os
import os.path
import sys
import re
import random
import string
import asyncio


from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InputMediaAudio
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackContext, ContextTypes


TOKEN = '7153515581:AAGLgLq0HUYuXkjz5tzAozQ4_CjjbqxSAyg'
DEBUG = False

ADMIN_USERNAME = "meselvarkovsky"
CONFIG_DIR = sys.argv[1]
CLIENTS_DIR = os.path.join(CONFIG_DIR, "clients")

START, START_ADMIN, START_ALLOWED, START_DENIED, INVITE, KICKOUT = range(6)



MARKUP_YES_NO = ReplyKeyboardMarkup([
    ["Да", "Нет"]
], one_time_keyboard=True)

MARKUP_ALLOWED = ReplyKeyboardMarkup([
    ["Скачать конфигурацию"]
], one_time_keyboard=True)

MARKUP_ADMIN_MENU = ReplyKeyboardMarkup([
    ["Пригласить", "Выгнать"],
    ["Моя конфигурация"], ["Генерировать"]
], one_time_keyboard=True)


def random_alphanumeric_string(length):
    return ''.join(
        random.choices(
            string.ascii_letters + string.digits,
            k=length
        )
    )


def is_client_exists(client_name: str):
    only_dirs = [os.path.splitext(d)[0] for d in os.listdir(CLIENTS_DIR) if os.path.isfile(os.path.join(CLIENTS_DIR, d))]
    if client_name in only_dirs:
        return True
    return False


def is_admin(username: str):
    if username == ADMIN_USERNAME:
        return True
    return False


async def generate_client(client_name: str):
    process = await asyncio.create_subprocess_shell(f"bash scripts/vpn_gen_client {CONFIG_DIR} {client_name}", stderr=asyncio.subprocess.PIPE)
    code = await process.wait()
    if code != 0:
        _, err = await process.communicate()
        raise Exception(f"<stderr>\n{err.decode()}\ngen_client error code: {code}\n</stderr>\n")


async def on_start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    client_name = user.username if user.username and is_client_exists(user.username) else f"tguid_{user.id}"
    context.user_data["client_name"] = client_name

    if user.username and is_admin(user.username):
        await update.message.reply_text('Привет, я помогу тебе настроить твой VPN сервер.', reply_markup=MARKUP_ADMIN_MENU)
        return START_ADMIN
    elif is_client_exists(client_name):
        await update.message.reply_text(
            "Привет! У тебя уже есть доступ. Скачивай OpenVPN клиент "
            "<a href=\"https://play.google.com/store/apps/details?id=net.openvpn.openvpn\">для Android</a> или "
            "<a href=\"https://apps.apple.com/ru/app/openvpn-connect-openvpn-app/id590379981\">для iOS</a> "
            "и устанавливай конфигурацию.",
            parse_mode='HTML',
            reply_markup=MARKUP_ALLOWED)
        return START_ALLOWED
    else:
        await update.message.reply_text('Привет, извини, но у тебя нет доступа к VPN.')
        return START


async def on_admin(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text

    if text == "Пригласить":
        await update.message.reply_text('Отправь мне имя пользователя или контакт.')
        return INVITE
    elif text == "Выгнать":
        await update.message.reply_text('Отправь мне имя пользователя или контакт.')
        return KICKOUT
    elif text == "Моя конфигурация":
        if not is_client_exists(context.user_data["client_name"]):
            await generate_client(context.user_data["client_name"])
        await update.message.reply_document(
            open(os.path.join(f"{CLIENTS_DIR}", context.user_data["client_name"] + ".ovpn"), "rb"),
            filename="config.ovpn",
            reply_markup=MARKUP_ADMIN_MENU)
    elif text == "Генерировать":
        client_name = f"__tmp__{random_alphanumeric_string(16)}"
        await generate_client(client_name)
        await update.message.reply_document(
            open(os.path.join(f"{CLIENTS_DIR}", client_name + ".ovpn"), "rb"),
            filename="config.ovpn",
            reply_markup=MARKUP_ADMIN_MENU)
        
        os.remove(os.path.join(f"{CLIENTS_DIR}", client_name + ".ovpn"))
    
    return START_ADMIN


async def on_allowed(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text

    if text == "Скачать конфигурацию" and context.user_data["client_name"] :
        await update.message.reply_document(
            open(os.path.join(f"{CLIENTS_DIR}", context.user_data["client_name"] + ".ovpn"), "rb"),
            filename="config.ovpn",
            reply_markup=MARKUP_ALLOWED)

    return START_ALLOWED


async def on_invite(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    username = update.message.text
    contact = update.message.contact

    if not username and not contact:
        await update.message.reply_text('Отправь мне контакт или username!', reply_markup=MARKUP_ADMIN_MENU)
        return INVITE

    if username and len(username) > 0 and username[0] == '@':
        username =  username[1:]

    client_name = f"tguid_{contact.user_id}" if contact else username

    await generate_client(client_name)
    await update.message.reply_text('Сделал!', reply_markup=MARKUP_ADMIN_MENU)

    return START_ADMIN


async def on_kickout(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    username = update.message.text

    await update.message.reply_text('Сделал!', reply_markup=MARKUP_ADMIN_MENU)

    return START_ADMIN


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user

    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

    
def main():
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT, on_start), CommandHandler("start", on_start)],
        states={
            START: [MessageHandler(filters.TEXT, on_start), CommandHandler("start", on_start)],
            START_ADMIN: [MessageHandler(filters.TEXT, on_admin), MessageHandler(filters.CONTACT, on_invite)],
            START_ALLOWED: [MessageHandler(filters.TEXT, on_allowed)],
            INVITE: [MessageHandler(filters.TEXT | filters.CONTACT, on_invite)],
            KICKOUT: [MessageHandler(filters.TEXT, on_kickout)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()