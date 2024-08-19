from render_box.shared.task import TaskManager

from ..shared.commands import TestCommand


def main() -> None:
    tm = TaskManager()
    tm.create_task(TestCommand(duration=1))
    tm.create_task(TestCommand(duration=2))
    tm.create_task(TestCommand(duration=3))

    t = TestCommand(duration=4)
    print(t.serialize())

    for task in tm.tasks:
        task.run()


if __name__ == "__main__":
    main()
