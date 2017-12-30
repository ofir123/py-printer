from collections import OrderedDict
import csv
from io import StringIO
import re

import prettytable

import pyprinter


class Table(object):
    """
    This class represent a table, by using rows.
    """

    COLUMN_SIZE_LIMIT = 40
    ALIGN_CENTER = 0
    ALIGN_LEFT = 1
    ALIGN_RIGHT = 2
    _ALIGN_DICTIONARY = {ALIGN_CENTER: 'c', ALIGN_LEFT: 'l', ALIGN_RIGHT: 'r'}

    def __init__(self, name, rows, columns=None, column_size_limit=COLUMN_SIZE_LIMIT,
                 headers_color=pyprinter.Printer.NORMAL, title_align=ALIGN_CENTER):
        """
        Initializes the table.

        :param name: The name of the scheme.
        :param rows: A list of all the rows in this scheme. All members of this list should be from the same class.
        :param columns: A list of the columns, or an OrderedDict of the columns and their max sizes.
                        If None, will be extracted from the first row's keys.
        :param column_size_limit: Column values larger than that size will be truncated.
        :param headers_color: The color of the columns (the headers of the table).
        :param title_align: The alignment of the name of the table.
        """
        self.name = name
        self._rows = rows
        self._column_size_limit = column_size_limit
        # _columns is a dict that maps the name of the column to its size limit.
        if isinstance(columns, OrderedDict):
            self._columns = columns
        else:
            self._columns = OrderedDict()
            if columns is not None:
                for column in columns:
                    self._columns[column] = self._column_size_limit
        self._headers_color = headers_color
        self.title_align = title_align

    def pretty_print(self, printer=None, align=ALIGN_CENTER, border=False):
        """
        Pretty prints the table.

        :param printer: The printer to print with.
        :param align: The alignment of the cells(Table.ALIGN_CENTER/ALIGN_LEFT/ALIGN_RIGHT)
        :param border: Whether to add a border around the table
        """
        if printer is None:
            printer = pyprinter.get_printer()
        table_string = self._get_pretty_table(indent=printer.indents_sum, align=align, border=border).get_string()
        if table_string != '':
            first_line = table_string.splitlines()[0]
            first_line_length = len(first_line) - len(re.findall(pyprinter.Printer._ANSI_REGEXP, first_line)) * \
                pyprinter.Printer._ANSI_COLOR_LENGTH
            if self.title_align == self.ALIGN_CENTER:
                title = ' ' * (first_line_length // 2 - len(self.name) // 2) + self.name
            elif self.title_align == self.ALIGN_LEFT:
                title = self.name
            else:
                title = ' ' * (first_line_length - len(self.name)) + self.name
            printer.write_line(printer.YELLOW + title)
            # We split the table to lines in order to keep the indentation.
            printer.write_line(table_string)

    @property
    def rows(self):
        """
        Returns the rows only of the table, in a case where columns is None.
        """
        rows = self._rows
        if len(self._columns.keys()) == 0:
            rows = self._rows[1:]

        return rows

    @property
    def columns(self):
        """
        Returns the columns only of the table, in a case where columns is None.
        """
        columns = self._columns.keys()
        if len(columns) == 0:
            columns = self._rows[0] if isinstance(self._rows[0], list) else self._rows[0].__dict__.keys()

        return list(columns)

    @property
    def rows_list(self):
        """
        Returns the rows of the table as a list.
        """
        rows = self.rows
        columns = self.columns
        result_rows = []

        for row in rows:
            if isinstance(row, dict):
                row = [row.get(column) for column in columns]
            elif not isinstance(row, list):
                row = [getattr(row, column) for column in columns]
            result_rows.append(row)

        return result_rows

    def set_column_size_limit(self, column_name, size_limit):
        """
        Sets the size limit of a specific column.

        :param column_name: The name of the column to change.
        :param size_limit: The max size of the column width.
        """
        if len(self._columns.keys()) == 0:
            raise ValueError('Can\'t have special column size limit without columns provided!')
        if self._columns.get(column_name) is not None:
            self._columns[column_name] = size_limit
        else:
            raise ValueError('There is no column named {}!'.format(column_name))

    def _get_pretty_table(self, indent=0, align=ALIGN_CENTER, border=False):
        """
        Returns the table format of the scheme, i.e.:

            <table name>
        +----------------+----------------
        |    <field1>    |   <field2>...
        +----------------+----------------
        | value1(field1) |  value1(field2)
        | value2(field1) |  value2(field2)
        | value3(field1) |  value3(field2)
        +----------------+----------------
        """
        rows = self.rows_list
        columns = self.columns
        # Adding the column color.
        if len(columns) > 0 and self._headers_color != pyprinter.Printer.NORMAL and len(rows) > 0 and len(rows[0]) > 0:
            # We need to copy the lists so that we wont insert colors in the original ones.
            rows[0] = rows[0][:]
            columns = columns[:]
            columns[0] = self._headers_color + columns[0]
            # Write the table itself in NORMAL color.
            rows[0][0] = pyprinter.Printer.NORMAL + str(rows[0][0])

        table = prettytable.PrettyTable(columns, border=border, max_width=pyprinter.get_console_width() - indent)
        table.align = self._ALIGN_DICTIONARY[align]

        for row in rows:
            table.add_row(row)
        # Set the max width according to the columns size dict, or by default size limit when columns were not provided.
        if len(self._columns.keys()) != 0:
            for column, max_width in self._columns.items():
                table.max_width[column] = max_width
        else:
            for column in columns:
                table.max_width[column] = self._column_size_limit
        return table

    def get_as_html(self):
        """
        Returns the table object as an HTML string.

        :return: HTML representation of the table.
        """
        table_string = self._get_pretty_table().get_html_string()
        title = ('{:^' + str(len(table_string.splitlines()[0])) + '}').format(self.name)
        return '<center><h1>{0}</h1></center>'.format(title) + table_string

    def get_as_csv(self):
        """
        Returns the table object as a CSV string.

        :return: CSV representation of the table.
        """
        string_io = StringIO()
        try:
            csv_writer = csv.writer(string_io)
            rows = self.rows_list
            columns = self.columns

            csv_writer.writerow(columns)
            for row in rows:
                csv_writer.writerow(row)
            string_io.seek(0)
            return string_io.read()
        finally:
            string_io.close()

    def __iter__(self):
        return iter(self.rows)
