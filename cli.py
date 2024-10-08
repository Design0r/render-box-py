import sys
from argparse import ArgumentParser, Namespace

import render_box.client.submitter as submitter
import render_box.client.worker as worker
import render_box.monitor.ui.window as monitor
import render_box.server.server as server


def parse_args() -> Namespace:
    parser = ArgumentParser()
    command = parser.add_subparsers(dest="command")
    command.add_parser("server", help="start server")
    submit = command.add_parser("submit", help="start server")
    submit.add_argument("num", type=int, help="number of tasks")
    command.add_parser("worker", help="start worker")
    command.add_parser("monitor", help="start monitor")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "server":
        server.start_server()
    elif args.command == "submit":
        submitter.start_submitter(count=args.num)
    elif args.command == "worker":
        worker.start_worker()
    elif args.command == "monitor":
        from PySide6.QtWidgets import QApplication

        app = QApplication(sys.argv)
        app.setStyle("fusion")
        window = monitor.Window()
        window.show()
        sys.exit(app.exec())

    return 0


if __name__ == "__main__":
    main()
