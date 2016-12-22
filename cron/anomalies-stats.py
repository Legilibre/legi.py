# encoding: utf8

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
from math import ceil
import os
import re
from string import Template


self_dir = os.path.dirname(os.path.abspath(__file__))


def columns(l, height=100):
    out = '<p class="columns">'
    maximum = max(d['value'] for d in l)
    last = len(l) - 1
    for i, data in enumerate(l):
        bar_height = str(ceil(data['value'] / maximum * height)) + 'px'
        extra_col_class = 'default-visible' if i == 0 or i == last else ''
        out += (
            '<a class="column ' + extra_col_class + '" href="' + data.get('href', '') + '">'
            '<span class="column-labels">' + str(data['value']) + '</span> '
            '<span class="column-bar" style="height: ' + bar_height + '"></span> '
            '<span class="column-labels">' + data['key'] + '</span>'
            '</a>'
        )
    out += '</p>'
    return out


def main():
    # Collect stats
    fname_re = re.compile(r'^anomalies-([0-9]{8})-[0-9]{6}.txt$')
    stats = []
    files = sorted(os.listdir('.'))
    for fname in files:
        m = fname_re.match(fname)
        if not m:
            print(fname, "doesn't match regexp")
            continue
        day = m.group(1)
        isodate = day[:4] + '-' + day[4:6] + '-' + day[6:]
        with open(fname, 'r') as f:
            n_lines = f.read().count('\n')
        stats.append({'key': isodate, 'value': n_lines, 'href': 'logs/' + fname})

    # Render report
    with open(os.path.join(self_dir, 'anomalies-stats.html')) as f:
        template = Template(f.read())
    print(template.substitute({
        'graph': columns(stats),
        'title': "Anomalies dans la base LEGI",
        'last_fname': files[-1],
        'last_count': stats[-1]['value'],
    }))


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('directory')
    args = p.parse_args()
    os.chdir(args.directory)
    main()
