import os
import re
import subprocess
import sys
from typing import List, Optional

# True if printer is in QT console context.
_IN_QT = None


class DefaultWriter:
    """
    A default writing stream.
    """

    def __init__(self, output_file=None, disabled: bool = False):
        """
        Initializes the default writer.

        :param output_file: The output file to write to (default is IPython's io.stdout).
        :param disabled: If True, nothing will be printed.
        """
        self.output_file = output_file or sys.stdout
        self.disabled = disabled

    def write(self, text: str):
        if not self.disabled:
            print(text, end='', file=self.output_file)


class _TextGroup:
    """
    This class is a context manager that adds indentation before the text it prints.
    It should only be created by specific methods of the Printer class.
    """

    def __init__(self, printer, unit: int, add_line: bool):
        self.printer = printer
        self.unit = unit
        self._add_line = add_line

    def __enter__(self):
        # Treat this like a new line.
        if self.printer._in_line:
            self.printer._is_first_line = True
        self.printer._indents.append(self.unit)
        self.printer.indents_sum += self.unit

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.printer._is_first_line = False
        self.printer._indents.pop()
        self.printer.indents_sum -= self.unit
        # Treat this like a line break.
        if self._add_line and self.printer._in_line:
            self.printer.write_line()


class Printer:
    """
    A user-friendly printer, with auxiliary functions for colors and tabs.
    """

    DEFAULT_INDENT = 4
    SEPARATOR = ':'
    LINE_SEP = '\n'

    # ANSI Color codes constants.
    _ANSI_COLOR_PREFIX = '\x1b'
    _ANSI_REGEXP = re.compile('\x1b\\[(\\d;)?(\\d+)m')
    _ANSI_COLOR_CODE = f'{_ANSI_COLOR_PREFIX}[%s%dm'
    _DARK_CODE = '0;'
    _LIGHT_CODE = '1;'

    NORMAL = _ANSI_COLOR_CODE % (_DARK_CODE, 0)
    DARK_RED = _ANSI_COLOR_CODE % (_DARK_CODE, 31)
    DARK_GREEN = _ANSI_COLOR_CODE % (_DARK_CODE, 32)
    DARK_YELLOW = _ANSI_COLOR_CODE % (_DARK_CODE, 33)
    DARK_BLUE = _ANSI_COLOR_CODE % (_DARK_CODE, 34)
    DARK_PURPLE = _ANSI_COLOR_CODE % (_DARK_CODE, 35)
    DARK_CYAN = _ANSI_COLOR_CODE % (_DARK_CODE, 36)
    GREY = _ANSI_COLOR_CODE % (_DARK_CODE, 37)
    RED = _ANSI_COLOR_CODE % (_LIGHT_CODE, 31)
    GREEN = _ANSI_COLOR_CODE % (_LIGHT_CODE, 32)
    YELLOW = _ANSI_COLOR_CODE % (_LIGHT_CODE, 33)
    BLUE = _ANSI_COLOR_CODE % (_LIGHT_CODE, 34)
    PURPLE = _ANSI_COLOR_CODE % (_LIGHT_CODE, 35)
    CYAN = _ANSI_COLOR_CODE % (_LIGHT_CODE, 36)
    WHITE = _ANSI_COLOR_CODE % (_LIGHT_CODE, 37)

    _COLORS_LIST = ['dark_red', 'dark_green', 'dark_yellow', 'dark_blue', 'dark_purple', 'dark_cyan', 'grey', 'red',
                    'green', 'yellow', 'blue', 'purple', 'cyan', 'white']

    _ANSI_COLOR_LENGTH = len(WHITE)

    def __init__(self, writer, colors: bool = True, width_limit: bool = True):
        """
        Initializes the printer with the given writer.

        :param writer: The writer to use (for example - IPythonWriter, or DefaultWriter).
        :param colors: If False, no colors will be printed.
        :param width_limit: If True, printing width will be limited by console width.
        """
        self._writer = writer
        self._in_line = False
        self._colors = colors
        self._width_limit = width_limit
        self._last_position = 0
        self._is_first_line = False
        self._indents = []
        self.indents_sum = 0

    def group(self, indent: int = DEFAULT_INDENT, add_line: bool = True) -> _TextGroup:
        """
        Returns a context manager which adds an indentation before each line.

        :param indent: Number of spaces to print.
        :param add_line: If True, a new line will be printed after the group.
        :return: A TextGroup context manager.
        """
        return _TextGroup(self, indent, add_line)

    def _split_lines(self, original_lines: List[str]) -> List[str]:
        """
        Splits the original lines list according to the current console width and group indentations.

        :param original_lines: The original lines list to split.
        :return: A list of the new width-formatted lines.
        """
        console_width = get_console_width()
        # We take indent into account only in the inner group lines.
        max_line_length = console_width - len(self.LINE_SEP) - self._last_position - \
            (self.indents_sum if not self._is_first_line else self.indents_sum - self._indents[-1])

        lines = []
        for i, line in enumerate(original_lines):
            fixed_line = []
            colors_counter = 0
            line_index = 0
            while line_index < len(line):
                c = line[line_index]

                # Check if we're in a color block.
                if self._colors and c == self._ANSI_COLOR_PREFIX and \
                        len(line) >= (line_index + self._ANSI_COLOR_LENGTH):
                    current_color = line[line_index:line_index + self._ANSI_COLOR_LENGTH]
                    # If it really is a color, skip it.
                    if self._ANSI_REGEXP.match(current_color):
                        line_index += self._ANSI_COLOR_LENGTH
                        fixed_line.extend(list(current_color))
                        colors_counter += 1
                        continue
                fixed_line.append(line[line_index])
                line_index += 1

                # Create a new line, if max line is reached.
                if len(fixed_line) >= max_line_length + (colors_counter * self._ANSI_COLOR_LENGTH):
                    # Special case in which we want to split right before the line break.
                    if len(line) > line_index and line[line_index] == self.LINE_SEP:
                        continue
                    line_string = ''.join(fixed_line)
                    if not line_string.endswith(self.LINE_SEP):
                        line_string += self.LINE_SEP
                    lines.append(line_string)
                    fixed_line = []
                    colors_counter = 0
                    self._last_position = 0
                    # Max line length has changed since the last position is now 0.
                    max_line_length = console_width - len(self.LINE_SEP) - self.indents_sum
                    self._is_first_line = False

            if len(fixed_line) > 0:
                fixed_line = ''.join(fixed_line)
                # If this line contains only color codes, attach it to the last line instead of creating a new one.
                if len(fixed_line) == self._ANSI_COLOR_LENGTH and self._ANSI_REGEXP.match(fixed_line) is not None and \
                        len(lines) > 0:
                    lines[-1] = lines[-1][:-1] + fixed_line
                else:
                    lines.append(fixed_line)
        return lines

    def write(self, text: str):
        """
        Prints text to the screen.
        Supports colors by using the color constants.
        To use colors, add the color before the text you want to print.

        :param text: The text to print.
        """
        # Default color is NORMAL.
        last_color = (self._DARK_CODE, 0)
        # We use splitlines with keepends in order to keep the line breaks.
        # Then we split by using the console width.
        original_lines = text.splitlines(True)
        lines = self._split_lines(original_lines) if self._width_limit else original_lines

        # Print the new width-formatted lines.
        for line in lines:
            # Print indents only at line beginnings.
            if not self._in_line:
                self._writer.write(' ' * self.indents_sum)
            # Remove colors if needed.
            if not self._colors:
                for color_code in self._ANSI_REGEXP.findall(line):
                    line = line.replace(self._ANSI_COLOR_CODE % (color_code[0], int(color_code[1])), '')
            elif not self._ANSI_REGEXP.match(line):
                # Check if the line starts with a color. If not, we apply the color from the last line.
                line = self._ANSI_COLOR_CODE % (last_color[0], int(last_color[1])) + line
            # Print the final line.
            self._writer.write(line)
            # Update the in_line status.
            self._in_line = not line.endswith(self.LINE_SEP)
            # Update the last color used.
            if self._colors:
                last_color = self._ANSI_REGEXP.findall(line)[-1]

        # Update last position (if there was no line break in the end).
        if len(lines) > 0:
            last_line = lines[-1]
            if not last_line.endswith(self.LINE_SEP):
                # Strip the colors to figure out the real number of characters in the line.
                if self._colors:
                    for color_code in self._ANSI_REGEXP.findall(last_line):
                        last_line = last_line.replace(self._ANSI_COLOR_CODE % (color_code[0], int(color_code[1])), '')
                self._last_position += len(last_line)
            else:
                self._last_position = 0
                self._is_first_line = False
        else:
            self._last_position = 0

        # Reset colors for the next print.
        if self._colors and not text.endswith(self.NORMAL):
            self._writer.write(self.NORMAL)

    def write_line(self, text: str = ''):
        """
        Prints a line of text to the screen.
        Uses the write method.

        :param text: The text to print.
        """
        self.write(text + self.LINE_SEP)

    def write_aligned(self, key: str, value: str, not_important_keys: Optional[List[str]] = None,
                      is_list: bool = False, align_size: Optional[int] = None, key_color: str = PURPLE,
                      value_color: str = GREEN, dark_key_color: str = DARK_PURPLE, dark_value_color: str = DARK_GREEN,
                      separator: str = SEPARATOR):
        """
        Prints keys and values aligned to align_size.

        :param key: The name of the property to print.
        :param value: The value of the property to print.
        :param not_important_keys: Properties that will be printed in a darker color.
        :param is_list: True if the value is a list of items.
        :param align_size: The alignment size to use.
        :param key_color: The key text color (default is purple).
        :param value_color: The value text color (default is green).
        :param dark_key_color: The key text color for unimportant keys (default is dark purple).
        :param dark_value_color: The values text color for unimportant values (default is dark green).
        :param separator: The separator to use (default is ':').
        """
        align_size = align_size or min(32, get_console_width() // 2)
        not_important_keys = not_important_keys or []
        if value is None:
            return
        if isinstance(value, bool):
            value = str(value)
        if key in not_important_keys:
            key_color = dark_key_color
            value_color = dark_value_color

        self.write(key_color + key + separator)
        self.write(' ' * (align_size - len(key) - 1))
        with self.group(indent=align_size):
            if is_list and len(value) > 0:
                self.write_line(value_color + value[0])
                if len(value) > 1:
                    for v in value[1:]:
                        self.write_line(value_color + v)
            elif not is_list:
                self.write_line(value_color + str(value))

    def write_title(self, title: str, title_color: str = YELLOW, hyphen_line_color: str = WHITE):
        """
        Prints title with hyphen line underneath it.

        :param title: The title to print.
        :param title_color: The title text color (default is yellow).
        :param hyphen_line_color: The hyphen line color (default is white).
        """
        self.write_line(title_color + title)
        self.write_line(hyphen_line_color + '=' * (len(title) + 3))

    def __getattr__(self, item: str):
        # Support color function in a generic fashion.
        if item in self._COLORS_LIST:
            def wrapper(text):
                # Color function content will be wrapped, and the rest of the text color will be normal.
                wrapped_text = getattr(self, item.upper()) + text
                # No need to duplicate normal color suffix.
                if not wrapped_text.endswith(self.NORMAL):
                    wrapped_text += self.NORMAL
                return wrapped_text

            return wrapper

        return super().__getattribute__(item)


_printer = None
# Colors won't work on Linux if TERM is not defined.
_colors = os.name == 'nt' or os.getenv('TERM')

# If we're not inside IPython, use pyreadline's console.
if os.name == 'nt' and sys.stdout == sys.__stdout__:
    try:
        assert __IPYTHON__
    except NameError:
        try:
            from pyreadline.console.console import Console

            _printer = Printer(Console())
        except ImportError:
            # If all failed, just print without colors.
            _colors = False


def get_printer(colors: bool = True, width_limit: bool = True, disabled: bool = False) -> Printer:
    """
    Returns an already initialized instance of the printer.

    :param colors: If False, no colors will be printed.
    :param width_limit: If True, printing width will be limited by console width.
    :param disabled: If True, nothing will be printed.
    """
    global _printer
    global _colors
    # Make sure we can print colors if needed.
    colors = colors and _colors
    # If the printer was never defined before, or the settings have changed.
    if not _printer or (colors != _printer._colors) or (width_limit != _printer._width_limit):
        _printer = Printer(DefaultWriter(disabled=disabled), colors=colors, width_limit=width_limit)
    return _printer


def _get_windows_console_width() -> int:
    """
    A small utility function for getting the current console window's width, in Windows.

    :return: The current console window's width.
    """
    from ctypes import byref, windll
    import pyreadline

    out = windll.kernel32.GetStdHandle(-11)
    info = pyreadline.console.CONSOLE_SCREEN_BUFFER_INFO()
    windll.kernel32.GetConsoleScreenBufferInfo(out, byref(info))
    return info.dwSize.X


def _get_linux_console_width() -> int:
    # Don't run tput if TERM is not defined, to prevent terminal-related errors.
    if os.getenv('TERM'):
        return int(subprocess.check_output(['tput', 'cols']))
    return 0


def _in_qtconsole() -> bool:
    """
    A small utility function which determines if we're running in QTConsole's context.
    """
    try:
        from IPython import get_ipython
        try:
            from ipykernel.zmqshell import ZMQInteractiveShell
            shell_object = ZMQInteractiveShell
        except ImportError:
            from IPython.kernel.zmq import zmqshell
            shell_object = zmqshell.ZMQInteractiveShell
        return isinstance(get_ipython(), shell_object)
    except Exception:
        return False


def get_console_width() -> int:
    """
    A small utility function for getting the current console window's width.

    :return: The current console window's width.
    """
    # Assigning the value once, as frequent call to this function
    # causes a major slow down(ImportErrors + isinstance).
    global _IN_QT
    if _IN_QT is None:
        _IN_QT = _in_qtconsole()

    try:
        if _IN_QT:
            # QTConsole determines and handles the max line length by itself.
            width = sys.maxsize
        else:
            width = _get_windows_console_width() if os.name == 'nt' else _get_linux_console_width()
        if width <= 0:
            return 80
        return width
    except Exception:
        # Default value.
        return 80


__all__ = ['get_printer', 'get_console_width', 'Printer', 'DefaultWriter']
