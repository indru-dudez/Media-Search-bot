import os
import logging
import pymongo
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import START_MSG, CHANNELS, ADMINS, AUTH_CHANEL, DATABASE_URI
from utils import Media

logger = logging.getLogger(__name__)

@Client.on_message(filters.command('sendtoall'))
async def sendtoall(bot, message):
    """Start command handler"""
    if message.reply_to_message is None:
       await message.send_message(
            chat_id=message.chat.id,
            text="Reply to text message",
            reply_to_message_id=message.message_id
        )
    subscribers = await bot.get_chat_members(
                      chat_id=AUTH_CHANEL
                  )
    myclient = pymongo.MongoClient(DATABASE_URI)
    mydb = myclient["mydatabase"]
    starters_db = mydb["starters"]
    total_sub = len(starters_db.find())
    sent_sub = 0
    for sent in subscribers:
       await bot.send_message(
            chat_id=message.chat.id,
            text=message.reply_to_message,
            reply_to_message_id=message.message_id
       )
       sent_sub = sent_sub + 1
       await bot.send_message(
            chat_id=message.chat.id,
            text="Message sent to {} Subscribers out of {}".format(sent_sub, total_sub),
            reply_to_message_id=message.message_id
       )
       return

@Client.on_message(filters.command('start'))
async def start(bot, message):
    """Start command handler"""
    myclient = pymongo.MongoClient(DATABASE_URI)
    mydb = myclient["mydatabase"]
    starters_db = mydb["starters"]
    if not message.chat.id in starters_db.find():
         added = starters_db.insert_one(message.chat.id)  
    buttons = [
       [
        InlineKeyboardButton('Join Channel', url='https://t.me/{}'.format(AUTH_CHANEL[1:]))
       ],
       [
        InlineKeyboardButton('Search Here', switch_inline_query_current_chat=''),
        InlineKeyboardButton('Go Inline', switch_inline_query=''),
       ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply(START_MSG, reply_markup=reply_markup)


@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    """Send basic information of channel"""
    
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    for channel in channels:
        channel_info = await bot.get_chat(channel)
        string = str(channel_info)
        if len(string) > 4096:
            filename = (channel_info.title or channel_info.first_name) + ".txt"
            with open(filename, 'w') as f:
                f.write(string)
            await message.reply_document(filename)
            os.remove(filename)
        else:
            await message.reply(str(channel_info))
            

@Client.on_message(filters.command('total') & filters.user(ADMINS))
async def total(bot, message):
    """Show total files in database"""
    msg = await message.reply("Processing...⏳", quote=True)
    try:
        total = await Media.count_documents()
        await msg.edit(f'📁 Saved files: {total}')
    except Exception as e:
        logger.exception('Failed to check total files')
        await msg.edit(f'Error: {e}')


@Client.on_message(filters.command('logger') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))


@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""

    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return

    result = await Media.collection.delete_one({
        'file_name': media.file_name,
        'file_size': media.file_size,
        'mime_type': media.mime_type,
        'caption': reply.caption
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        await msg.edit('File not found in database')
