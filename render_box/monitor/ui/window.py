from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from render_box.monitor.controller import Controller
from render_box.monitor.ui.models import JobModel, TaskModel, WorkerModel

STATE_COLORS = {
    "waiting": QtGui.QColor("white"),
    "progress": QtGui.QColor("green"),
    "completed": QtGui.QColor(77, 134, 196),
    "idle": QtGui.QColor("white"),
    "working": QtGui.QColor("green"),
    "offline": QtGui.QColor(120, 120, 120),
}
BG_COLORS = {"dark": QtGui.QColor(20, 20, 20), "light": QtGui.QColor(40, 40, 40)}


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


class TableView(QtWidgets.QTableView):
    def __init__(self):
        super().__init__()
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Interactive
        )
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)


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
        self.tasks = TableView()
        self.task_model = TaskModel(self.controller)
        self.tasks.setModel(self.task_model)
        self.task_widget = LabeledTable("Tasks", self.tasks)

        self.worker = TableView()
        self.worker_model = WorkerModel(self.controller)
        self.worker.setModel(self.worker_model)
        self.worker_widget = LabeledTable("Worker", self.worker)

        self.jobs = TableView()
        self.job_model = JobModel(self.controller)
        self.jobs.setModel(self.job_model)
        self.job_widget = LabeledTable("Jobs", self.jobs)

        self.v_split = QtWidgets.QSplitter()
        self.v_split.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.v_split.addWidget(self.job_widget)
        self.v_split.addWidget(self.worker_widget)

        self.h_split = QtWidgets.QSplitter()
        self.h_split.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.h_split.addWidget(self.v_split)
        self.h_split.addWidget(self.task_widget)

    def _init_layouts(self) -> None:
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.h_split)

    def _init_signals(self) -> None:
        selection_model = self.jobs.selectionModel()
        selection_model.selectionChanged.connect(
            lambda: self.task_model.on_job_change(self.job_model, selection_model)
        )
        first_row = self.job_model.index(0, 0)
        selection_model.select(
            first_row,
            QtCore.QItemSelectionModel.SelectionFlag.Select
            | QtCore.QItemSelectionModel.SelectionFlag.Rows,
        )
        self.jobs.setCurrentIndex(first_row)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.task_model.refresh)
        self.timer.timeout.connect(self.worker_model.refresh)
        self.timer.timeout.connect(self.job_model.refresh)
        self.timer.start(2000)
