from collections import defaultdict
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

    def __init__(self, title, data, column_size_map=None, column_size_limit=COLUMN_SIZE_LIMIT,
                 headers_color=pyprinter.Printer.NORMAL, title_align=ALIGN_CENTER):
        """
        Initializes the table.

        :param title: The title of the table.
        :param data: A list of dictionaries, each representing a row.
        :param column_size_map: A map between each column name and its max size.
        :param column_size_limit: Column values larger than that size will be truncated.
        :param headers_color: The color of the columns (the headers of the table).
        :param title_align: The alignment of the name of the table.
        """
        self.title = title
        self.data = data
        self._column_size_map = defaultdict(lambda: column_size_limit)
        if column_size_map:
            for column_name, max_size in column_size_map.items():
                self._column_size_map[column_name] = max_size
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
                title = ' ' * (first_line_length // 2 - len(self.title) // 2) + self.title
            elif self.title_align == self.ALIGN_LEFT:
                title = self.title
            else:
                title = ' ' * (first_line_length - len(self.title)) + self.title
            printer.write_line(printer.YELLOW + title)
            # We split the table to lines in order to keep the indentation.
            printer.write_line(table_string)

    @property
    def rows(self):
        """
        Returns the table rows.
        """
        return [list(d.values()) for d in self.data]

    @property
    def columns(self):
        """
        Returns the table columns.
        """
        return list(self.data[0].keys())

    def set_column_size_limit(self, column_name, size_limit):
        """
        Sets the size limit of a specific column.

        :param column_name: The name of the column to change.
        :param size_limit: The max size of the column width.
        """
        if self._column_size_map.get(column_name):
            self._column_size_map[column_name] = size_limit
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
        rows = self.rows
        columns = self.columns
        # Add the column color.
        if self._headers_color != pyprinter.Printer.NORMAL and len(rows) > 0 and len(columns) > 0:
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
        for column, max_width in self._column_size_map.items():
            table.max_width[column] = max_width

        return table

    def get_as_html(self):
        """
        Returns the table object as an HTML string.

        :return: HTML representation of the table.
        """
        table_string = self._get_pretty_table().get_html_string()
        title = ('{:^' + str(len(table_string.splitlines()[0])) + '}').format(self.title)
        return '<center><h1>{0}</h1></center>'.format(title) + table_string

    def get_as_csv(self, output_file_path=None):
        """
        Returns the table object as a CSV string.

        :param output_file_path: The output file to save the CSV to, or None.
        :return: CSV representation of the table.
        """
        output = StringIO() if not output_file_path else open(output_file_path, 'w')
        try:
            csv_writer = csv.writer(output)

            csv_writer.writerow(self.columns)
            for row in self.rows:
                csv_writer.writerow(row)
            output.seek(0)
            return output.read()
        finally:
            output.close()

    def __iter__(self):
        return iter(self.rows)
