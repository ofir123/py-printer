import pytest

from pyprinter import DefaultWriter, printer, Printer


def _prepare_lines(original_lines):
    """
    # Adds the line breaks to each original line.
    """
    new_original_lines = []
    for original_line in original_lines:
        new_original_lines.append(original_line + '\n')
    return new_original_lines


@pytest.fixture
def color_printer(monkeypatch):
    printer_instance = Printer(DefaultWriter(), colors=True)
    monkeypatch.setattr(printer, 'get_console_width', lambda: 80)
    return printer_instance


def test_color_functions(color_printer):
    assert color_printer.yellow('test') == color_printer.YELLOW + 'test' + color_printer.NORMAL
    assert color_printer.red('test' + color_printer.yellow('test')) + 'test' == \
        color_printer.RED + 'test' + color_printer.YELLOW + 'test' + color_printer.NORMAL + 'test'


@pytest.mark.parametrize(('original_lines', 'split_lines'),
                         [(['A' * 79],
                           ['A' * 79]),
                          (['B' * 80],
                           ['B' * 79, 'B']),
                          (['C' * 100, 'D' * 200],
                           ['C' * 79, 'C' * 21, 'D' * 79, 'D' * 79, 'D' * 42]),
                          (['E' * 76 + Printer.YELLOW + 'F' * 100 + Printer.PURPLE + 'G' * 100 + Printer.NORMAL],
                           ['E' * 76 + Printer.YELLOW + 'F' * 3, 'F' * 79, 'F' * 18 + Printer.PURPLE + 'G' * 61,
                            'G' * 39 + Printer.NORMAL])])
def test_split_lines(color_printer, original_lines, split_lines):
    """
    Test all standard split line options (with and without colors).
    """
    original_lines = _prepare_lines(original_lines)
    # Check split.
    for result_line, expected_line in zip(color_printer._split_lines(original_lines), split_lines):
        assert result_line == expected_line + '\n'


@pytest.mark.parametrize(('original_lines', 'split_lines', 'indent_size'),
                         [(['A' * 79],
                           ['A' * 69, 'A' * 10], 10),
                          (['B' * 80],
                           ['B' * 69, 'B' * 11], 10),
                          (['C' * 100, 'D' * 200],
                           ['C' * 59, 'C' * 41, 'D' * 59, 'D' * 59, 'D' * 59, 'D' * 23], 20),
                          (['E' * 76 + Printer.YELLOW + 'F' * 100 + Printer.PURPLE + 'G' * 100 + Printer.NORMAL],
                           ['E' * 74, 'E' * 2 + Printer.YELLOW + 'F' * 72, 'F' * 28 + Printer.PURPLE + 'G' * 46,
                            'G' * 54 + Printer.NORMAL], 5)])
def test_indented_split_lines(color_printer, original_lines, split_lines, indent_size):
    """
    Test all indented split line options (with and without colors).
    """
    original_lines = _prepare_lines(original_lines)
    # Check split.
    with color_printer.group(indent=indent_size):
        for result_line, expected_line in zip(color_printer._split_lines(original_lines), split_lines):
            assert result_line == expected_line + '\n'


@pytest.mark.parametrize(('original_lines', 'split_lines', 'first_indent_size', 'second_indent_size'),
                         [(['A' * 79],
                           ['A' * 64, 'A' * 15], 10, 5),
                          (['B' * 80],
                           ['B' * 67, 'B' * 13], 10, 2),
                          (['C' * 100, 'D' * 200],
                           ['C' * 49, 'C' * 49, 'C' * 2, 'D' * 49, 'D' * 49, 'D' * 49, 'D' * 49, 'D' * 4], 20, 10),
                          (['E' * 76 + Printer.YELLOW + 'F' * 100 + Printer.PURPLE + 'G' * 100 + Printer.NORMAL],
                           ['E' * 69, 'E' * 7 + Printer.YELLOW + 'F' * 62, 'F' * 38 + Printer.PURPLE + 'G' * 31,
                            'G' * 69 + Printer.NORMAL], 5, 5)])
def test_multi_indented_split_lines(color_printer, original_lines, split_lines, first_indent_size, second_indent_size):
    """
    Test all multi indented split line options (with and without colors).
    """
    original_lines = _prepare_lines(original_lines)
    # Check split.
    with color_printer.group(indent=first_indent_size):
        with color_printer.group(indent=second_indent_size):
            for result_line, expected_line in zip(color_printer._split_lines(original_lines), split_lines):
                assert result_line == expected_line + '\n'
