import pyprinter


class FileSize(object):
    """
    Represents a file size measured in bytes.
    """

    MULTIPLIERS = [('kb', 1024), ('mb', 1024 ** 2), ('gb', 1024 ** 3), ('tb', 1024 ** 4), ('b', 1)]

    SIZE_COLORS = {'B': pyprinter.Printer.YELLOW,
                   'KB': pyprinter.Printer.CYAN,
                   'MB': pyprinter.Printer.GREEN,
                   'GB': pyprinter.Printer.RED,
                   'TB': pyprinter.Printer.DARK_RED}

    def __init__(self, size):
        """
        Initializes a new FileSize from an integer (or a string) of the bytes amount.
        """
        # Handle cases where size is another FileSize instance (Copy C'tor).
        if isinstance(size, FileSize):
            self.size = size.size
        else:
            chosen_multiplier = 1
            # Handle cases where size is a string like '1,600 KB'.
            if isinstance(size, bytes):
                size = size.decode('UTF-8')
            if isinstance(size, str):
                size = size.replace(',', '').lower()
                for ms, mi in self.MULTIPLIERS:
                    if size.endswith(ms):
                        chosen_multiplier = mi
                        size = size[:-len(ms)]
                        break
            self.size = int(float(size) * chosen_multiplier)

    def __str__(self):
        unit, unit_divider = self._unit_info()
        # We multiply then divide by 100 in order to have only two decimal places.
        size_in_unit = (self.size * 100) / unit_divider / 100
        return '{0:.1f} {1}'.format(size_in_unit, unit)

    def __repr__(self):
        return '<FileSize - {0}>'.format(self)

    def _unit_info(self):
        """
        Returns both the best unit to measure the size, and its power.

        :return: A tuple containing the unit and its power.
        """
        abs_bytes = abs(self.size)
        if abs_bytes < 1024:
            unit = 'B'
            unit_divider = 1
        elif abs_bytes < (1024 ** 2):
            unit = 'KB'
            unit_divider = 1024
        elif abs_bytes < (1024 ** 3):
            unit = 'MB'
            unit_divider = (1024 ** 2)
        elif abs_bytes < (1024 ** 4):
            unit = 'GB'
            unit_divider = (1024 ** 3)
        else:
            unit = 'TB'
            unit_divider = (1024 ** 4)

        return unit, unit_divider

    @property
    def bytes(self):
        return self.size

    @property
    def kilo_bytes(self):
        return self.bytes // 1024

    @property
    def mega_bytes(self):
        return self.kilo_bytes // 1024

    @staticmethod
    def get_file_size_string(size_bytes):
        return str(FileSize(size_bytes))

    def __add__(self, file_size):
        """
        Handles adding numbers or file sizes to the file size.

        :param file_size: The size to add to the current file size.
        :return: A new file size with the combined number of the file sizes.
        """
        if isinstance(file_size, FileSize):
            return FileSize(self.size + file_size.size)
        if isinstance(file_size, (int, float)):
            return FileSize(self.size + file_size)
        raise TypeError('Can\'t add a {} to a file size'.format(type(file_size).__name__))

    def __sub__(self, file_size):
        """
        Handles subtracting numbers or file sizes from the file size.

        :param file_size: The size to subtract from the current file size.
        :return: A new file size with the difference between the file sizes.
        """
        if isinstance(file_size, FileSize):
            return FileSize(self.size - file_size.size)
        if isinstance(file_size, (int, float)):
            return FileSize(self.size - file_size)
        raise TypeError('Can\'t subtract a {} from a file size'.format(type(file_size).__name__))

    def __int__(self):
        return self.size

    def __float__(self):
        return float(self.size)

    def __mul__(self, amount):
        """
        Multiplies the file size by the specified amount.

        :param amount: The amount by which to multiply.
        :return: A new file size with the multiplied value of this file size.
        """
        if isinstance(amount, (int, float)):
            return FileSize(self.size * amount)
        raise TypeError('Can\'t multiply a file size by a {} (only by a number)'.format(type(amount).__name__))

    def __truediv__(self, amount):
        """
        Divides the file size by the specified amount.

        :param amount: The amount by which to divide.
        :return: A new file size with the divided value of this file size.
        """
        if isinstance(amount, (int, float)):
            return FileSize(self.size / amount)
        raise TypeError('Can\'t divide a file size by a {} (only by a number)'.format(type(amount).__name__))

    def __floordiv__(self, amount):
        """
        Divides the file size by the specified amount and floors the result.

        :param amount: The amount by which to divide.
        :return: A new file size with the divided value of this file size.
        """
        if isinstance(amount, (int, float)):
            return FileSize(self.size // amount)
        raise TypeError('Can\'t divide a file size by a {} (only by a number)'.format(type(amount).__name__))

    def __lt__(self, other):
        """
        Returns whether this size is less than the other size.

        :param FileSize other: The other size.
        """
        return int(self) < int(FileSize(other))

    def __le__(self, other):
        """
        Returns whether this size is less than or equal to the other size.

        :param FileSize other: The other size.
        """
        return int(self) <= int(FileSize(other))

    def __eq__(self, other):
        """
        Returns whether this size is equal to the other size.

        :param FileSize other: The other size.
        """
        return other is not None and isinstance(other, (int, float, FileSize)) and int(self) == int(FileSize(other))

    def __ne__(self, other):
        """
        Returns whether this size is not equal to the other size.

        :param FileSize other: The other size.
        """
        return not self.__eq__(other)

    def __gt__(self, other):
        """
        Returns whether this size is greater than the other size.

        :param FileSize other: The other size.
        """
        return int(self) > int(FileSize(other))

    def __ge__(self, other):
        """
        Returns whether this size is greater than or equal to the other size.

        :param FileSize other: The other size.
        """
        return int(self) >= int(FileSize(other))

    def pretty_print(self, printer=None, min_width=1, min_unit_width=1):
        """
        Prints the file size (and it's unit), reserving places for longer sizes and units.
        For example:
            min_unit_width = 1:
                793 B
                100 KB
            min_unit_width = 2:
                793  B
                100 KB
            min_unit_width = 3:
                793   B
                100  KB
        """
        unit, unit_divider = self._unit_info()
        unit_color = self.SIZE_COLORS[unit]
        # Multiply and then divide by 100 in order to have only two decimal places.
        size_in_unit = (self.size * 100) / unit_divider / 100
        # Add spaces to align the units.
        unit = ' ' * (min_unit_width - len(unit)) + unit
        size_string = '{0:.1f}'.format(size_in_unit)
        total_len = len(size_string) + 1 + len(unit)
        if printer is None:
            printer = pyprinter.get_printer()
        spaces_count = min_width - total_len
        if spaces_count > 0:
            printer.write(' ' * spaces_count)
        printer.write(size_string + ' ' + unit_color + unit)
