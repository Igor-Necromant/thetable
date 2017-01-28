import gettext
import xml.etree.ElementTree as Et
from PyQt4 import QtSql, QtGui
import sys
from os.path import expanduser, realpath
import configparser
from os import makedirs, chdir, getcwd


class Globals:
    app = QtGui.QApplication(sys.argv)
    screen_resolution = app.desktop().screenGeometry()
    field_type = {'pk': 'INT',
                  'line': 'TEXT',
                  'real': 'REAL',
                  'color': 'TEXT',
                  'int': 'INT',
                  'text': 'TEXT',
                  'hash': 'TEXT',
                  'bool': 'INT',
                  'choice': 'TEXT',
                  'fk': 'INT'}

    def __init__(self):
        # set real working directory
        print('Debug message: ' + getcwd())
        chdir(realpath(__file__)[:-len('src/globals.py')])
        print('Debug message: ' + getcwd())
        try:
            self.translator = gettext.translation('tables', 'localization/', ['ru_RU']).gettext
        except FileNotFoundError:
            self.translator = lambda x: x
        # initializing
        self.module_on = False
        self.module_path = str()
        self.root = dict()
        # getting config done properly
        self.config_path = expanduser('~') + '/.config/iamthetable/'
        makedirs(self.config_path, exist_ok=True)
        self.config_path += 'config'
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)
        if 'DEFAULT' in self.config:
            if 'module' in self.config['DEFAULT']:
                try:
                    self.module_path = self.config['DEFAULT']['module']
                    self.root = Et.parse(self.module_path).getroot()
                    self.module_on = True
                except FileNotFoundError:
                    self.module_path = str()
        try:
            self.css = open(str(self.root.get('style')), 'r').read()
        except FileNotFoundError:
            self.css = ''

    def change_module(self, module_path):
        self.module_path = module_path
        self.module_on = True
        self.config['DEFAULT']['module'] = self.module_path
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
        self.root = Et.parse(self.module_path).getroot()
        self.change_style()

    def change_style(self, style_path=-1):
        if style_path == -1:
            style_path = self.root.get('style')
        try:
            self.css = open(str(style_path), 'r').read()
        except FileNotFoundError:
            self.css = ''

    @staticmethod
    def write_xml(root, filename):
        Et.ElementTree(root).write(filename)
        # adding whitespaces for readability
        text = open(filename, 'r').read()
        open(filename, 'w').write(Globals.add_whitespace(text))

    @staticmethod
    def add_whitespace(text):
        tag = str()  # tag info, defines whitespaces
        write_tag = False  # if true, tag is written for further recognition
        indent = '\n'  # stuff put between > and <
        result = text  # string that will contain new version of text
        result_index = 0  # stores index differences between result and original text
        for i in range(0, len(text)):
            # tag is over
            if text[i] == '>':
                # stop writing
                write_tag = False
                # increase indent unless it is 1) closing tag 2) one-line tag 3) tag that specifies xml version
                if tag[0] != '/' and tag[-1] != '/' and tag[0] != '?':
                    indent += '    '
                # clear current tag
                tag = str()
            if write_tag:
                tag += text[i]
            if text[i] == '<':
                write_tag = True
                if i != 0:
                    # decrease indent when closing tag is encountered
                    if i + 1 < len(text):
                        if text[i + 1] == '/':
                            indent = indent[:-4]
                    # insert indent and update result index
                    if text[i - 1] == '>':
                        result = result[:i + result_index] + indent + text[i:]
                        result_index += len(indent)
        return result

    @staticmethod
    def node(name, branch):
        for node in branch:
            if node.attrib['name'] == name:
                return node
        return Et.Element()

    @staticmethod
    def build_join(table, view):
        def make_fks(node):
            # generating list of existing fks in this particular table
            local_fks = list()
            for f in node.findall('field'):
                if f.get('type') == 'fk':
                    local_fks.append(f)
            return local_fks

        # digging into tag, recursively deciphering tag and appending to join and columns strings
        def add(parent_name, tag, local_name, local_fks, my_joined):
            my_join = str()
            my_columns = str()
            # nothing to decipher in tag, time to append to columns
            if tag.find('.') == -1:
                my_columns += '__' + parent_name + '__.' + tag + ' AS ' + local_name + ", "
                return [my_columns, my_join]
            for fk in local_fks:
                # finding which fk this is about
                if fk.get('name') == tag[:len(fk.get('name'))]:
                    # appending to join
                    if fk.get('name') not in my_joined:
                        my_join += " JOIN " + fk.get('fk') + " AS __" + fk.get('name') + "__ ON __" +\
                                   fk.get('name') + "__.id = __" + parent_name + "__." + fk.get('name')
                        my_joined.append(fk.get('name'))
                    # generating params for recursive add call
                    # removing this fk's key from tag
                    tag = tag[len(fk.get('name')) + 1:]
                    # getting child table object from xml
                    kid = Globals.node(fk.get('fk'), g.root)
                    # getting list of fk in child object
                    kids_fks = make_fks(kid)
                    # getting returned columns and join
                    local_to_add = add(fk.get('name'), tag, local_name, kids_fks, my_joined)
                    # updating columns and join
                    my_columns += local_to_add[0]
                    my_join += local_to_add[1]
                    return [my_columns, my_join]
        # initializing strings for init_table's select query
        columns = str()
        join = " AS __" + table.get('name') + "__"
        joined = list()
        fks = make_fks(table)
        for col in view:
            if isinstance(col.text, type(None)):
                name = col.tag
                point = name.rfind('.')
                if point != -1:
                    name = name[point + 1:]
            else:
                name = '`' + col.text + '`'
            to_add = add(table.get('name'), col.tag, name, fks, joined)
            columns += to_add[0]
            join += to_add[1]
        columns = columns[:len(columns) - 2]
        return [columns, join]

    @staticmethod
    def master_submit(to_submit):
        if type(to_submit) != dict:
            print('[edit][master_submit] WTS is this')
            return
        model = QtSql.QSqlTableModel()
        db = model.database()
        db.transaction()
        for table in to_submit.keys():
            for entry in to_submit[table].keys():
                if to_submit[table][entry]['id']:
                    # INSERT
                    query = QtSql.QSqlQuery()
                    insert = "INSERT INTO " + table + " (id"
                    values = " VALUES(:id"
                    for field in to_submit[table][entry].keys():
                        if field != 'id':
                            insert += "," + field
                            values += ",:" + field
                    insert += ')'
                    values += ')'
                    query.prepare(insert + values)
                    for field in to_submit[table][entry].keys():
                        if field != 'id':
                            query.bindValue(":" + field, to_submit[table][entry][field])
                        else:
                            query.bindValue(":" + field, int(entry))
                    query.exec_()
                else:
                    # UPDATE
                    query = QtSql.QSqlQuery()
                    update = "UPDATE " + table + " SET "
                    for field in to_submit[table][entry].keys():
                        if field != 'id':
                           update += field + '=:' + field + ','
                    update = update[:(len(update) - 1)]
                    update += ' WHERE id=' + entry
                    query.prepare(update)
                    for field in to_submit[table][entry].keys():
                        if field != 'id':
                            query.bindValue(":" + field, to_submit[table][entry][field])
                    query.exec_()
        if not db.commit():
            print(db.lastError().text())
            db.rollback()

    @staticmethod
    def validate(filename):
        print(filename)
        return True


g = Globals()
