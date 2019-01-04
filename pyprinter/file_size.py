from typing import Optional, Tuple, TypeVar, Union

from pyprinter import get_printer, Printer

# An internal type for self-related methods inside FileSize.
_FileSizeType = TypeVar('_FileSizeType', bound='FileSize')


class FileSize:
    """
    Represents a file size measured in bytes.
    """

    MULTIPLIERS = [('kb', 1024), ('mb', 1024 ** 2), ('gb', 1024 ** 3), ('tb', 1024 ** 4), ('b', 1)]

    SIZE_COLORS = {
        'B': Printer.YELLOW,
        'KB': Printer.CYAN,
        'MB': Printer.GREEN,
        'GB': Printer.RED,
        'TB': Printer.DARK_RED
    }

    def __init__(self, size: Union[int, float, str, bytes, _FileSizeType]):
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

    def __str__(self) -> str:
        unit, unit_divider = self._unit_info()
        # We multiply then divide by 100 in order to have only two decimal places.
        size_in_unit = (self.size * 100) / unit_divider / 100
        return f'{size_in_unit:.1f} {unit}'

    def __repr__(self) -> str:
        return f'<FileSize - {self}>'

    def _unit_info(self) -> Tuple[str, int]:
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
    def bytes(self) -> int:
        return self.size

    @property
    def kilo_bytes(self) -> int:
        return self.bytes // 1024

    @property
    def mega_bytes(self) -> int:
        return self.kilo_bytes // 1024

    @staticmethod
    def get_file_size_string(size_bytes: int) -> str:
        return str(FileSize(size_bytes))

    def __add__(self, file_size: Union[int, float, _FileSizeType]) -> _FileSizeType:
        """
        Handles adding numbers or file sizes to the file size.

        :param file_size: The size to add to the current file size.
        :return: A new file size with the combined number of the file sizes.
        """
        if isinstance(file_size, FileSize):
            return FileSize(self.size + file_size.size)
        if isinstance(file_size, (int, float)):
            return FileSize(self.size + file_size)
        raise TypeError(f'Can\'t add a {type(file_size).__name__} to a file size')

    def __sub__(self, file_size: Union[int, float, _FileSizeType]) -> _FileSizeType:
        """
        Handles subtracting numbers or file sizes from the file size.

        :param file_size: The size to subtract from the current file size.
        :return: A new file size with the difference between the file sizes.
        """
        if isinstance(file_size, FileSize):
            return FileSize(self.size - file_size.size)
        if isinstance(file_size, (int, float)):
            return FileSize(self.size - file_size)
        raise TypeError(f'Can\'t subtract a {type(file_size).__name__} from a file size')

    def __int__(self) -> int:
        return self.size

    def __float__(self) -> float:
        return float(self.size)

    def __mul__(self, amount: Union[int, float]) -> _FileSizeType:
        """
        Multiplies the file size by the specified amount.

        :param amount: The amount by which to multiply.
        :return: A new file size with the multiplied value of this file size.
        """
        if isinstance(amount, (int, float)):
            return FileSize(self.size * amount)
        raise TypeError(f'Can\'t multiply a file size by a {type(amount).__name__} (only by a number)')

    def __truediv__(self, amount: Union[int, float]) -> _FileSizeType:
        """
        Divides the file size by the specified amount.

        :param amount: The amount by which to divide.
        :return: A new file size with the divided value of this file size.
        """
        if isinstance(amount, (int, float)):
            return FileSize(self.size / amount)
        raise TypeError(f'Can\'t divide a file size by a {type(amount).__name__} (only by a number)')

    def __floordiv__(self, amount: Union[int, float]) -> _FileSizeType:
        """
        Divides the file size by the specified amount and floors the result.

        :param amount: The amount by which to divide.
        :return: A new file size with the divided value of this file size.
        """
        if isinstance(amount, (int, float)):
            return FileSize(self.size // amount)
        raise TypeError(f'Can\'t divide a file size by a {type(amount).__name__} (only by a number)')

    def __lt__(self, other) -> bool:
        """
        Returns whether this size is less than the other size.

        :param FileSize other: The other size.
        """
        return int(self) < int(FileSize(other))

    def __le__(self, other) -> bool:
        """
        Returns whether this size is less than or equal to the other size.

        :param FileSize other: The other size.
        """
        return int(self) <= int(FileSize(other))

    def __eq__(self, other) -> bool:
        """
        Returns whether this size is equal to the other size.

        :param FileSize other: The other size.
        """
        return other is not None and isinstance(other, (int, float, FileSize)) and int(self) == int(FileSize(other))

    def __ne__(self, other) -> bool:
        """
        Returns whether this size is not equal to the other size.

        :param FileSize other: The other size.
        """
        return not self.__eq__(other)

    def __gt__(self, other) -> bool:
        """
        Returns whether this size is greater than the other size.

        :param FileSize other: The other size.
        """
        return int(self) > int(FileSize(other))

    def __ge__(self, other) -> bool:
        """
        Returns whether this size is greater than or equal to the other size.

        :param FileSize other: The other size.
        """
        return int(self) >= int(FileSize(other))

    def pretty_print(self, printer: Optional[Printer] = None, min_width: int = 1, min_unit_width: int = 1):
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
        unit = '{}{}'.format(' ' * (min_unit_width - len(unit)), unit)
        size_string = f'{size_in_unit:.1f}'
        total_len = len(size_string) + 1 + len(unit)
        if printer is None:
            printer = get_printer()
        spaces_count = min_width - total_len
        if spaces_count > 0:
            printer.write(' ' * spaces_count)
        printer.write(f'{size_string} {unit_color}{unit}')
