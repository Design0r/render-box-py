from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from render_box.monitor.controller import Controller
from render_box.shared.task import SerializedTask, WorkerMetadata
from render_box.shared.utils import format_timestamp

STATE_COLORS = {
    "waiting": QtGui.QColor("white"),
    "progress": QtGui.QColor("green"),
    "finished": QtGui.QColor(77, 134, 196),
    "idle": QtGui.QColor("white"),
    "working": QtGui.QColor("green"),
    "offline": QtGui.QColor(120, 120, 120),
}
BG_COLORS = {"dark": QtGui.QColor(20, 20, 20), "light": QtGui.QColor(40, 40, 40)}


class TaskModel(QtGui.QStandardItemModel):
    column_labels = ("ID", "Priority", "State", "Tiemstamp", "Command")

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

    def add_row(self, task: SerializedTask) -> None:
        row_idx = self.rowCount()
        bg_col = BG_COLORS["light"] if row_idx % 2 == 0 else BG_COLORS["dark"]
        col_list: tuple[str, ...] = (
            str(task["id"]),
            str(task["priority"]),
            task["state"],
            format_timestamp(task["timestamp"]),
            task["command"]["name"],
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
        tasks = self.controller.get_tasks()
        for task in tasks.values():
            self.add_row(task)

    def refresh(self) -> None:
        tasks = self.controller.get_tasks()
        current_row_count = self.rowCount()

        seen: set[str] = set()
        for row in range(current_row_count):
            task_id = self.item(row, 0).text()
            seen.add(task_id)
            task = tasks.get(task_id)
            if not task:
                self.removeRow(row)
                continue

            status_item = self.item(row, 2)
            task_state = task.get("state", "")
            if status_item.text() != task_state:
                status_item.setText(task_state)
                self.set_row_color(STATE_COLORS[task_state], row)

        for id, task in tasks.items():
            if id in seen:
                continue
            self.add_row(task)
            self.set_row_color(STATE_COLORS[task["state"]], self.rowCount() - 1)


class LabeledTable(QtWidgets.QWidget):
    def __init__(
        self,
        label: str,
        table: QtWidgets.QTableView,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.table = table
        self.label = label
        self._init_widgets()
        self._init_layouts()
        self._init_signals()

    def _init_widgets(self) -> None:
        self.label_widget = QtWidgets.QLabel(self.label)
        self.label_widget.setStyleSheet("font-size: 16pt;")

    def _init_layouts(self) -> None:
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.label_widget)
        self.main_layout.addWidget(self.table)

    def _init_signals(self) -> None:
        pass


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

    def add_row(self, worker: WorkerMetadata) -> None:
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
            worker_id = self.item(row, 0).text()
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


class TaskWidget(QtWidgets.QTableView):
    def __init__(self):
        super().__init__()
        self.verticalHeader().setVisible(False)
        # self.setShowGrid(False)
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )


class Window(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)
        self.setWindowTitle("RenderBox Monitor")
        self.setWindowFlag(QtCore.Qt.WindowType.Window)
        self.resize(QtCore.QSize(1500, 750))

        self.controller = Controller()

        self._init_widgets()
        self._init_layouts()
        self._init_signals()

    def _init_widgets(self) -> None:
        self.tasks = TaskWidget()
        self.task_model = TaskModel(self.controller)
        self.tasks.setModel(self.task_model)
        self.task_widget = LabeledTable("Tasks", self.tasks)

        self.worker = TaskWidget()
        self.worker_model = WorkerModel(self.controller)
        self.worker.setModel(self.worker_model)
        self.worker_widget = LabeledTable("Worker", self.worker)

        self.splitter = QtWidgets.QSplitter()
        self.splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter.addWidget(self.task_widget)
        self.splitter.addWidget(self.worker_widget)

    def _init_layouts(self) -> None:
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.splitter)

    def _init_signals(self) -> None:
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.task_model.refresh)
        self.timer.timeout.connect(self.worker_model.refresh)
        self.timer.start(2000)
