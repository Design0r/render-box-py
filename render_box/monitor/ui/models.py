from abc import abstractmethod
from typing import Iterable, Optional, override

from PySide6 import QtCore, QtGui

from render_box.monitor.controller import Controller
from render_box.shared.serialize import SerializedJob, SerializedTask, SerializedWorker
from render_box.shared.utils import format_timestamp

STATE_COLORS = {
    "waiting": QtGui.QColor("white"),
    "progress": QtGui.QColor("green"),
    "completed": QtGui.QColor(77, 134, 196),
    "idle": QtGui.QColor("white"),
    "working": QtGui.QColor("green"),
    "offline": QtGui.QColor(120, 120, 120),
}


class BaseModel(QtGui.QStandardItemModel):
    column_labels = ("",)

    def __init__(self, controller: Controller, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent=parent)
        self.controller = controller
        self._set_column_headers()
        self.set_column_content()

    def _set_column_headers(self) -> None:
        self.setColumnCount(len(self.column_labels))
        for idx, label in enumerate(self.column_labels):
            self.setHeaderData(idx, QtCore.Qt.Orientation.Horizontal, label)

    def _set_row_color(self, color: QtGui.QColor, row: int) -> None:
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if not item:
                continue
            item.setForeground(color)

    def _add_row(self, row_content: Iterable[str], state: str) -> None:
        row: list[QtGui.QStandardItem] = []
        for col in row_content:
            item = QtGui.QStandardItem(col)
            item.setEditable(False)
            item.setForeground(STATE_COLORS[state])
            row.append(item)

        self.appendRow(row)

    @abstractmethod
    def set_column_content(self): ...

    @abstractmethod
    def refresh(self) -> None: ...


class JobModel(BaseModel):
    column_labels = ("Name", "Priority", "State", "Timestamp", "ID")

    def __init__(self, controller: Controller, parent: Optional[QtCore.QObject] = None):
        super().__init__(controller, parent=parent)

    def get_row_content_from_job(self, job: SerializedJob) -> Iterable[str]:
        return (
            job["name"],
            str(job["priority"]),
            job["state"],
            format_timestamp(job["timestamp"]),
            job["id"],
        )

    @override
    def set_column_content(self):
        jobs = self.controller.get_jobs()
        for job in jobs.values():
            self._add_row(self.get_row_content_from_job(job), job["state"])

    @override
    def refresh(self) -> None:
        jobs = self.controller.get_jobs()
        current_row_count = self.rowCount()

        seen: set[str] = set()
        for row in range(current_row_count):
            job_name = self.item(row, 0).text()
            seen.add(job_name)
            job = jobs.get(job_name)
            if not job:
                self.removeRow(row)
                continue

            status_item = self.item(row, 2)
            job_state = job.get("state", "")
            if status_item.text() != job_state:
                status_item.setText(job_state)
                self._set_row_color(STATE_COLORS[job_state], row)

        for id, job in jobs.items():
            if id in seen:
                continue
            self._add_row(self.get_row_content_from_job(job), job["state"])


class TaskModel(BaseModel):
    column_labels = ("Priority", "State", "Timestamp", "Command", "ID")

    def __init__(self, controller: Controller, parent: Optional[QtCore.QObject] = None):
        self.job_id: Optional[str] = None
        super().__init__(controller, parent=parent)

    def get_row_content_from_task(self, task: SerializedTask) -> Iterable[str]:
        return (
            str(task["priority"]),
            task["state"],
            format_timestamp(task["timestamp"]),
            task["command"]["name"],
            task["id"],
        )

    @override
    def set_column_content(self):
        if not self.job_id:
            return
        tasks = self.controller.get_tasks(self.job_id)
        for task in tasks.values():
            self._add_row(self.get_row_content_from_task(task), task["state"])

    @override
    def refresh(self) -> None:
        if not self.job_id:
            return

        tasks = self.controller.get_tasks(self.job_id)
        current_row_count = self.rowCount()

        seen: set[str] = set()
        for row in range(current_row_count):
            task_item = self.item(row, 4)
            if not task_item:
                continue
            task_name = task_item.text()
            seen.add(task_name)
            task = tasks.get(task_name)
            if not task:
                self.removeRow(row)
                continue

            state_item = self.item(row, 1)
            task_state = task.get("state", "")
            if state_item.text() != task_state:
                state_item.setText(task_state)
                self._set_row_color(STATE_COLORS[task_state], row)

        for id, task in tasks.items():
            if id in seen:
                continue
            self._add_row(self.get_row_content_from_task(task), task["state"])

    def on_job_change(
        self, model: JobModel, selection: QtCore.QItemSelectionModel
    ) -> None:
        selected_row = [
            model.itemFromIndex(index) for index in selection.selectedIndexes()
        ]
        if not selected_row:
            return
        self.job_id = selected_row[-1].text()
        self.clear()
        self._set_column_headers()
        self.set_column_content()


class WorkerModel(BaseModel):
    column_labels = ("ID", "Name", "State", "Timestamp", "Task")

    def __init__(self, controller: Controller, parent: Optional[QtCore.QObject] = None):
        super().__init__(controller, parent=parent)

    def get_row_content_from_worker(self, worker: SerializedWorker) -> Iterable[str]:
        return (
            str(worker["id"]),
            worker["name"],
            worker["state"],
            format_timestamp(worker["timestamp"]),
            worker.get("task_id") or "",
        )

    @override
    def set_column_content(self):
        workers = self.controller.get_workers()
        for worker in workers.values():
            self._add_row(self.get_row_content_from_worker(worker), worker["state"])

    @override
    def refresh(self) -> None:
        workers = self.controller.get_workers()
        current_row_count = self.rowCount()

        seen: set[str] = set()
        for row in range(current_row_count):
            worker_item = self.item(row, 0)
            if not worker_item:
                continue
            worker_id = worker_item.text()
            seen.add(worker_id)
            worker = workers.get(worker_id)
            if not worker:
                self.removeRow(row)
                continue

            status_item = self.item(row, 2)
            task_item = self.item(row, 4)

            if (
                status_item.text() != worker["state"]
                or task_item.text() != worker["task_id"]
            ):
                status_item.setText(worker["state"])
                task_item.setText(str(worker["task_id"]))

                self._set_row_color(STATE_COLORS[worker["state"]], row)

        for id, worker in workers.items():
            if id in seen:
                continue
            self._add_row(self.get_row_content_from_worker(worker), worker["state"])
