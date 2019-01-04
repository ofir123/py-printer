import sys
import time
from typing import List, Optional

from pyprinter import get_console_width

"""
Code taken from the "progressbar" and "progressbar33" packages.

Helps to display progress meters.

A progress meter instance should be able to:
1) Init with total.
2) Eval with current.
3) Inc from current.
4) Finish.

Behavior:
- Method `eval` returns a string with the progress meter.
- Method `inc` behaves the same but uses internal counter.
- Current range is 0 to (`total`-1).
- Some progress meters can be initialized without `total`, in that case they will display what they know.
- When working without `total`, call `eval` with no parameters to affect the animation.
- Method `finish` brings the progress bar to 100%.

Example:
    # Count lines in files.
    file_names = [...]
    n_lines = 0

    # Using a progress bar.
    from pyprinter import ProgressBar

    progress = ProgressBar(len(file_names))
    for i in range(len(file_names)):
        n_lines += len(open(file_names[i]).readlines())
        progress.eval(i)
    progress.finish()

    # Go down one line.
    print()
    # Print the summary.
    print('counted {} lines.'.format(n_lines))
"""


class Frames:
    pinwheel = ('-', '\\', '|', '/', '-', '\\', '|', '/')
    pacman = ('(', '(', 'C', 'C', 'G', 'C', 'C')
    sticks = ('\\/', '||', '/\\', '||')
    ping = (
        r"|        ",
        r" /       ",
        r"  -      ",
        r"   \     ",
        r"    |    ",
        r"     /   ",
        r"      -  ",
        r"       \ ",
        r"        |",
        r"       \ ",
        r"      -  ",
        r"     /   ",
        r"    |    ",
        r"   \     ",
        r"  -      ",
        r" /       ",
    )


class Bar:
    def __init__(self, total: int, width: int = 20, before: str = '-', after: str = '#'):
        self.total = total
        self.width = width
        self.after = after
        self.before = before

    def eval(self, current: int) -> str:
        # Number of 'after' characters.
        num_after = current * self.width // self.total
        # Shouldn't pass the width.
        num_after = min(num_after, self.width)
        bar = num_after * self.after + (self.width - num_after) * self.before
        return bar


class Percentage:
    def __init__(self, total: int):
        self.total = total

    def eval(self, current: int) -> str:
        percent = current * 100 // self.total
        return f'{percent:3}%'


class Animated:
    # The number of eval calls it takes to switch animation frame.
    _N_PER_CYCLE = 100

    def __init__(self, total: Optional[int] = None, frames: List[str] = Frames.pinwheel,
                 n_per_cycle: Optional[int] = None):
        if n_per_cycle is None:
            n_per_cycle = total // 10 if total is not None else self._N_PER_CYCLE
        self.n_per_cycle = n_per_cycle
        self.frames = frames
        # Keep last state for empty eval calls.
        self._last_state = 0

    def eval(self, current: Optional[int]) -> str:
        # Use either the eval input, or the previous saved state.
        if current is not None:
            self._last_state = current
        else:
            self._last_state += 1
            current = self._last_state

        cycle_ratio = (current % self.n_per_cycle) / self.n_per_cycle
        pos = int(round(cycle_ratio * len(self.frames)))
        pos %= len(self.frames)
        return self.frames[pos]


class Timing:
    """
    Timing (how much time has elapsed, how much is left).
    Find the time elapsed since its creation, calculate the average time for
    each "unit", then predict the time left.
    """

    _DEFAULT_FORMAT = 'elapsed: {0:>5s} left: {1:>5s}'

    def __init__(self, total: Optional[int] = None, print_format: str = _DEFAULT_FORMAT):
        self.total = total
        self.print_format = print_format

        # time.strftime output format.
        # Starts with minutes and seconds.
        self.fmt = '%M:%S'
        # Saving the time of the instance's creation.
        self.start_time = None

    def eval(self, current: Optional[int]) -> str:
        # Start measuring time only after the first eval call.
        if not self.start_time:
            self.start_time = time.monotonic()
            elapsed = 0
        else:
            elapsed = time.monotonic() - self.start_time

        time_per_unit = elapsed / current if current is not None and current > 0 else None

        if self.total is not None and time_per_unit is not None:
            remaining = time_per_unit * (self.total - current)
        else:
            remaining = 0

        # Let time.strftime format the seconds as strings.
        # Show only minutes and seconds, so we don't see it's 1970 :-)

        # Add hours if necessary.
        if elapsed >= 3600 or remaining >= 3600:
            self.fmt = '%H:%M:%S'

        elapsed_str = time.strftime(self.fmt, time.gmtime(round(elapsed)))
        if self.total is not None and time_per_unit is not None:
            remaining_str = time.strftime(self.fmt, time.gmtime(round(remaining)))
        else:
            remaining_str = '?'
        return self.print_format.format(elapsed_str, remaining_str)


class Composite:
    """
    A composite of other progress meters.
    """

    def __init__(self, meters: List, print_format: Optional[str] = None):
        self.meters = meters
        if print_format is not None:
            self.print_format = print_format
        else:
            self.print_format = ''
            for i in range(len(meters)):
                self.print_format += '{' + str(i) + '} '
            self.print_format = self.print_format[:-1] + '{' + str(len(meters)) + '}'

    def eval(self, current: Optional[int], message: str = '') -> str:
        res_list = [x.eval(current) for x in self.meters]
        return self.print_format.format(*(res_list + [message]))


class ProgressBar(Composite):
    """
    The default progress bar.
    """

    # The length taken by all the different meters we use.
    _METERS_LEN = 55
    # No printing will be done in the safe margin, to avoid accidental new lines.
    _SAFE_MARGIN = 5

    # Time constants.
    _FIRST_MESSAGE_TIME = 60
    _SECOND_MESSAGE_TIME = 120
    _THIRD_MESSAGE_TIME = 180

    def __init__(self, total=None, verbose=True, show_default_message=True, is_lying=False, n_per_cycle=None):
        """
        Initializes the progress bar.

        :param total: The total amount of units. If None, a general progress bar will be printed.
        :param verbose: If True, the progress bar will be printed to the screen after every eval call.
        :param show_default_message: If True, a default message will be shown next to the progress bar.
        :param is_lying: If True, this is a lying progress bar and you shouldn't believe it!
        :param n_per_cycle: The number of eval calls it takes to switch animation frame.
        """
        self._is_lying = is_lying
        self._verbose = verbose
        self._show_default_message = show_default_message
        self.current = None
        self.total = total
        self._width = get_console_width() - self._METERS_LEN
        self._start_time = None

        if total is not None and total > 0:
            meters = [Bar(total), Percentage(total)]
        else:
            meters = [Animated(n_per_cycle=n_per_cycle)]
        meters.append(Timing(total))
        super().__init__(meters)

    def eval(self, current: Optional[int] = None, message: str = ''):
        if self.total and current is None:
            raise ValueError('Must supply a value for eval!')

        # Start measuring time only after the first eval call.
        if not self._start_time:
            self._start_time = time.monotonic()

        if current is not None:
            self.current = current
            if self.total and current > self.total:
                current = self.total

        if message:
            message = f' ({message})'
        elif self._show_default_message:
            current_time = time.monotonic() - self._start_time
            # Write something comforting.
            if self._is_lying:
                message = ' (It\'s lying!!!)'
            elif current_time > self._THIRD_MESSAGE_TIME:
                message = ' (When will it end?)'
            elif current_time > self._SECOND_MESSAGE_TIME:
                message = ' (Enough already!!)'
            elif current_time > self._FIRST_MESSAGE_TIME:
                message = ' (Still here?)'

        # Format message to fit console width (and add whitespaces to overwrite previous message).
        message = message[:self._width] + ' ' * max(0, self._width - len(message) - self._SAFE_MARGIN)
        # Print the result.
        result = super(ProgressBar, self).eval(current, message)
        if self._verbose:
            print(f'\r{result}', end='')
            sys.stdout.flush()

    def finish(self):
        if self._verbose:
            if self.total and self.total > 0:
                # Get to 100%.
                self.eval(self.total)

            # Finish the line.
            print('')

    def inc(self, amount: int = 1, message: str = ''):
        if amount < 1:
            raise ValueError('Must increment by 1 or more!')

        if self.current is None:
            amount -= 1
            self.current = 0
        self.eval(self.current + amount, message)


class ProgressBarIterator:
    """
    An iterable version of ProgressBar.
    """

    def __init__(self, iterable, total: Optional[int] = None, verbose: bool = True, show_default_message: bool = True,
                 is_lying: bool = False, n_per_cycle: Optional[int] = None):
        """
        Initializes the progress bar iterator.

        :param iterable: The iterable to go over.
        :param total: The total number of iterations (if None, will be extracted from iterator).
        :param verbose: If True, the progress bar will be printed to the screen after every eval call.
        :param show_default_message: If True, a default message will be shown next to the progress bar.
        :param is_lying: If True, this is a lying progress bar and you shouldn't believe it!
        :param n_per_cycle: The number of eval calls it takes to switch animation frame.
        """
        self._iterator = iter(iterable)
        if total or hasattr(iterable, '__len__'):
            total = total or len(iterable)
            self._progress_bar = ProgressBar(total, verbose=verbose, show_default_message=show_default_message,
                                             is_lying=is_lying, n_per_cycle=n_per_cycle)
        else:
            self._progress_bar = ProgressBar(verbose=verbose, show_default_message=show_default_message,
                                             is_lying=is_lying, n_per_cycle=n_per_cycle)

    def __iter__(self):
        return self

    def __next__(self):
        self._progress_bar.inc()
        if self._progress_bar.total and self._progress_bar.total == self._progress_bar.current:
            self._progress_bar.finish()
        return next(self._iterator)
