from bot_create import dp, bot
import asyncio
from routers.start_router import router_start
from callbacks.cb_start_work import router_cb_start

dp.include_router(router_start)
dp.include_router(router_cb_start)

async def main():
    await dp.start_polling(bot)

asyncio.run(main())