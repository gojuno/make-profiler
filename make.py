import argparse
import collections
import logging
from clean import clean_target
from timing import parse_timing_db
from dot_export import export_dot

commands = []


def instrument_makefile(infile, outfile, hooks={}):
    dependencies = {}
    task_name = ''
    out = open(outfile, 'w')
    prev_line = ''
    if 'start' in hooks:
        print >> out, hooks['start']
    for line in open(infile):
        # empty lines - skip
        if not line.strip():
            continue
        if line.strip()[0] == '#':
            continue

        # multi-line lines - glue
        if line.strip()[-1] == '\\':
            if (prev_line == '') and (line[0] == '\t'):
                prev_line = '\t'
            cur_line = line.strip()
            cur_line = cur_line.rstrip('\\')
            cur_line = cur_line.strip()
            prev_line += cur_line + ' '
            continue
        else:
            line = prev_line + line
            prev_line = ''

        # target body
        if line[0] == '\t':
            if task_name not in ('stuff',):
                print >> out, hooks['before_command'] + line.strip() + hooks['after_command']
            else:
                print >> out, '\t' + line.strip()
        # target names - sort and add to graph
        elif ':' in line and ':=' not in line:

            # final instrumentation for previous target
            if task_name and task_name not in ('stuff',):
                if 'after_block' in hooks:
                    print >> out, hooks['after_block']
            order_only = ""
            task_name, deps = line.split(':', 1)
            if "|" in deps:
                deps, order_only = deps.split('|', 1)
            deps = sorted(deps.split())
            order_only = order_only.split()
            order_only.sort()
            if task_name not in ('.PHONY',):
                dependencies[task_name] = [deps, order_only]
            print >> out, "%s: %s | %s" % (task_name, " ".join(deps), " ".join(order_only))

            # start instrumentation for the target
            if task_name not in ('stuff',):
                if 'before_block' in hooks:
                    print >> out, hooks['before_block']
        # something else: assignment? import? don't touch it.
        else:
            print >> out, line.strip()

    # final instrumentation for last target
    if 'after_block' in hooks:
        print >> out, '\t' + hooks['after_block']
    return dependencies


def get_influences(dependencies):
    influences = collections.defaultdict(set)
    order_only = set()
    for name, (deps, order_deps) in dependencies.iteritems():
        influences[name]
        for k in deps:
            influences[k].add(name)
        for k in order_deps:
            influences[k]
        order_only.update(order_deps)

    return influences, order_only


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
        'targets',
        default=['all'],
        metavar='target',
        type=str,
        nargs='*',
        help='Targets to process')
    args = options.parse_args()

    performance = parse_timing_db('make_profile.db')

    deps = instrument_makefile(
        args.filename,
        'Makefile',
        {
            'start':
                """RANDOM_HASH := $(shell hexdump -e \'/1 "%02x"\' -v -n10 < /dev/urandom)
RUN_DIRECTORY := pwd
SHELL := /bin/bash""",
            'before_block':
                """\techo | awk "{ print strftime(\\"%s\\"), \\"${RANDOM_HASH}\\", \\"start\\", \\"$@\\"; }" >> make_profile.db
\tmkdir -p ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@""",
            'after_block':
                """\techo | awk "{ print strftime(\\"%s\\"), \\"${RANDOM_HASH}\\", \\"finish\\", \\"$@\\"; }" >> make_profile.db
\tln -s -f -T ${RANDOM_HASH} ${RUN_DIRECTORY}/logs/latest
\ttouch ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/log.txt""",
            'before_command':
                """\t{ """,
            'after_command':
                """ || touch ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/failed.touch ; } 2>&1 | gawk '{print strftime("[%Y-%m-%d %H:%M:%S] ",systime()) $$0 }' | tee -a ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/log.txt; test ! -e ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/failed.touch"""
        })

    influences, order_only = get_influences(deps)

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
