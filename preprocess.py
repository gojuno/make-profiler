#!/usr/bin/python3

import sys
import argparse

from lib.parser import parse, Tokens

STUFF_TARGETS = ('stuff',)


def generate_makefile(ast, hooks, fd):
    def clean(value):
        if type(value) is list:
            return '\n'.join(value)
        return ' '.join(map(str.strip, value.split('\n')))

    clean_hooks = dict((k, clean(h)) for k, h in hooks.items())

    def print_body(item, ihooks={}):
        if 'before_block' in ihooks:
            fd.write('\t{}\n'.format(ihooks['before_block']))
        for body_type, body_item in item['body']:
            if body_type == Tokens.expression:
                fd.write('{}\n'.format(body_item))
            else:
                fd.write('\t{} '.format(ihooks.get('before_command')))
                fd.write(body_item)
                fd.write(ihooks.get('after_command', ''))
                fd.write('\n')
        if 'after_block' in ihooks:
            fd.write('\t{}\n'.format(ihooks['after_block']))

    fd.write('{}\n'.format(clean_hooks['start']))
    for item_type, item in ast:
        if item_type == Tokens.expression:
            fd.write('{}\n'.format(item))
        elif item_type == Tokens.target:
            fd.write('{}:'.format(item['target']))
            deps, order_deps = item['deps']
            if deps:
                fd.write(' {}'.format(' '.join(deps)))
            if order_deps:
                fd.write(' | {}'.format(' '.join(order_deps)))
            fd.write('\n')

            if item['target'] in STUFF_TARGETS:
                print_body(item)
            else:
                print_body(item, clean_hooks)


def main(argv):
    options = argparse.ArgumentParser(
        description='advanced Makefile processor')
    options.add_argument(
        '-i',
        action='store',
        dest='in_filename',
        type=str,
        default=None,
        help='Makefile to read (default stdin)')
    options.add_argument(
        '-db',
        action='store',
        dest='db_filename',
        type=str,
        default='make_profile.db',
        help='Profile with timings')
    options.add_argument(
        '-o',
        action='store',
        dest='out_filename',
        type=str,
        default=None,
        help='Makefile to write (default: stdout)')

    args = options.parse_args(argv)

    in_file = open(args.out_filename, 'r') if args.in_filename else sys.stdin
    out_file = open(args.in_filename, 'w') if args.out_filename else sys.stdout

    ast = parse(in_file)

    generate_makefile(
        ast,
        hooks={
            'start':
                'RANDOM_HASH := $(shell hexdump -e \'/1 "%02x"\' -v -n10 < /dev/urandom)\nRUN_DIRECTORY := $(shell pwd)',
            'before_block':
                '\techo | awk "{ print strftime(\\"%s\\"), \\"${RANDOM_HASH}\\", \\"start\\", \\"$@\\"; }" '
                '>> make_profile.db;'
                'mkdir -p ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@',
            'after_block':
                '\techo | awk "{ print strftime(\\"%s\\"), \\"${RANDOM_HASH}\\", \\"finish\\", \\"$@\\"; }" '
                '>> make_profile.db;'
                'ln -s -f -T ${RANDOM_HASH} ${RUN_DIRECTORY}/logs/latest;'
                'touch ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/log.txt',
            'before_command':
                '\t{ ',
            'after_command':
                """ || touch ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/failed.touch ; } 2>&1"""
                """ | gawk '{print strftime("[%Y-%m-%d %H:%M:%S] ",systime()) $$0 }'"""
                """ | tee -a ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/log.txt;"""
                """test ! -e ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/failed.touch"""
        },
        fd=out_file
    )


if __name__ == '__main__':
    main(sys.argv[1:])
