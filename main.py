import os
import sys
from src import edit
from PyQt4 import QtCore, QtGui, QtSql
from src.globals import Globals, g
from src import db_defaults, field


class DBView(QtGui.QTableView):

    def __init__(self):
        QtGui.QTableView.__init__(self)
        self.dbModel = QtSql.QSqlQueryModel()
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setWordWrap(True)
        self.verticalHeader().hide()
        self.horizontalHeader().setStyleSheet(g.css)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.setMouseTracking(True)
        '''# parsing css file
        temp = Globals.css[Globals.css.find('QTableView::item:hover'):]
        temp = temp[temp.find('{'):]
        temp = temp[:temp.find('}') + 1]
        self.hover_css = 'QTableView::item ' + temp

    # TODO def mouseMoveEvent(self, e):'''


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setStyleSheet(g.css)
        _ = g.translator

        # top_toolbars
        # module toolbar
        self.toolbarModule = QtGui.QToolBar()
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbarModule)

        # label
        self.lblToolbarModule = QtGui.QLabel()
        self.lblToolbarModule.setText(_('moduleControl'))
        self.toolbarModule.addWidget(self.lblToolbarModule)

        # open
        self.btnOpen = QtGui.QPushButton()
        self.btnOpen.setText(_('open'))
        self.btnOpen.clicked.connect(self.open_clicked)
        self.toolbarModule.addWidget(self.btnOpen)

        # current module
        self.lblCurrentModule = QtGui.QLabel()
        self.lblCurrentModule.setText(_('currentModuleFile:') + ' ' + g.module_path)
        self.toolbarModule.addWidget(self.lblCurrentModule)

        # quit
        self.toolbarModule.addSeparator()
        self.btnKill = QtGui.QPushButton()
        self.btnKill.setText(_('quit'))
        self.btnKill.clicked.connect(Globals.app.quit)
        self.toolbarModule.addWidget(self.btnKill)

        # data toolbar
        self.addToolBarBreak(QtCore.Qt.TopToolBarArea)
        self.toolbarData = QtGui.QToolBar()
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbarData)
        # label
        self.lblToolbarData = QtGui.QLabel()
        self.lblToolbarData.setText(_('dataControl'))
        self.toolbarData.addWidget(self.lblToolbarData)

        # create db
        self.btnCreateDb = QtGui.QPushButton()
        self.btnCreateDb.setText(_('createDB'))
        self.btnCreateDb.clicked.connect(self.create_database_clicked)
        self.toolbarData.addWidget(self.btnCreateDb)

        # load default table
        self.btnLoadDef = QtGui.QPushButton()
        self.btnLoadDef.setText(_('loadDefaults'))
        self.btnLoadDef.clicked.connect(self.load_defaults_clicked)
        self.toolbarData.addWidget(self.btnLoadDef)

        # save as default
        self.btnToPreset = QtGui.QPushButton()
        self.btnToPreset.setText(_('writeAsDefaults'))
        self.btnToPreset.clicked.connect(self.write_table_as_defaults_clicked)
        self.toolbarData.addWidget(self.btnToPreset)

        # save all as default
        self.btnAllToPreset = QtGui.QPushButton()
        self.btnAllToPreset.setText(_('writeAllAsDefaults'))
        self.btnAllToPreset.clicked.connect(self.write_all_as_defaults_clicked)
        self.toolbarData.addWidget(self.btnAllToPreset)

        # right_toolbar
        self.toolbarTable = QtGui.QToolBar()
        self.addToolBar(QtCore.Qt.RightToolBarArea, self.toolbarTable)

        # caption
        self.lblTableChoice = QtGui.QLabel()
        self.lblTableChoice.setText(_('chooseTable:'))
        self.toolbarTable.addWidget(self.lblTableChoice)

        # choosing table
        self.tablesList = QtGui.QListWidget()
        if g.module_on:
            for table in g.root:
                self.tablesList.addItem(g.translator(table.get('name')))
            self.tablesList.setCurrentRow(0)
        self.tablesList.connect(self.tablesList, QtCore.SIGNAL("currentRowChanged(int)"),
                                lambda: self.init_table(self.tablesList.currentRow()))
        self.toolbarTable.addWidget(self.tablesList)

        # add
        self.btnAdd = QtGui.QPushButton()
        self.btnAdd.setText(_('addElement'))
        self.btnAdd.clicked.connect(self.add_clicked)
        self.toolbarTable.addWidget(self.btnAdd)

        # del
        self.btnDel = QtGui.QPushButton()
        self.btnDel.setText(_('delElement'))
        self.btnDel.clicked.connect(lambda: self.delete_clicked(self.dbView.selectedIndexes()))
        self.toolbarTable.addWidget(self.btnDel)

        # gen
        self.btnGen = QtGui.QPushButton()
        self.btnGen.setText(_('generate'))
        self.toolbarTable.addWidget(self.btnGen)

        # views
        # views label
        self.lblViews = QtGui.QLabel()
        self.lblViews.setText(_('chooseView:'))
        self.toolbarTable.addWidget(self.lblViews)
        # views' list
        self.views = QtGui.QListWidget()
        self.views.connect(self.views, QtCore.SIGNAL("currentRowChanged(int)"),
                           lambda: self.on_view_change(self.views.currentRow()))
        self.toolbarTable.addWidget(self.views)

        # double click lockout
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)

        # db object model & view
        self.db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        if g.module_on:
            self.db.setDatabaseName(g.root.get('file'))
            if not self.db.open():
                print('Failed to open database')
        else:
            self.toolbarData.setEnabled(False)
            self.toolbarTable.setEnabled(False)
        self.dbView = DBView()
        self.btnGen.clicked.connect(lambda: self.generate_clicked(self.dbView.dbModel.rowCount()))
        if g.module_on:
            self.init_table(self.tablesList.currentRow())
        self.dbView.doubleClicked.connect(self.view_double_clicked)

        self.setCentralWidget(self.dbView)
        self.setWindowTitle(_('tableEditor') + ' ' + str(_(g.root.get('name'))))

    def resizeEvent(self, event):
        # width
        self.dbView.geometry().setWidth(0.8 * event.size().width())
        self.toolbarTable.setMinimumWidth(0.2 * event.size().width())
        # height
        self.toolbarModule.setMinimumWidth(0.07 * event.size().height())
        self.dbView.geometry().setHeight(0.93 * event.size().height())

    def generate_clicked(self, row):
        gen = field.GenerateForm(self.tablesList.currentRow(), row)
        if gen.exec_():
            self.init_table(self.tablesList.currentRow(), update_views=False)

    def load_defaults_clicked(self):
        db_defaults.load()
        self.init_table(self.tablesList.currentRow(), update_views=False)

    def create_database_clicked(self):
        # free old db resources
        self.free_db()
        # remove file w/ old data
        os.remove(g.root.get('file'))
        # run all the CREATE TABLE according to *.xml settings
        db_defaults.create()
        # create new db connection
        self.open_db()
        # init current table again
        self.init_table(self.tablesList.currentRow())

    def write_all_as_defaults_clicked(self):
        table_nodes = list()
        table_records = dict()
        for table in g.root.findall('table'):
            table_nodes.append(table)
            table_records[table.get('name')] = list()
            model = QtSql.QSqlQueryModel()
            model.setQuery("SELECT * FROM " + table.get('name'))
            for index in range(0, model.rowCount()):
                record = dict()
                for f in table.findall('field'):
                    record[f.get('name')] = model.record(index).field(f.get('name')).value()
                table_records[table.get('name')].append(record)
        db_defaults.to_preset(table_nodes, table_records)

    def write_table_as_defaults_clicked(self):
        records = list()
        table = Globals.node(self.tablesList.currentItem().text(), g.root)
        for index in range(0, self.dbView.dbModel.rowCount()):
            record = dict()
            for f in table.findall('field'):
                record[f.attrib['name']] = self.dbView.dbModel.record(index).field(f.attrib['name']).value()
            records.append(record)
        db_defaults.to_preset([table], {table.get('name'): records})

    def delete_clicked(self, selected):
        db_edit_model = QtSql.QSqlTableModel()
        i = self.tablesList.currentRow()
        db_edit_model.setTable(g.root[i].get('name'))
        db_edit_model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        db_edit_model.select()
        # TODO in xml insert referenced param. If row with such param is deleted, program should
        # propose removing row(s) that references currently removed row
        # TODO redo delete with transaction and native sql
        if len(selected) > 0:
            for i in selected:
                db_edit_model.removeRows(i.row(), 1)
            if not db_edit_model.submitAll():
                print(db_edit_model.lastError().text())
            # reorganizing indexes
            for i in range(0, db_edit_model.rowCount()):
                db_edit_model.setData(db_edit_model.index(i, 0), i)
            if not db_edit_model.submitAll():
                print(db_edit_model.lastError().text())
        else:
            note = QtGui.QMessageBox()
            _ = g.translator
            note.setText(_('selectForDelete'))
            note.setWindowTitle(_('notification'))
            note.setStyleSheet(g.css)
            note.exec_()
            return
        self.init_table(self.tablesList.currentRow(), update_views=False)

    def edit_clicked(self, row, table_index):
        form = edit.EntryForm(table_index, row)
        if form.exec_():
            self.init_table(table_index, update_views=False)

    def add_clicked(self):
        row = self.dbView.dbModel.rowCount()
        self.edit_clicked(row, self.tablesList.currentRow())

    def view_double_clicked(self, index):
        if self.timer.isActive():
            return
        row = index.row()
        self.edit_clicked(row, self.tablesList.currentRow())

    def open_clicked(self):
        _ = g.translator
        open_dlg = QtGui.QFileDialog(caption='Open module')
        open_dlg.setStyleSheet(g.css)
        open_dlg.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        open_dlg.setFileMode(QtGui.QFileDialog.ExistingFile)
        open_dlg.setFilter("*.xml")
        if open_dlg.exec():
            file = open_dlg.selectedFiles()
            if Globals.validate(file[0]):
                g.change_module(file[0])
                self.toolbarData.setEnabled(True)
                self.toolbarTable.setEnabled(True)
                self.init_db()
                self.lblCurrentModule.setText(_('currentModuleFile:') + ' ' + g.module_path)
                self.setWindowTitle(_('tableEditor') + ' ' +
                                    str(_(g.root.get('name'))))
            else:
                error = QtGui.QMessageBox(2, _('error'), _('badXml'))
                error.setStyleSheet(g.css)
                error.exec()

    def on_view_change(self, view_index):
        if view_index == -1:
            return
        # shifting +1 if there is no default (i.e. default is first)
        shift = 1
        for v in g.root[self.tablesList.currentRow()].findall('view'):
            if v.get('name') == 'default':
                shift = 0
        # in case default view is selected and table doesn't have default view reimplemented, need to call normal
        # init_table without shenanigans
        if shift == 1 and view_index == 0:
            self.init_table(self.tablesList.currentRow(), update_views=False)
            return
        # obtaining view node
        view = g.root[self.tablesList.currentRow()].findall('view')[view_index - shift]
        columns, join = Globals.build_join(g.root[self.tablesList.currentRow()], view)
        if columns == "":
            self.init_table(self.tablesList.currentRow(), update_views=False, columns="*", join=join)
        else:
            self.init_table(self.tablesList.currentRow(), update_views=False, columns=columns, join=join)

    def init_table(self, table_index, update_views=True, columns="*", join=""):
        # print("SELECT " + columns + " FROM " + Globals.root[table_index].get('name') + join)
        model = QtSql.QSqlQueryModel()
        model.setQuery("SELECT " + columns + " FROM " + g.root[table_index].get('name') + join)
        self.dbView.dbModel = model
        # changing list of available lists for this particular table
        if update_views:
            views = list()
            for view in g.root[table_index].findall('view'):
                views.append(g.translator(view.get('name')))
            if 'default' not in views:
                views.insert(0, 'default')
            self.views.clear()
            self.views.addItems(views)
            self.views.setCurrentRow(0)
        # changing table view
        for i in range(0, self.dbView.dbModel.columnCount()):
            header = self.dbView.dbModel.headerData(i, QtCore.Qt.Horizontal)
            self.dbView.dbModel.setHeaderData(i, QtCore.Qt.Horizontal, g.translator(header))
        self.dbView.setModel(self.dbView.dbModel)
        if 'generate' in g.root[table_index].attrib.keys():
            self.btnGen.setEnabled(True)
        else:
            self.btnGen.setEnabled(False)

    def free_db(self):
        self.dbView.setModel(None)
        del self.dbView.dbModel
        self.db.close()
        del self.db
        QtSql.QSqlDatabase.removeDatabase('qt_sql_default_connection')

    def open_db(self):
        self.db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(g.root.get('file'))
        if not self.db.open():
            print('Failed to open database ' + g.root.get('file'))
        # set up models and stuff again
        self.dbView.dbModel = QtSql.QSqlQueryModel()

    def init_db(self):
        # free old db resources
        self.free_db()
        # assign new
        self.open_db()
        # init views
        self.tablesList.clear()
        for table in g.root:
            self.tablesList.addItem(g.translator(table.get('name')))
        self.tablesList.setCurrentRow(0)
        self.init_table(self.tablesList.currentRow())

if __name__ == '__main__':
    # app
    mainWindow = MainWindow()
    mainWindow.setGeometry(200, 200, 1000, 600)
    # launch
    mainWindow.show()
    sys.exit(Globals.app.exec_())
