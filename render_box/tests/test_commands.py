from render_box.shared.task import TaskManager, TestCommand


def main() -> None:
    tm = TaskManager()
    tm.create_task(TestCommand("hello"))
    tm.create_task(TestCommand("whats"))
    tm.create_task(TestCommand("up"))

    t = TestCommand("test")
    print(t.serialize())

    for task in tm.tasks:
        task.run()


if __name__ == "__main__":
    main()
