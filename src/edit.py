from PyQt4 import QtCore, QtGui, QtSql
from src.globals import Globals, g
from src.field import Field
from src.field_types import Line, Bool


class FkDlg(QtGui.QDialog):
    # TODO build joins
    # TODO add to FK'ed table
    def __init__(self, caller, ref, name):
        QtGui.QDialog.__init__(self)
        self.setStyleSheet(g.css)
        self.caller = caller
        self._ = g.translator
        self.ref = ref
        self.result = int()

        layout = QtGui.QVBoxLayout()

        # model
        columns = '*'
        join = ''
        for view in self.ref.findall('view'):
            if view.get('name') == 'default':
                columns, join = Globals.build_join(self.ref, view)
        model = QtSql.QSqlQueryModel()
        model.setQuery("SELECT " + columns + " FROM " + ref.attrib['name'] + join)
        # setting headers
        for j in range(0, model.columnCount()):
            header = model.headerData(j, QtCore.Qt.Horizontal)
            model.setHeaderData(j, QtCore.Qt.Horizontal, self._(header))
        # view
        self.table = QtGui.QTableView()
        self.table.setModel(model)
        self.table.setSelectionBehavior(1)
        self.table.doubleClicked.connect(self.submit)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setStyleSheet(g.css)
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        layout.addWidget(self.table)

        # cancel
        cancel = QtGui.QPushButton()
        cancel.setText(self._('cancel'))
        cancel.clicked.connect(lambda: self.reject())
        layout.addWidget(cancel)

        # layout
        self.setLayout(layout)
        self.setWindowTitle(self._('fkEdit:') + ' ' + self._(name))
        self.adjustSize()

    def launch(self):
        if self.exec_():
            self.caller.update(self.result)

    def submit(self, index):
        self.result = index.row()
        self.accept()


class HashDlg(QtGui.QDialog):

    def __init__(self, caller, value, field_type, name):
        QtGui.QDialog.__init__(self)
        self.setStyleSheet(g.css)
        self.caller = caller
        self._ = g.translator
        self.data = value
        self.fields = list()

        layout = QtGui.QVBoxLayout()
        # table
        self.table = QtGui.QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([self._('key'), self._('value')])
        # init
        for key in self.data.keys():
            self.table.insertRow(self.table.rowCount())
            self.table.setItem(self.table.rowCount() - 1, 0, QtGui.QTableWidgetItem(key))
            if field_type == 'bool':
                field = Bool()
                field.update(self.data[key])
                self.fields.append(field)
                self.table.setCellWidget(self.table.rowCount() - 1, 1, field.widget)
            else:
                field = Line()
                field.update(self.data[key])
                self.fields.append(field)
                self.table.setCellWidget(self.table.rowCount() - 1, 1, field.widget)

        self.table.verticalHeader().hide()
        self.table.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.table.horizontalHeader().setStyleSheet(g.css)
        self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)

        layout.addWidget(self.table)

        # submit
        submit = QtGui.QPushButton()
        submit.setText(self._('submit'))
        submit.clicked.connect(self.submit)
        layout.addWidget(submit)

        # cancel
        cancel = QtGui.QPushButton()
        cancel.setText(self._('cancel'))
        cancel.clicked.connect(lambda: self.reject())
        layout.addWidget(cancel)

        # layout
        self.setLayout(layout)
        self.setWindowTitle(self._('hashEdit:') + ' ' + self._(name))

    def submit(self):
        self.data.clear()
        for i in range(0, self.table.rowCount()):
            try:
                self.data[self.table.item(i, 0).text()] = str(self.fields[i].submit())
            except AttributeError:
                continue
        self.accept()

    def launch(self):
        if self.exec_():
            self.caller.update(str(self.data))


class EntryForm(QtGui.QDialog):

    def __init__(self, table_index, row_id):
        QtGui.QDialog.__init__(self)
        self.setStyleSheet(g.css)
        self._ = g.translator
        self.table = g.root[table_index]
        self.fields = list()
        # layout
        layout = QtGui.QGridLayout()
        # putting field widgets
        for node, j in zip(self.table, range(0, len(self.table))):
            if node.tag == 'field':
                field = Field(table_index, j, row_id)
                layout.addWidget(field.label, j, 0)
                layout.addWidget(field.widget, j, 1)
                if not isinstance(field.button, type(None)):
                    layout.addWidget(field.button, j, 2)
                if not isinstance(field.roll, type(None)):
                    layout.addWidget(field.roll, j, 3)
                self.fields.append(field)

        # adding buttons
        buttons = QtGui.QFrame()
        btn_layout = QtGui.QHBoxLayout()

        # submit button
        btn_submit = QtGui.QPushButton()
        btn_submit.setText(self._('submit'))
        btn_submit.clicked.connect(self.submit)
        btn_layout.addWidget(btn_submit)

        # revert button
        btn_revert = QtGui.QPushButton()
        btn_revert.setText(self._('cancel'))
        btn_revert.clicked.connect(self.reject)
        btn_layout.addWidget(btn_revert)

        buttons.setLayout(btn_layout)
        layout.addWidget(buttons, layout.rowCount(), 1)

        self.setLayout(layout)
        self.setWindowTitle(self._('addEntryTo:') + ' ' + self._(self.table.attrib['name']))

    def submit(self):
        to_submit = dict()
        for field in self.fields:
            if not field.submit(to_submit):
                return
        Globals.master_submit(to_submit)
        self.accept()
