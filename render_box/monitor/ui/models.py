from typing import Optional

from PySide6 import QtCore, QtGui

from render_box.monitor.controller import Controller
from render_box.shared.serialize import SerializedJob
from render_box.shared.task import SerializedTask, Worker
from render_box.shared.utils import format_timestamp

STATE_COLORS = {
    "waiting": QtGui.QColor("white"),
    "progress": QtGui.QColor("green"),
    "completed": QtGui.QColor(77, 134, 196),
    "idle": QtGui.QColor("white"),
    "working": QtGui.QColor("green"),
    "offline": QtGui.QColor(120, 120, 120),
}
BG_COLORS = {"dark": QtGui.QColor(20, 20, 20), "light": QtGui.QColor(40, 40, 40)}


class JobModel(QtGui.QStandardItemModel):
    column_labels = ("Name", "Priority", "State", "Timestamp", "ID")

    def __init__(self, controller: Controller, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent=parent)
        self.controller = controller
        self._set_column_headers()
        self.set_column_content()

    def _set_column_headers(self) -> None:
        self.setColumnCount(len(self.column_labels))
        for idx, label in enumerate(self.column_labels):
            self.setHeaderData(idx, QtCore.Qt.Orientation.Horizontal, label)

    def set_row_color(self, color: QtGui.QColor, row: int) -> None:
        bg_col = BG_COLORS["light"] if row % 2 == 0 else BG_COLORS["dark"]
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setForeground(color)
                item.setBackground(bg_col)

    def add_row(self, job: SerializedJob) -> None:
        row_idx = self.rowCount()
        bg_col = BG_COLORS["light"] if row_idx % 2 == 0 else BG_COLORS["dark"]
        col_list: tuple[str, ...] = (
            str(job["name"]),
            str(job["priority"]),
            job["state"],
            format_timestamp(job["timestamp"]),
            job["id"],
        )
        row: list[QtGui.QStandardItem] = []
        for col in col_list:
            item = QtGui.QStandardItem(col)
            item.setEditable(False)
            item.setForeground(STATE_COLORS[job["state"]])
            item.setBackground(bg_col)
            row.append(item)

        self.appendRow(row)

    def set_column_content(self):
        jobs = self.controller.get_jobs()
        for job in jobs.values():
            self.add_row(job)

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
            task_state = job.get("state", "")
            if status_item.text() != task_state:
                status_item.setText(task_state)
                self.set_row_color(STATE_COLORS[task_state], row)

        for id, job in jobs.items():
            if id in seen:
                continue
            self.add_row(job)
            self.set_row_color(STATE_COLORS[job["state"]], self.rowCount() - 1)


class TaskModel(QtGui.QStandardItemModel):
    column_labels = ("Priority", "State", "Timestamp", "Command", "ID")

    def __init__(self, controller: Controller, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent=parent)
        self.controller = controller
        self.job_id: Optional[str] = None
        self._set_column_headers()
        self.set_column_content()

    def _set_column_headers(self) -> None:
        self.setColumnCount(len(self.column_labels))
        for idx, label in enumerate(self.column_labels):
            self.setHeaderData(idx, QtCore.Qt.Orientation.Horizontal, label)

    def set_row_color(self, color: QtGui.QColor, row: int) -> None:
        bg_col = BG_COLORS["light"] if row % 2 == 0 else BG_COLORS["dark"]
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setForeground(color)
                item.setBackground(bg_col)

    def add_row(self, task: SerializedTask) -> None:
        row_idx = self.rowCount()
        bg_col = BG_COLORS["light"] if row_idx % 2 == 0 else BG_COLORS["dark"]
        col_list: tuple[str, ...] = (
            str(task["priority"]),
            task["state"],
            format_timestamp(task["timestamp"]),
            task["command"]["name"],
            str(task["id"]),
        )
        row: list[QtGui.QStandardItem] = []
        for col in col_list:
            item = QtGui.QStandardItem(col)
            item.setEditable(False)
            item.setForeground(STATE_COLORS[task["state"]])
            item.setBackground(bg_col)
            row.append(item)

        self.appendRow(row)

    def set_column_content(self):
        if not self.job_id:
            return
        tasks = self.controller.get_tasks(self.job_id)
        for task in tasks.values():
            self.add_row(task)

    def refresh(self) -> None:
        self.clear()
        self._set_column_headers()
        self.set_column_content()
        return

        if not self.job_id:
            return

        tasks = self.controller.get_tasks(self.job_id)
        current_row_count = self.rowCount()

        seen: set[str] = set()
        for row in range(current_row_count):
            task_item = self.item(row, 4)
            if not task_item:
                continue
            task_id = task_item.text()
            seen.add(task_id)
            task = tasks.get(task_id)
            if not task:
                self.removeRow(row)
                continue

            status_item = self.item(row, 1)
            task_state = task.get("state", "")
            if status_item.text() != task_state:
                status_item.setText(task_state)
                self.set_row_color(STATE_COLORS[task_state], row)

        for id, task in tasks.items():
            if id in seen:
                continue
            self.add_row(task)
            self.set_row_color(STATE_COLORS[task["state"]], self.rowCount() - 1)

    def on_job_change(
        self, model: JobModel, selection: QtCore.QItemSelectionModel
    ) -> None:
        selected_row = [
            model.itemFromIndex(index) for index in selection.selectedIndexes()
        ]
        if not selected_row:
            return
        self.job_id = selected_row[-1].text()
        self.refresh()


class WorkerModel(QtGui.QStandardItemModel):
    column_labels = ("ID", "Name", "State", "Timestamp", "Task")

    def __init__(self, controller: Controller, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent=parent)
        self.controller = controller
        self._set_column_headers()
        self.set_column_content()

    def _set_column_headers(self) -> None:
        self.setColumnCount(len(self.column_labels))
        for idx, label in enumerate(self.column_labels):
            self.setHeaderData(idx, QtCore.Qt.Orientation.Horizontal, label)

    def add_row(self, worker: Worker) -> None:
        row_idx = self.rowCount()
        bg_col = BG_COLORS["light"] if row_idx % 2 == 0 else BG_COLORS["dark"]
        columns: tuple[str, ...] = (
            str(worker.id),
            worker.name,
            worker.state,
            format_timestamp(worker.timestamp),
            str(worker.task_id) or "",
        )

        row: list[QtGui.QStandardItem] = []
        for col in columns:
            item = QtGui.QStandardItem(col)
            item.setEditable(False)
            item.setForeground(STATE_COLORS[worker.state])
            item.setBackground(bg_col)
            row.append(item)

        self.appendRow(row)

    def set_column_content(self):
        workers = self.controller.get_workers()
        for worker in workers.values():
            self.add_row(worker)

    def set_row_color(self, color: QtGui.QColor, row: int) -> None:
        bg_col = BG_COLORS["light"] if row % 2 == 0 else BG_COLORS["dark"]
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setForeground(color)
                item.setBackground(bg_col)

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

            if status_item.text() != worker.state or task_item.text() != worker.task_id:
                status_item.setText(worker.state)
                task_item.setText(str(worker.task_id))

                self.set_row_color(STATE_COLORS[worker.state], row)

        for id, worker in workers.items():
            if id in seen:
                continue
            self.add_row(worker)