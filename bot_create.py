from aiogram import Dispatcher, Bot
from dotenv import load_dotenv
import os
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()

token = os.getenv('TOKEN')
bot = Bot(token=token)
dp = Dispatcher(storage=MemoryStorage())
