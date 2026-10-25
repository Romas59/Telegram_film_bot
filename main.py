import asyncio
import os
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dotenv import load_dotenv
from commands import router

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Почати роботу"),
        BotCommand(command="help", description="Допомога"),
        BotCommand(command="favourites", description="Улюблені фільми"),
        BotCommand(command="search", description="Знайти фільм в інтернеті"),
        BotCommand(command="about", description="Інформація"),
    ]
    await bot.set_my_commands(commands)


async def main():
    await set_commands(bot)
    print("bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())