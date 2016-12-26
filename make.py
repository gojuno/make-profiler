import sys
import argparse
import collections
import logging
from clean import clean_target
from timing import parse_timing_db
from dot_export import export_dot
from more_itertools import peekable


class Tokens:
    target = 'target'
    command = 'command'
    expression = 'expression'


STUFF_TARGETS = ('stuff',)


def tokenizer(infile):
    it = enumerate(open(infile))

    def glue_multiline(line):
        lines = []
        strip_line = line.strip()
        while strip_line[-1] == '\\':
            lines.append(strip_line.rstrip('\\').strip())
            line_num, line = next(it)
            strip_line = line.strip()
        lines.append(strip_line.rstrip('\\').strip())
        return ' '.join(lines)

    for line_num, line in it:
        strip_line = line.strip()
        # skip empty lines
        if not strip_line:
            continue
        # skip comments
        if strip_line[0] == '#':
            continue
        elif line[0] == '\t':
            yield (Tokens.command, glue_multiline(line))
        elif ':' in line and '=' not in line:
            yield (Tokens.target, glue_multiline(line))
        else:
            yield (Tokens.expression, line.strip())


def parse_makefile(infile):
    ast = []
    it = peekable(tokenizer(infile))

    def parse_target(token):
        line = token[1]
        target, deps = line.split(':', 1)
        raw_deps = deps.strip().split('|', 1)
        deps = raw_deps[0]
        order_deps = raw_deps[1] if raw_deps[1:] else ''
        body = parse_body()
        ast.append((
            token[0],
            {
                'target': target.strip(),
                'deps': [
                    sorted(deps.split()) if deps else [],
                    list(order_deps.split()) if order_deps else []
                ],
                'body': body
            })
        )

    def parse_body():
        body = []
        try:
            while it.peek()[0] != Tokens.target:
                token = next(it)
                if token[0] == Tokens.command:
                    body.append((token[0], token[1]))
                else:
                    body.append(token)
        except StopIteration:
            pass
        return body

    for token in it:
        if token[0] == Tokens.target:
            parse_target(token)
        else:
            # expression
            ast.append(token)

    return ast


def generate_makefile(ast, hooks, fd=sys.stdout):

    def print_body(item, ihooks={}):
        if 'before_block' in ihooks:
            fd.write('{}\n'.format(ihooks['before_block']))
        for body_type, body_item in item['body']:
            if body_type == Tokens.expression:
                fd.write('{}\n'.format(body_item))
            else:
                fd.write(ihooks.get('before_command', '\t'))
                fd.write(body_item)
                fd.write(ihooks.get('after_command', ''))
                fd.write('\n')
        if 'after_block' in ihooks:
            fd.write('{}\n'.format(ihooks['after_block']))

    fd.write('{}\n'.format(hooks['start']))
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
                print_body(item, hooks)


def get_dependencies_influences(ast):
    dependencies = {}
    influences = collections.defaultdict(set)
    order_only = set()

    for item_t, item in ast:
        if item_t != Tokens.target:
            continue
        target = item['target']
        deps, order_deps = item['deps']

        if target not in ('.PHONY',):
            dependencies[target] = [deps, order_deps]

        # influences
        influences[target]
        for k in deps:
            influences[k].add(target)
        for k in order_deps:
            influences[k]
        order_only.update(order_deps)
    return (dependencies, influences, order_only)


if __name__ == "__main__":
    options = argparse.ArgumentParser(description='advanced Makefile processor')
    options.add_argument(
        '--clean',
        action='store_true',
        help='Targets to process')
    options.add_argument(
        '-f',
        action='store',
        dest='filename',
        type=str,
        default='Makefile_template',
        help='Makefile to read')
    options.add_argument(
        '-o',
        action='store',
        dest='out_filename',
        type=str,
        default='Makefile',
        help='Makefile to write')
    options.add_argument(
        '-db',
        action='store',
        dest='db_filename',
        type=str,
        default='make_profile.db',
        help='Profile with timings')
    options.add_argument(
        'targets',
        default=['all'],
        metavar='target',
        type=str,
        nargs='*',
        help='Targets to process')
    args = options.parse_args()

    ast = parse_makefile(args.filename)

    generate_makefile(ast, {
        'start':
            'RANDOM_HASH := $(shell hexdump -e \'/1 "%02x"\' -v -n10 < /dev/urandom)\nRUN_DIRECTORY := $(shell pwd)',
        'before_block':
            '\techo | awk "{ print strftime(\\"%s\\"), \\"${RANDOM_HASH}\\", \\"start\\", \\"$@\\"; }" >> make_profile.db; mkdir -p ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@',
        'after_block':
            '\techo | awk "{ print strftime(\\"%s\\"), \\"${RANDOM_HASH}\\", \\"finish\\", \\"$@\\"; }" >> make_profile.db; ln -s -f -T ${RANDOM_HASH} ${RUN_DIRECTORY}/logs/latest; touch ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/log.txt',
        'before_command':
            '\t{ ',
        'after_command':
            """ || touch ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/failed.touch ; } 2>&1 | gawk '{print strftime("[%Y-%m-%d %H:%M:%S] ",systime()) $$0 }' | tee -a ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/log.txt; test ! -e ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/failed.touch"""
    }, fd=open(args.out_filename, 'w'))

    performance = parse_timing_db(args.db_filename)
    deps, influences, order_only = get_dependencies_influences(ast)

    export_dot(
        open('make.dot', 'w'),
        influences,
        deps,
        order_only,
        performance
    )

    if args.clean:
        for target in args.targets:
            clean_target(deps, target)
