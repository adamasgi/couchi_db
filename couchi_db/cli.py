import asyncio
import uvloop
import argparse
import sys
from rich.pretty import pprint
from main import Couchi
from prompt_toolkit import Application


asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def add_file(db, doc_id: str, filename: str, attach_id: [str | None] = None):
    if attach_id is None:
        attach_id = filename

    r = await db.attach_file(filename, doc_id, attach_id)
    return r


async def help():
    print("Extra help")


async def main(args: list):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="subcmd", dest="subcmd", help="subcmds")
    add_parser = subparsers.add_parser("add")
    add_file_parser = subparsers.add_parser("add-file")
    add_file_parser.add_argument("filename", type=str, default="./testing.txt")
    add_file_parser.add_argument("id", type=str, default="testing-id")
    subparsers.add_parser("tui")
    subparsers.add_parser("get-all")

    args = parser.parse_args()

    async with Couchi("hello-there") as db:
        await db.get_session_auth()
        if args.subcmd == "add-file":
            r = await add_file(db, args.id, args.filename)
        elif args.subcmd == "add":
            r = await db.add("testing", {"testing": True})
        elif args.subcmd == "get-all":
            r = await db.get_all()
        elif args.subcmd == "tui":
            await tui()
        else:
            await help()
        pprint(r)


def run(args: list = []):
    asyncio.run(main(sys.argv))


if __name__ == "__main__":
    run(sys.argv)
