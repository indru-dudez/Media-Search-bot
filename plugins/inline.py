from urllib.parse import quote
from pyrogram import Client, filters, emoji
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedDocument, InlineQuery
from utils import get_search_results
from info import MAX_RESULTS, CACHE_TIME, SHARE_BUTTON_TEXT
from info import AUTH_CHANEL

@Client.on_inline_query()
async def answer(_, i_query: InlineQuery):
    """Show search results for given inline query"""
    try:
        await _.get_chat_member(
          chat_id=AUTH_CHANEL,
          user_id=i_query.from_user.id
        )
    except pyrogram.errors.exceptions.bad_request_400.UserNotParticipant:
        await i_query.answer(
            results = [],
            cache_time=CACHE_TIME,
            switch_pm_text="You must Join my Group to use me",
            switch_pm_parameter="okay"
        )
        return
    results = []
    if '|' in i_query.query:
        string, file_type = i_query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = i_query.query.strip()
        file_type = None
    
    offset = int(i_query.offset or 0)
    reply_markup = get_reply_markup(_.username)
    files, next_offset = await get_search_results(string,
                                                  file_type=file_type,
                                                  max_results=MAX_RESULTS,
                                                  offset=offset)

    for file in files:
        results.append(
            InlineQueryResultCachedDocument(
                title=file.file_name,
                file_id=file.file_id,
                caption=file.caption or "",
                description=f'Size: {get_size(file.file_size)}\nType: {file.file_type}',
                reply_markup=reply_markup))

    if results:
        count = len(results)
        switch_pm_text = f"{emoji.FILE_FOLDER} {count} Result{'s' if count > 1 else ''}"
        if string:
            switch_pm_text += f" for {string}"

        await i_query.answer(results=results,
                           cache_time=CACHE_TIME,
                           switch_pm_text=switch_pm_text,
                           switch_pm_parameter="start",
                           next_offset=str(next_offset))
    else:

        switch_pm_text = f'{emoji.CROSS_MARK} No results'
        if string:
            switch_pm_text += f' for "{string}"'

        await i_query.answer(results=[],
                           cache_time=CACHE_TIME,
                           switch_pm_text=switch_pm_text,
                           switch_pm_parameter="okay")


def get_reply_markup(username):
    buttons = [[
        InlineKeyboardButton('Search again', switch_inline_query_current_chat=''),
        InlineKeyboardButton(
            text='Share bot',
            url='t.me/share/url?url='+ quote(SHARE_BUTTON_TEXT.format(username=username))),
    ]]
    return InlineKeyboardMarkup(buttons)


def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])
