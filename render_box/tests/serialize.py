from render_box.shared.worker import WorkerMetadata, WorkerState

w = WorkerMetadata(1, "test", WorkerState.Idle, 199.0, "lskhjg")
print(w.serialize())
