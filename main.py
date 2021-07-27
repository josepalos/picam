import argparse

import client
import picam
import server
from storage import VALID_FILE_EXTENSIONS


def parse_args():
    parser = argparse.ArgumentParser()
    mode = parser.add_subparsers(dest="mode")
    gui_parser = mode.add_parser("gui")

    server_parser = mode.add_parser("server")
    server_parser.add_argument("--address", default="localhost")
    server_parser.add_argument("--port", default=8000)
    server_parser.add_argument("--storage-path", default="./images")

    client_parser = mode.add_parser("client")
    client_parser.add_argument("--address", default="localhost")
    client_parser.add_argument("--port", default=8000)
    client_parser.add_argument("--extension", default="jpeg",
                               choices=VALID_FILE_EXTENSIONS)

    return parser.parse_args()


def server_mode(args):
    server.main(args.address, args.port, args.storage_path)


def client_mode(args):
    client.main(args.address, args.port, args.extension)


def gui_mode(args):
    picam.main()


_modes = {
    "gui": gui_mode,
    "server": server_mode,
    "client": client_mode,
}


def main():
    args = parse_args()

    func = _modes[args.mode]
    func(args)


if __name__ == "__main__":
    main()
