from typing import Any, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from render_box.monitor.controller import Controller
from render_box.shared.commands import SerializedCommand
from render_box.shared.task import SerializedTask


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
            name_item = QtGui.QStandardItem(task["command"]["name"])
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


class TaskWidget(QtWidgets.QTableView):
    def __init__(self):
        super().__init__()


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
        model = TaskModel(self.controller)
        self.tasks.setModel(model)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(model.refresh)
        self.timer.start(2000)

    def _init_layouts(self) -> None:
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.tasks)
        self.main_layout.addWidget(QtWidgets.QPushButton("Hello"))

    def _init_signals(self) -> None:
        pass
