import asyncio
import uvloop
from prompt_toolkit import Application
from main import Couchi


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def run():
    app = Application(full_screen=True)
    app.run()
