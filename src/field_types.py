import ast
import random
from PyQt4 import QtSql, QtGui, QtCore
from src.globals import Globals, g
from src import edit


class NotFilled(Exception):
    @staticmethod
    def msg_box(_, field_name):
        warn = QtGui.QMessageBox()
        warn.setStyleSheet(g.css)
        warn.setText(_('initField') + '\n  ' + _(field_name))
        warn.setWindowTitle(_('error'))
        warn.exec_()


class FieldType:
    def __init__(self):
        self.widget = None
        self._value = None

    def update(self, value):
        self._value = value

    def submit(self):
        return self._value

    def roll(self):
        pass


class Text(FieldType):
    def __init__(self):
        FieldType.__init__(self)
        self.widget = QtGui.QTextEdit()

    def update(self, value):
        if not isinstance(value, type(None)) and not isinstance(value, QtCore.QPyNullVariant):
            self.widget.setText(str(value))

    def submit(self):
        return self.widget.toPlainText()


class Line(FieldType):
    def __init__(self):
        FieldType.__init__(self)
        self.widget = QtGui.QLineEdit()

    def update(self, value):
        if not isinstance(value, type(None)):
            self.widget.setText(str(value))

    def submit(self):
        return self.widget.text()


class Bool(FieldType):
    def __init__(self):
        FieldType.__init__(self)
        self.widget = QtGui.QCheckBox()

    def update(self, value):
        value = str(value)
        if value == '' or value == '0':
            self.widget.setCheckState(0)
        else:
            self.widget.setCheckState(2)

    def submit(self):
        if self.widget.checkState():
            return 1
        return 0


class Pk(FieldType):
    def __init__(self):
        FieldType.__init__(self)
        self.widget = QtGui.QSpinBox()
        self.widget.setReadOnly(True)

    def update(self, value):
        try:
            self.widget.setValue(float(value))
        except TypeError:
            self.widget.setValue(1.0)

    def submit(self):
        return self.widget.value()


class Integer(FieldType):
    def __init__(self):
        FieldType.__init__(self)
        self.widget = QtGui.QSpinBox()
        self.widget.setRange(-1000000.0, 1000000.0)

    def update(self, value):
        try:
            self.widget.setValue(float(value))
        except TypeError:
            pass

    def submit(self):
        return self.widget.value()


class Real(FieldType):
    def __init__(self):
        FieldType.__init__(self)
        self.widget = QtGui.QDoubleSpinBox()
        self.widget.setRange(-1000000.0, 1000000.0)
        self.widget.setSingleStep(0.1)
        self.widget.setValue(1.0)

    def update(self, value):
        try:
            self.widget.setValue(float(value))
        except TypeError:
            self.widget.setValue(1.0)

    def submit(self):
        return self.widget.value()


class FkMockUp(FieldType):
    def __init__(self, field):
        FieldType.__init__(self)
        self.field = field
        self._ = g.translator
        # catching referenced table
        self.ref = Globals.node(self.field['fk'], g.root)
        # creating the field
        self.widget = QtGui.QComboBox()
        model = QtSql.QSqlQueryModel()
        model.setQuery("SELECT * FROM " + self.ref.attrib['name'])
        for j in range(0, model.rowCount()):
            if model.record(j).value("name"):
                self.widget.addItem(self._(model.record(j).value("name")))
            else:
                self.widget.addItem(self._(str(model.record(j).value("id"))))
        # creating the button
        self.button = QtGui.QPushButton()
        self.button.setText('>>>')
        self.button.clicked.connect(
            lambda: edit.FkDlg(self, self.ref, self.field['name']).launch())

    def update(self, value):
        self.widget.setCurrentIndex(int(value))

    def submit(self):
        if self.widget.currentIndex() == -1:
            raise NotFilled
        else:
            return self.widget.currentIndex()

    def roll(self):
        if 'roll' not in self.field.keys():
            return
        table = self.field['fk']
        model = QtSql.QSqlQueryModel()
        model.setQuery("SELECT * FROM " + table)
        if model.rowCount() == 0:
            error = QtGui.QMessageBox(2, self._('error'), self._(table) + ': ' + self._('tableIsEmpty') + '.')
            error.exec_()
            return
        if self.field['roll'] == 'uniform':
            value = round(random.uniform(0, model.rowCount()), 0)
        elif self.field['roll'] == 'discrete':
            if 'probabilities' not in self.field.keys():
                error = QtGui.QMessageBox(2, self._('error'), self._(self.field['name']) + ': ' +
                                          self._('probabilitiesAttributeNotFound') + '.')
                error.exec_()
                return
            probabilities = list()
            values = list()
            for i in range(0, model.rowCount()):
                probabilities.append(model.record(i).value(self.field['probabilities']))
                values.append(model.record(i).value('id'))
            if round(sum(probabilities), 0) != 1:
                error = QtGui.QMessageBox(2, self._('error'), self._(self.field['probabilities']) + ': ' +
                                          self._('invalidProbabilitiesSum') + '.')
                error.exec_()
                return
            n = random.random()
            index = 0
            while sum(probabilities[:index]) < n and index != len(values):
                index += 1
            value = values[index - 1]
        else:
            value = 0
        self.update(value)


class Color(FieldType):
    def __init__(self):
        FieldType.__init__(self)
        self.widget = QtGui.QPushButton()
        self.widget.setText('')
        self.widget.clicked.connect(self._open_dlg)
        self.color = QtGui.QColorDialog()
        self.color.setStyleSheet(g.css)

    def update(self, value):
        try:
            rgb = ast.literal_eval(value)
            self.widget.setStyleSheet('QPushButton { background: rgb(%i, %i, %i) }' %
                                      (rgb[0], rgb[1], rgb[2]))
            self.color.setCurrentColor(QtGui.QColor(rgb[0], rgb[1], rgb[2]))
        except ValueError:
            self.widget.setStyleSheet('QPushButton { background: rgb(%i, %i, %i) }' %
                                      (255, 255, 255))
            self.color.setCurrentColor(QtGui.QColor(255, 255, 255))

    def _open_dlg(self):
        if self.color.exec_():
            self.update(str(self.color.currentColor().getRgb()[:3]))

    def submit(self):
        return str(self.color.currentColor().getRgb()[:3])


# hash creates connection from fields of one table to fields of another table.
class Hash(FieldType):
    def __init__(self, field):
        FieldType.__init__(self)
        self.field = field
        self._ = g.translator
        # catching referenced table
        table = Globals.node(self.field['hash'], g.root)
        # creating the field
        self.widget = QtGui.QTextEdit()
        self.widget.setReadOnly(True)
        # generating values dict
        self.value = dict()
        if self.field['valueType'] == 'bool':
            value = bool(False)
        else:
            value = str()
        model = QtSql.QSqlQueryModel()
        model.setQuery("SELECT name FROM " + table.attrib['name'])
        for j in range(0, model.rowCount()):
            self.value[model.record(j).value("name")] = value
        # teh button
        self.button = QtGui.QPushButton()
        self.button.setText('>>>')
        self.button.clicked.connect(lambda: edit.HashDlg(self, self.value, self.field['valueType'],
                                                         self.field['name']).launch())

    def update(self, value):
        self.widget.setText(value)
        self.value = ast.literal_eval(value)

    def submit(self):
        return self.widget.toPlainText()


class Choice(FieldType):
    def __init__(self, field):
        FieldType.__init__(self)
        self.widget = QtGui.QComboBox()
        if 'list' in field.keys():
            self.widget.addItems(ast.literal_eval(field['list']))

    def update(self, value):
        index = self.widget.findText(value)
        if index != -1:
            self.widget.setCurrentIndex(index)
        else:
            self.widget.setCurrentIndex(0)

    def submit(self):
        return self.widget.currentText()
