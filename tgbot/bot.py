import os
import os.path
import io
import sys
import re
import random
import string
import asyncio

import libvpn

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InputMediaAudio
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, CallbackContext, ContextTypes


TOKEN = os.getenv("TGBOT_TOKEN")
DEBUG = os.getenv("TGBOT_DEBUG", False)

ADMIN_USERNAME = os.getenv("TGBOT_ADMIN_USERNAME")
CERTS_DIR = os.getenv("SERVER_PKI_CERTS_DIR")

START, START_ADMIN, START_ALLOWED, START_DENIED, INVITE, REVOKE = range(6)

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

def is_admin(username: str):
    if username == ADMIN_USERNAME:
        return True
    return False


async def on_start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user        
    
    client_name = f"tguname_{user.username}" if user.username and libvpn.is_client_exists(f"tguname_{user.username}") else f"tguid_{user.id}"
    context.user_data["client_name"] = client_name

    if user.username and is_admin(user.username):
        await update.message.reply_text('Привет, я помогу тебе настроить твой VPN сервер.', reply_markup=MARKUP_ADMIN_MENU)
        return START_ADMIN
    elif libvpn.is_client_exists(client_name):
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
        return REVOKE
    elif text == "Моя конфигурация":
        if not libvpn.is_client_exists(context.user_data["client_name"]):
            await libvpn.create_client(context.user_data["client_name"])
        await update.message.reply_document(
            io.BytesIO(await libvpn.generate_client_config(context.user_data["client_name"])),
            filename="config.ovpn",
            reply_markup=MARKUP_ADMIN_MENU)
    elif text == "Генерировать":
        client_name = f"__tmp__{random_alphanumeric_string(16)}"
        await libvpn.create_client(client_name)
        await update.message.reply_document(
            io.BytesIO(await libvpn.generate_client_config(client_name)),
            filename="config.ovpn",
            reply_markup=MARKUP_ADMIN_MENU)
    
    return START_ADMIN


async def on_allowed(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    text = update.message.text

    if text == "Скачать конфигурацию" and context.user_data["client_name"] :
        await update.message.reply_document(
            io.BytesIO(await libvpn.generate_client_config(context.user_data["client_name"])),
            filename="config.ovpn",
            reply_markup=MARKUP_ALLOWED)

    return START_ALLOWED


async def on_invite(update: Update, context: CallbackContext) -> int:
    username = update.message.text
    contact = update.message.contact

    if not username and not contact:
        await update.message.reply_text('Отправь мне контакт или username!', reply_markup=MARKUP_ADMIN_MENU)
        return INVITE

    if username and len(username) > 0 and username[0] == '@':
        username =  username[1:]

    client_name = f"tguid_{contact.user_id}" if contact else f"tguname_{username}"

    await libvpn.create_client(client_name)
    await update.message.reply_text('Сделал!', reply_markup=MARKUP_ADMIN_MENU)

    return START_ADMIN


async def on_revoke(update: Update, context: CallbackContext) -> int:
    username = update.message.text
    contact = update.message.contact

    if not username and not contact:
        await update.message.reply_text('Отправь мне контакт или username!', reply_markup=MARKUP_ADMIN_MENU)
        return INVITE

    if username and len(username) > 0 and username[0] == '@':
        username =  username[1:]
    
    if contact and libvpn.is_client_exists(f"tguid_{contact.user_id}"):
        await libvpn.revoke_client(f"tguid_{contact.user_id}")
    elif username and libvpn.is_client_exists(f"tguname_{username}"):
        await libvpn.revoke_client(f"tguname_{username}")
    else:
        await update.message.reply_text('Клиет не найден либо изгнан!', reply_markup=MARKUP_ADMIN_MENU)
        return START_ADMIN
    
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
            REVOKE: [MessageHandler(filters.TEXT | filters.CONTACT, on_revoke)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()