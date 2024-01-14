from aiogram import Router
from aiogram.filters import Command
from aiogram import types
from keyboards.kb_main import mkp_main

router_start = Router()

@router_start.message(Command('start'))
async def start_message(msg: types.Message):
    await msg.answer('<b>Добро пожаловать в бота рассылку Gmail</b>', parse_mode='html', reply_markup=mkp_main)