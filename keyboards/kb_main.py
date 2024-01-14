from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

mkp_main = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='Начать рассылку', callback_data='call.startwork')
    ]
])