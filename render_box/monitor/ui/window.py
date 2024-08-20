from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from render_box.monitor.controller import Controller


class TaskModel(QtGui.QStandardItemModel):
    column_labels = ("ID", "Command")
    ID_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
    COMMAND_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2

    def __init__(self, controller: Controller, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent=parent)
        self.controller = controller
        self._set_column_headers()
        self.set_column_content()

    def _set_column_headers(self) -> None:
        self.setColumnCount(len(self.column_labels))
        for idx, label in enumerate(self.column_labels):
            self.setHeaderData(idx, QtCore.Qt.Orientation.Horizontal, label)

    def set_column_content(self):
        tasks = self.controller.get_tasks()
        for task in tasks.values():
            id_item = QtGui.QStandardItem(str(task["id"]))
            id_item.setEditable(False)
            name_item = QtGui.QStandardItem(task["command"]["name"])
            name_item.setEditable(False)
            self.appendRow([id_item, name_item])

    def refresh(self) -> None:
        tasks = self.controller.get_tasks()
        current_row_count = self.rowCount()

        seen: set[str] = set()
        for row in range(current_row_count):
            task_id = self.item(row, 0).text()
            seen.add(task_id)
            # task_name = self.item(row, 1).data(self.COMMAND_ROLE)
            task = tasks.get(task_id)
            if not task:
                self.removeRow(row)

        for id, task in tasks.items():
            if id in seen:
                continue
            id_item = QtGui.QStandardItem(id)
            name_item = QtGui.QStandardItem(task["command"]["name"])
            self.appendRow([id_item, name_item])


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
    column_labels = ("Name", "Timestamp")
    ID_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
    NAME_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2

    def __init__(self, controller: Controller, parent: Optional[QtCore.QObject] = None):
        super().__init__(parent=parent)
        self.controller = controller
        self._set_column_headers()
        self.set_column_content()

    def _set_column_headers(self) -> None:
        self.setColumnCount(len(self.column_labels))
        for idx, label in enumerate(self.column_labels):
            self.setHeaderData(idx, QtCore.Qt.Orientation.Horizontal, label)

    def set_column_content(self):
        workers = self.controller.get_workers()
        for worker in workers.values():
            name_item = QtGui.QStandardItem(worker.name)
            name_item.setEditable(False)
            time_item = QtGui.QStandardItem(str(worker.timestamp))
            time_item.setEditable(False)
            self.appendRow([name_item, time_item])

    def refresh(self) -> None:
        pass
        # workers = self.controller.get_worker()
        # current_row_count = self.rowCount()
        #
        # seen: set[str] = set()
        # for row in range(current_row_count - 1):
        #     task_id = self.item(row, 0).text()
        #     seen.add(task_id)
        #     # task_name = self.item(row, 1).data(self.COMMAND_ROLE)
        #     task = workers.get(task_id)
        #     if not task:
        #         self.removeRow(row)
        #
        # for id, task in workers.items():
        #     if id in seen:
        #         continue
        #     id_item = QtGui.QStandardItem(id)
        #     name_item = QtGui.QStandardItem(task["command"]["name"])
        #     self.appendRow([id_item, name_item])


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
        self.timer.start(2000)
