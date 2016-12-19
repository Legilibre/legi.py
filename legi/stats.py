"""
Compiles stats about a LEGI archive.
"""

from __future__ import division, print_function, unicode_literals

from argparse import ArgumentParser
import json

import libarchive
from lxml import etree


def main(args):

    avg_file_size = 0
    number_of_files = 0
    max_size = 0
    biggest_file = None
    min_size = float('inf')
    smallest_file = None
    roots = {}
    values_count = {
        'META/META_SPEC/META_ARTICLE/ETAT': {},
        'META/META_SPEC/META_ARTICLE/TYPE': {},
        'META/META_COMMUN/ORIGINE': {},
        'META/META_COMMUN/NATURE': {},
    }
    etats_par_dossier = {
        'code_en_vigueur': {},
        'code_non_vigueur': {},
        'TNC_en_vigueur': {},
        'TNC_non_vigueur': {},
    }

    parser = etree.XMLParser()
    with libarchive.file_reader(args.archive) as archive:
        for entry in archive:
            path = entry.pathname
            if path[-1] == '/':
                continue
            number_of_files += 1
            size = entry.size
            avg_file_size += size
            if size > max_size:
                biggest_file = path
                max_size = size
            if size < min_size:
                smallest_file = path
                min_size = size
            for block in entry.get_blocks():
                parser.feed(block)
            xml = parser.close()
            tag = xml.tag
            roots[tag] = roots.get(tag, 0) + 1
            for xpath, values_dict in values_count.iteritems():
                e = xml.find(xpath)
                if e is not None:
                    v = e.text
                    values_dict[v] = values_dict.get(v, 0) + 1
            if tag != 'ARTICLE':
                continue
            d = etats_par_dossier[path.split('/')[3]]
            etat = xml.find('META/META_SPEC/META_ARTICLE/ETAT')
            etat = None if etat is None else etat.text
            d[etat] = d.get(etat, 0) + 1

    avg_file_size /= number_of_files
    biggest_file = {'path': biggest_file, 'size': max_size}
    smallest_file = {'path': smallest_file, 'size': min_size}

    stats = {
        'avg_file_size', 'number_of_files', 'biggest_file', 'smallest_file',
        'roots', 'etats_par_dossier', 'values_count'
    }
    r = {k: v for k, v in locals().items() if k in stats}
    print(json.dumps(r, indent=4, sort_keys=True))


p = ArgumentParser()
p.add_argument('archive')
args = p.parse_args()

main(args)
