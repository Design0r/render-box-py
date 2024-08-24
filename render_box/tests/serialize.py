from render_box.shared.worker import Worker, WorkerState

w = Worker(1, "test", WorkerState.Idle, 199.0, "lskhjg")
print(w.serialize())
