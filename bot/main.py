import asyncio
from bot import build_app
from loguru import logger

async def main():
    app = build_app()
    logger.info("Bot starting ...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())