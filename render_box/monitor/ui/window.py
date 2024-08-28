from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from render_box.monitor.controller import Controller
from render_box.monitor.ui.models import BaseModel, JobModel, TaskModel, WorkerModel
from render_box.shared.event import EventSystem


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
    selection_changed = QtCore.Signal()

    def __init__(self, model: BaseModel):
        super().__init__()
        self.table_model = model
        self.setModel(self.table_model)

        self._init_styling()
        self._init_signals()

    def _init_styling(self) -> None:
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

    def _init_signals(self) -> None:
        self.selectionModel().selectionChanged.connect(
            lambda: self.selection_changed.emit()
        )

    def selected_item(self) -> list[QtGui.QStandardItem]:
        selection = self.selectionModel().selectedIndexes()
        model = self.model()
        return [model.itemFromIndex(index) for index in selection]


class Window(QtWidgets.QWidget):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent=parent)
        self.setWindowTitle("RenderBox Monitor")
        self.setWindowFlag(QtCore.Qt.WindowType.Window)
        self.resize(QtCore.QSize(1500, 750))

        self.controller = Controller()

        self._register_events()
        self._init_widgets()
        self._init_layouts()
        self._init_signals()
        self.select_first_row()

    def _register_events(self) -> None:
        EventSystem.register_event("tables.jobs.selection.changed")

    def _init_widgets(self) -> None:
        self.task_model = TaskModel(self.controller)
        self.task_view = TableView(self.task_model)
        self.task_widget = LabeledTable("Tasks", self.task_view)

        self.worker_model = WorkerModel(self.controller)
        self.worker_view = TableView(self.worker_model)
        self.worker_widget = LabeledTable("Worker", self.worker_view)

        self.job_model = JobModel(self.controller)
        self.job_view = TableView(self.job_model)
        self.job_widget = LabeledTable("Jobs", self.job_view)

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
        self.job_view.selection_changed.connect(self.emit_job_changed)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(lambda: EventSystem.emit("models.*.refresh"))
        self.timer.start(2000)

    def emit_job_changed(self) -> None:
        EventSystem.emit("tables.jobs.selection.changed", self.job_view.selected_item())

    def select_first_row(self):
        selection_model = self.job_view.selectionModel()
        first_row = self.job_model.index(0, 0)
        selection_model.select(
            first_row,
            QtCore.QItemSelectionModel.SelectionFlag.Select
            | QtCore.QItemSelectionModel.SelectionFlag.Rows,
        )
        self.job_view.setCurrentIndex(first_row)
