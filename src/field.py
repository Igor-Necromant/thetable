import parser
from PyQt4 import QtSql, QtGui, QtCore
from src.field_types import NotFilled, Text, Line, Bool, FkMockUp, Hash, Choice, Color, Integer, Pk, Real
from src.globals import Globals, g


class Field:
    # TODO change all error message boxes to raising custom exception.
    def __init__(self, table_index, col_id, row_id):
        self.table = g.root[table_index].attrib
        self.field = g.root[table_index][col_id].attrib
        self.row_id = row_id
        self._ = g.translator
        # init current value
        model = QtSql.QSqlQueryModel()
        model.setQuery("SELECT " + self.field['name'] +
                       " FROM " + self.table['name'] + " WHERE id=" + str(row_id))
        if model.rowCount() == 0:
            # has to add new
            if self.field['name'] == 'id':
                self.value = row_id
                self.new = True
            else:
                self.value = None
        else:
            self.value = model.record(0).value(0)
            self.new = False
        # init label
        self.label = QtGui.QLabel()
        self.label.setText(self._(self.field['name']))
        # init field widget & (if needed) button
        self.widget = None
        self.button = None
        field_type = {'pk': Pk, 'text': Text, 'line': Line, 'int': Integer, 'bool': Bool, 'real': Real, 'fk': FkMockUp,
                      'color': Color, 'hash': Hash, 'choice': Choice}
        if self.field['type'] in field_type.keys():
            # generating input field depending on type
            if self.field['type'] == 'fk' or self.field['type'] == 'hash' or self.field['type'] == 'choice':
                self.widgetClass = field_type[self.field['type']](self.field)
            else:
                self.widgetClass = field_type[self.field['type']]()

            if not isinstance(self.value, type(None)):
                self.widgetClass.update(self.value)
            self.widget = self.widgetClass.widget
            try:
                self.button = self.widgetClass.button
            except AttributeError:
                self.button = None
        else:
            print('[edit.py][class Field][def __init__] Key not found: ' + self.field['type'])
        # generating roll button
        self.roll = None
        if 'roll' in self.field.keys():
            self.roll = QtGui.QPushButton()
            self.roll.setText(self._('roll'))
            self.roll.clicked.connect(self.widgetClass.roll)

    def update_widget(self):
        self.widget = self.widgetClass.widget
        self.button = self.widgetClass.widget

    def update(self, value):
        self.value = value
        self.widgetClass.update(value)

    def submit(self, to_submit):
        try:
            value = self.widgetClass.submit()
        except AttributeError:
            return True
        except NotFilled:
            NotFilled.msg_box(self._, self.field['name'])
            return False
        if self.table['name'] not in to_submit.keys():
            to_submit[self.table['name']] = dict()
        if str(self.row_id) not in to_submit[self.table['name']].keys():
            to_submit[self.table['name']][str(self.row_id)] = dict()
        if self.field['type'] == 'real':
            value = round(value, 2)
        if self.field['type'] == 'pk':
            # shows if query should be INSERT or UPDATE
            to_submit[self.table['name']][str(self.row_id)][self.field['name']] = self.new
        else:
            to_submit[self.table['name']][str(self.row_id)][self.field['name']] = value
        return True


class Fk(FkMockUp):

    def __init__(self, field,):
        FkMockUp.__init__(self, field)

    def create(self, name, mode):
        model = QtSql.QSqlQueryModel()
        model.setQuery("SELECT * FROM " + self.field['fk'])
        self._value = model.rowCount()
        for index in range(0, len(g.root)):
            if g.root[index].attrib['name'] == self.field['fk']:
                self.widget = DaBox(index, self._value, mode, name, True)
                break
        self.button = None

    def submit(self):
        return self._value

    def update(self, value):
        pass


class GenField(Field):
    def __init__(self, table_index, col_id, row_id, mode, name):
        # normal widget
        Field.__init__(self, table_index, col_id, row_id)
        self.lock = QtGui.QCheckBox(self._('lock'))
        # special widget with recursive box call - made special for fk
        if mode != 'source' and isinstance(self.widgetClass, FkMockUp):
            if mode == 'mixedsource':
                mode = 'source'
            if mode == 'result':
                mode = 'fk'
            if mode == 'mixedresult':
                mode = 'result'
            self.widgetClass = Fk(self.field)
            self.widgetClass.create(name, mode)
            self.update_widget()
            self.lock = None
            self.label = None


class DaBox(QtGui.QGroupBox):
    def __init__(self, table_index, row, mode, name, show_id):
        # initializing stuff
        self.table = g.root[table_index]
        self._ = g.translator
        # naming stuff
        if mode == 'source':
            title = self._('sourceBox') + ' '
        elif mode == 'result':
            title = self._('resultBox') + ' '
        elif mode == 'fk':
            title = self._('fkBox') + ' '
        else:
            print('Bad mode param')
            return
        title += self._(name)
        # calling the papa code
        QtGui.QGroupBox.__init__(self, title)
        self.setCheckable(True)
        self.toggled.connect(
            lambda: self.setMaximumHeight(5000)
            if self.maximumHeight() == 35
            else self.setMaximumHeight(35)
        )
        # filling up the box
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        # list of fields to be generated in the future
        self.fields_tree = dict()
        self.fields = list()
        self.generate_name = name
        # going through each column
        for col_id in range(0, len(self.table)):
            col = self.table[col_id]
            if col.tag == 'field':
                # id gets printed only if show_id is True
                if col.attrib['name'] == 'id':
                    if show_id:
                        field = Field(table_index, col_id, row)
                        self.layout.addWidget(field.label, col_id, 0, 1, 2)
                        self.layout.addWidget(field.widget, col_id, 2, 1, 2)
                        if isinstance(field.widget, DaBox):
                            self.fields_tree[col.attrib['name']] = field.widget.fields_tree
                        else:
                            self.fields_tree[col.attrib['name']] = field
                        self.fields.append(field)
                # fk mode doesn't require generate_name attribute in xml to describe wot do
                elif mode == 'fk':
                    field = GenField(table_index, col_id, row, 'result', self.generate_name + '.' + col.attrib['name'])
                    self.add(field, col_id, col.attrib['name'])
                # here it comes - parsing directions from xml
                elif self.generate_name in col.attrib.keys():
                    # in 'result' or 'source' case its all simple
                    if col.attrib[self.generate_name] == mode:
                        field = GenField(table_index, col_id, row, mode,
                                         self.generate_name + '.' + col.attrib['name'])
                        self.add(field, col_id, col.attrib['name'])
                    # in 'mixed' case each result/source add only related to itself fields
                    elif col.attrib[self.generate_name] == 'mixed':
                        field = GenField(table_index, col_id, row, col.attrib[self.generate_name] + mode,
                                         self.generate_name + '.' + col.attrib['name'])
                        self.add(field, col_id, col.attrib['name'])
                    elif mode == 'result' and col.attrib[self.generate_name] != 'source':
                        field = GenField(table_index, col_id, row, 'result',
                                         self.generate_name + '.' + col.attrib['name'])
                        self.add(field, col_id, col.attrib['name'])
                else:
                    print('Bad xml')
        generate_to_submit.append(self.fields)

    def add(self, field, col_id, name):
        if not isinstance(field.lock, type(None)):
            self.layout.addWidget(field.lock, col_id, 0)
        if not isinstance(field.label, type(None)):
            self.layout.addWidget(field.label, col_id, 1)
        if isinstance(field.widget, DaBox):
            self.fields_tree[name] = field.widget.fields_tree
            self.layout.addWidget(field.widget, col_id, 0, 1, 4)
        else:
            self.fields_tree[name] = field
            if not isinstance(field.button, type(None)):
                self.layout.addWidget(field.widget, col_id, 2)
                self.layout.addWidget(field.button, col_id, 3)
            else:
                self.layout.addWidget(field.widget, col_id, 2, 1, 2)
        self.fields.append(field)


class GenerateForm(QtGui.QDialog):
    def __init__(self, table_index, row):
        QtGui.QDialog.__init__(self)
        self.setStyleSheet(g.css)
        self.table = g.root[table_index]
        self._ = g.translator
        self.to_generate = dict()
        global generate_to_submit
        generate_to_submit = list()

        # layout
        layout = QtGui.QVBoxLayout()

        frame = QtGui.QFrame()
        boxes_layout = QtGui.QHBoxLayout()

        # order is important for submit!
        # make right side (result)
        self.right_box = DaBox(table_index, row, 'result', g.root[table_index].attrib['generate'], False)
        right_scroll = QtGui.QScrollArea()
        right_scroll.setWidget(self.right_box)
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        right_scroll.setMinimumSize(self.right_box.minimumSizeHint())
        self.right_box.setCheckable(False)

        # make left side (source)
        self.left_box = DaBox(table_index, row, 'source', g.root[table_index].attrib['generate'], True)
        left_scroll = QtGui.QScrollArea()
        left_scroll.setWidget(self.left_box)
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        left_scroll.setMinimumSize(self.left_box.minimumSizeHint())
        self.left_box.setCheckable(False)

        # adding stuff
        boxes_layout.addWidget(left_scroll)
        boxes_layout.addWidget(right_scroll)
        frame.setLayout(boxes_layout)
        layout.addWidget(frame)

        # control buttons
        # apply
        btn_apply = QtGui.QPushButton()
        btn_apply.setText(self._('apply'))
        btn_apply.clicked.connect(self.apply)
        layout.addWidget(btn_apply)

        # generate
        btn_generate = QtGui.QPushButton()
        btn_generate.setText(self._('generate'))
        btn_generate.clicked.connect(self.generate)
        layout.addWidget(btn_generate)

        # cancel
        btn_cancel = QtGui.QPushButton()
        btn_cancel.setText(self._('cancel'))
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

        self.setLayout(layout)
        self.setWindowTitle(self._('generateEntryFor:') + ' ' + self._(self.table.attrib['name']))

    def sql_recursion(self, table, value):
        model = QtSql.QSqlQueryModel()
        model.setQuery("SELECT * FROM " + table.attrib['name'] + " WHERE id=" + str(value))
        if model.rowCount() == 0:
            raise NotFilled
        else:
            result = dict()
            for node in table:
                if node.tag == 'field':
                    if node.attrib['type'] == 'fk':
                        result[node.attrib['name']] = self.sql_recursion(Globals.node(node.attrib['fk'], g.root),
                                                                         model.record(0).value(node.attrib['name']))
                    else:
                        result[node.attrib['name']] = model.record(0).value(node.attrib['name'])
                    if isinstance(result[node.attrib['name']], QtCore.QPyNullVariant):
                        result[node.attrib['name']] = None
        return result

    def source_recursion(self, table, gen_name, fields):
        result = dict()
        for node in table:
            if node.tag == 'field':
                # only working with ids, mixed fks and source fields
                if node.attrib['name'] == 'id':
                    result[node.attrib['name']] = fields[node.attrib['name']].widgetClass.submit()
                elif node.attrib[gen_name] == 'mixed':
                    # going recursion
                    result[node.attrib['name']] = self.source_recursion(Globals.node(node.attrib['fk'], g.root),
                                                                        gen_name + '.' + node.attrib['name'],
                                                                        fields[node.attrib['name']])
                elif node.attrib[gen_name] == 'source':
                    # if not locked, we SPIN THE WHEEL
                    if isinstance(fields[node.attrib['name']].lock, QtGui.QCheckBox):
                        if not fields[node.attrib['name']].lock.isChecked():
                            fields[node.attrib['name']].widgetClass.roll()
                    # fk, need to do sql recursion
                    if node.attrib['type'] == 'fk':
                        try:
                            value = fields[node.attrib['name']].widgetClass.submit()
                        except NotFilled:
                            value = 0
                        try:
                            result[node.attrib['name']] = self.sql_recursion(Globals.node(node.attrib['fk'], g.root), value)
                        except NotFilled:
                            result[node.attrib['name']] = 'fucking shit'
                    # otherwise just get valued from submit
                    else:
                        result[node.attrib['name']] = fields[node.attrib['name']].widgetClass.submit()
        return result

    def result_recursion(self, table, gen_name, fields):
        generate = self.to_generate
        for node in table:
            if node == 'field':
                # working with result-like fields only
                if node.attrib['name'] == 'id':
                    pass
                elif node.attrib['type'] == 'fk' and node.attrib[gen_name] != 'source':
                    self.result_recursion(Globals.node(node.attrib['fk'], g.root),
                                          gen_name + '.' + node.attrib['name'],
                                          fields[node.attrib['name']])
                elif node.attrib[gen_name] != 'source':
                    if isinstance(fields[node.attrib['name']].lock, QtGui.QCheckBox):
                        if not fields[node.attrib['name']].lock.isChecked():
                            try:
                                value = eval(parser.expr(node.attrib[gen_name]).compile())
                                fields[node.attrib['name']].update(value)
                            except NameError:
                                print('its fine')

    def apply(self):
        to_submit = list()
        splitter = int()  # shows what part of to_submit is result and what is source
        once = True
        for index in range(0, len(generate_to_submit)):
            to_submit.append(dict())
            for field in generate_to_submit[index]:
                field.submit(to_submit[index])
                if self.table.attrib['name'] in to_submit[index] and once:
                    splitter = index
                    once = False
        for result_index in range(0, splitter + 1):
            for source_index in range(splitter + 1, len(to_submit)):
                if to_submit[result_index].keys() == to_submit[source_index].keys():
                    for table_key in to_submit[result_index]:
                        for id_key in to_submit[result_index][table_key]:
                            to_submit[result_index][table_key][id_key].update(
                                to_submit[source_index][table_key][id_key])
        to_submit = to_submit[:splitter + 1]
        for submit in to_submit:
            Globals.master_submit(submit)
        self.accept()

    def generate(self):
        # initialize all source fields. If lock==True, just submit(), else roll. If fk, go recursion with sql
        self.to_generate = self.source_recursion(self.table, self.table.attrib['generate'], self.left_box.fields_tree)
        # generate result based on formulas given, using ast parser
        self.result_recursion(self.table, self.table.attrib['generate'], self.right_box.fields_tree)
