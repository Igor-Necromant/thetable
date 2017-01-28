import parser
import sqlite3
import xml.etree.ElementTree as Et
from PyQt4 import QtSql
from src.globals import Globals, g


# tables is list of nodes
# values is dictionary of records per table { "table": [{ "field": value, ... }, ...], ... }
def to_preset(tables, values):
    filename = 'defaults.xml'
    try:
        tree = Et.parse(filename)
        root = tree.getroot()
    except (FileNotFoundError, Et.ParseError):
        root = Et.Element('presetValues')
    for table in tables:
        # removing previous preset data for this table if it existed
        for node in root:
            if node.attrib['name'] == table.attrib['name']:
                root.remove(node)
        # now adding new
        preset_table = Et.SubElement(root, 'table')
        preset_table.set('name', table.attrib['name'])
        for record in values[table.get('name')]:
            entry = Et.SubElement(preset_table, 'entry')
            for el in table:
                if el.tag == 'field':
                    node = Et.SubElement(entry, el.attrib['name'])
                    node.set('type', Globals.field_type[el.attrib['type']])
                    node.text = str(record[el.attrib['name']])
    Globals.write_xml(root, filename)


def create():
    db = sqlite3.connect(g.root.attrib['file'])
    for table in g.root:
        query = "CREATE TABLE " + table.attrib['name'] + " ("
        fk = str()
        for node in table:
            if node.tag == 'field':
                query += node.attrib['name'] + ' ' + Globals.field_type[node.attrib['type']]
                if node.attrib['type'] == 'pk':
                    query += ' PRIMARY KEY'
                query += ", "
                if node.attrib['type'] == 'fk':
                    fk += "FOREIGN KEY(" + node.attrib['name'] + ") REFERENCES " + node.attrib['fk'] + "(id), "
        query += fk
        query = query[:len(query) - 2]
        query += ');'
        db.execute(query)
    db.commit()
    db.close()


def load():
    # filling levels table
    model = QtSql.QSqlTableModel()
    db = model.database()
    db.transaction()
    for table in g.root:
        if 'default' in table.attrib.keys():
            # removing old rows
            query = QtSql.QSqlQuery(db)
            query.exec_("DELETE FROM " + table.attrib['name'])
    if not db.commit():
        print(db.lastError().text())
        db.rollback()
    db.transaction()
    for table in g.root:
        if 'default' in table.attrib.keys():
            # adding new from file
            if table.attrib['default'] == 'file':
                if 'file' in table.attrib.keys():
                    p_root = Et.parse(table.attrib['file']).getroot()
                    preset = Globals.node(table.attrib['name'], p_root)
                    if preset:
                        for entry in preset:
                            row = list()
                            for node in entry:
                                if node.attrib['type'] == 'INT':
                                    value = int(node.text)
                                elif node.attrib['type'] == 'REAL':
                                    value = float(node.text)
                                else:
                                    value = node.text
                                row.append(value)
                            query = QtSql.QSqlQuery()
                            s = "INSERT INTO " + table.attrib['name'] + " VALUES(?"
                            for v in range(0, len(row) - 1):
                                s += ",?"
                            s += ")"
                            query.prepare(s)
                            for v in row:
                                query.addBindValue(v)
                            query.exec_()
                    else:
                        print(table.attrib['name'] + ' table not found in ' + table.get('file') + ' file.')
                else:
                    print('Bad xml.')
            # adding new mathematically
            else:
                for x in range(0, int(table.attrib['default'])):
                    row = list()
                    for node in table:
                        if node.tag == 'field':
                            if node.attrib['name'] == 'id':
                                value = x
                            elif 'default' in node.attrib.keys():
                                d = eval(parser.expr(node.attrib['default']).compile())
                                if node.attrib['type'] == 'real':
                                    d = round(d, 2)
                                value = d
                            else:
                                value = str()
                            row.append(value)
                    query = QtSql.QSqlQuery()
                    s = "INSERT INTO " + table.attrib['name'] + " VALUES(?"
                    for v in range(0, len(row) - 1):
                        s += ",?"
                    s += ")"
                    query.prepare(s)
                    for v in row:
                        query.addBindValue(v)
                    query.exec_()
    if not db.commit():
        print(db.lastError().text())
        db.rollback()
