import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handler import router

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    logging.info("Инициализация бота...")

    try:
        logging.info("Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

