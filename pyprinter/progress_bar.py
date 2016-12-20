import sys
import time

from pyprinter import get_console_width

"""
Code taken from the "progressbar" and "progressbar33" packages.

Helps to display progress meters.

A progress meter instance should be able to:
1) Init with total.
2) Eval with current.
3) Clear.

Behavior:
- Method `eval` returns a string with the progress meter.
- Current range is 0 to (total-1).
- Some progress meters can be initialized without total, in that case they will display what they know.
- Method `finish` brings the progress bar to 100%.

Example:
    # Count lines in files.
    file_names = [...]
    n_lines = 0

    # Using a progress bar.
    import progress_bars
    meter = progress_bars.Bar(len(file_names))

    for i in range(len(file_names)):
        print('\r{}'.format(meter.eval(i))),
        n_lines += len( open(file_names[i]).readlines() )
    # Go down one line.
    print()
    # Print the summary.
    print('counted {} lines.'.format(n_lines))
"""


class Frames(object):
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


class Bar(object):
    def __init__(self, total, width=20, before='-', after='#'):
        self.total = total
        self.width = width
        self.after = after
        self.before = before

    def eval(self, current):
        # Number of 'after' characters.
        num_after = current * self.width // self.total
        # Shouldn't pass the width.
        num_after = min(num_after, self.width)
        bar = num_after * self.after + (self.width - num_after) * self.before
        return bar


class Percentage(object):
    def __init__(self, total):
        self.total = total

    def eval(self, current):
        percent = current * 100 // self.total
        return '{0:>4s}'.format('%{0}'.format(percent))


class Animated(object):
    def __init__(self, total=None, frames=Frames.pinwheel, n_per_cycle=None):
        if n_per_cycle is None:
            if total is not None:
                n_per_cycle = total // 10
            else:
                n_per_cycle = 1
        self.n_per_cycle = n_per_cycle
        self.frames = frames

    def eval(self, current):
        cycle_ratio = (current % self.n_per_cycle) / self.n_per_cycle
        pos = int(round(cycle_ratio * len(self.frames)))
        pos %= len(self.frames)
        return self.frames[pos]


class Timing(object):
    """
    Timing (how much time has elapsed, how much is left).
    Find the time elapsed since its creation, calculate the average time for
    each "unit", then predict the time left.
    """

    def __init__(self, total=None, print_format='elapsed: {0:>5s} left: {1:>5s}'):
        self.total = total
        self.print_format = print_format

        # time.strftime output format.
        # Starts with minutes and seconds.
        self.fmt = '%M:%S'
        # Saving the time of the instance's creation.
        self.start_time = time.time()

    def eval(self, current):
        elapsed = time.time() - self.start_time
        if current > 0:
            time_per_unit = elapsed / current
        else:
            time_per_unit = None
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


class Composite(object):
    """
    A composite of other progress meters.
    """

    def __init__(self, meters, print_format=None):
        self.meters = meters
        if print_format is not None:
            self.print_format = print_format
        else:
            self.print_format = ''
            for i in range(len(meters)):
                self.print_format += '{' + str(i) + '} '
            self.print_format = self.print_format[:-1] + '{' + str(len(meters)) + '}'

    def eval(self, current, message=''):
        res_list = [x.eval(current) for x in self.meters]
        return self.print_format.format(*(res_list + [message]))


class ProgressBar(Composite):
    """
    The default progress bar.
    """

    # The length taken by all the different meters we use.
    _METERS_LEN = 55

    # Time constants.
    _FIRST_MESSAGE_TIME = 30
    _SECOND_MESSAGE_TIME = 90
    _THIRD_MESSAGE_TIME = 180

    def __init__(self, total=None, verbose=True, is_lying=False):
        """
        Initializes the progress bar.

        :param total: The total amount of units. If None, a general progress bar will be printed.
        :param verbose: If True, the progress bar will be printed to the screen after every eval call.
        :param is_lying: If True, this is a lying progress bar and you shouldn't believe it!
        """
        self._is_lying = is_lying
        self._verbose = verbose
        self.total = total
        self._width = get_console_width() - self._METERS_LEN
        self._start_time = time.time()
        if total is not None and total > 0:
            meters = [Bar(total), Percentage(total)]
        else:
            meters = [Animated(n_per_cycle=10000)]
        meters.append(Timing(total))
        super(ProgressBar, self).__init__(meters)

    def eval(self, current, message=''):
        if current > self.total:
            current = self.total
        # Write something comforting (all messages are of the same size, because of the \r).
        if message:
            message = ' ({0})'.format(message)
        elif time.time() - self._start_time > self._THIRD_MESSAGE_TIME:
            message = ' (When will it end?)'
        elif time.time() - self._start_time > self._SECOND_MESSAGE_TIME:
            message = ' (Enough already!!) '
        elif time.time() - self._start_time > self._FIRST_MESSAGE_TIME:
            message = ' (Still here?)      '
        elif self._is_lying:
            message = ' (It\'s lying!!!)   '
        # Print the result.
        result = super(ProgressBar, self).eval(current, message[:self._width])
        if self._verbose:
            print('\r{0}'.format(result), end='')
            sys.stdout.flush()

    def finish(self):
        if self._verbose and self.total > 0:
            # Get to 100%.
            self.eval(self.total)
            # Finish the line.
            print('')
