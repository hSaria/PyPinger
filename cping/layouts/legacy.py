"""A line-based, non-interactive layout. The "original"."""
import shutil
import time

import cping.layouts


class Layout(cping.layouts.Layout):
    """A line-based, non-interactive layout. The "original"."""
    def __call__(self):
        try:
            # Enable alternate screen buffer
            print('\x1b[?1049h', end='')

            while any([host.is_running() for host in self.hosts]):
                # Move to 1;1
                print('\x1b[H', end='')
                print(self.get_results_table(), end='', flush=True)
                time.sleep(self.protocol.interval / 2)
        finally:
            # Disable alternate screen buffer
            print('\x1b[?1049l', end='')

            # Print the last summary, including any overflowing hosts
            print(self.get_results_table(all_hosts=True), end='')

    def get_results_table(self, all_hosts=False):
        """Returns a table (string) of the hosts' results.

        Args:
            all_hosts (bool): If `False`, table won't exceed screen's height.
        """
        table = ''
        term_size = shutil.get_terminal_size()
        host_padding = max([len(str(x)) for x in self.hosts]) + 1

        for index, host in enumerate(self.hosts):
            # Not printing all hosts and lines limit reached
            if not all_hosts and index >= term_size.lines - 1:
                break

            host_line = format_host(host, host_padding, term_size.columns)

            # Clear to end of line
            table += host_line + '\x1b[K\n'

        # Clear to end of screen
        table += '\x1b[J'

        # Not printing all hosts and some hosts overflowed
        if not all_hosts and len(self.hosts) > term_size.lines - 1:
            overflow = len(self.hosts) - (term_size.lines - 1)
            table += '+{} more'.format(overflow)

        return table


def format_host(host, host_padding, line_width):
    """Returns a line representing a summary of the host's results."""
    # line_width - host - min (8) - avg (8) - max (8) - stdev (8) - pktloss (8)
    host.set_results_length(line_width - host_padding - 8 * 5)
    line = str(host).ljust(host_padding)

    if host.status:
        return line + '   ' + host.status

    for stat in ['min', 'avg', 'max', 'stdev']:
        if host.results_summary[stat] is not None:
            line += ' {:>7.2f}'.format(host.results_summary[stat])
        else:
            line += '     -  '

    if host.results_summary['pktloss'] is not None:
        line += ' {:>5.0%}  '.format(host.results_summary['pktloss'])
    else:
        line += '    -   '

    # Output optimization by only including color markers when the color changes
    last_color = None

    for result in host.results:
        if result['latency'] == -1:
            line += get_color('red', last_color) + '.'
            last_color = 'red'
        else:
            color = 'green' if not result['error'] else 'yellow'
            line += get_color(color, last_color) + '!'
            last_color = color

    # Include a color reset at the end of the line
    return line + get_color('reset')


def get_color(color, last_color=None):
    """Returns the ANSI code for `color`, taking in mind `last_color` to skip
    unnecessary color codes. `color` can be green, red, yellow, and reset"""
    if color != last_color:
        return {
            'green': '\x1b[32m',
            'red': '\x1b[31m',
            'yellow': '\x1b[33m',
            'reset': '\x1b[39m',
        }.get(color, '')

    return ''
