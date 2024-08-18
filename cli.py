from argparse import ArgumentParser, Namespace

from render_box.client.submitter import start_submitter
from render_box.client.worker import start_worker
from render_box.server.server import start_server


def parse_args() -> Namespace:
    parser = ArgumentParser()
    command = parser.add_subparsers(dest="command")
    command.add_parser("server", help="start server")
    submitter = command.add_parser("submitter", help="start server")
    submitter.add_argument("num", type=int, help="number of tasks")
    command.add_parser("worker", help="start worker")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "server":
        start_server()
    elif args.command == "submitter":
        start_submitter(count=args.num)
    elif args.command == "worker":
        start_worker()

    return 0


if __name__ == "__main__":
    main()
