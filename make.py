import os
import shutil
import argparse
import datetime
from timing import parse_timing_db

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


def get_influences(dependencies, direct=False):
    influences = {}
    order_only = set()
    for name, v in deps.iteritems():
        if name not in influences:
            influences[name] = set([name])
        for k in v[0]:
            if k not in influences:
                influences[k] = set([k])
            influences[k].add(name)
        order_only.update(v[1])

    if not direct:
        changed = True
        while changed:
            changed = False
            for k in influences:
                for l in influences[k].copy():
                    if l in influences:
                        if not influences[l].issubset(influences[k]):
                            changed = True
                            influences[k].update(influences[l])
    else:
        for k in influences:
            influences[k].discard(k)

    return influences, order_only


def export_dot(f, influences, dependencies, order_only, performance):
    def dot_node(name, performance):
        node = {}
        node["label"] = name
        node['fontsize'] = 10
        if name in performance:
            target_performance = performance[name]
            if target_performance["done"]:
                node['color'] = ".7 .3 1.0"
                if target_performance["isdir"]:
                    node['color'] = ".2 .3 1.0"
            timing_sec = 0
            if 'start_prev' in target_performance:
                timing_sec = target_performance["finish_prev"] - target_performance["start_prev"]
            if 'finish_current' in target_performance and 'start_current' in target_performance:
                timing_sec = target_performance["finish_current"] - target_performance["start_current"]
            timing = str(datetime.timedelta(seconds=int(timing_sec)))
            if timing != '0:00:00':
                node["label"] += '\\n%s\\r' % timing
                node['fontsize'] = min(max(timing_sec ** .5, node['fontsize']), 100)
        node['group'] = "/".join(name.split('/')[:2])
        node['shape'] = 'box'
        node['style'] = 'filled'
        if name[-4:] == ".png" and os.path.exists(name):
            node['image'] = name
            node['imagescale'] = 'true'
            node['width'] = '1'
        node = ','.join(['%s="%s"' % (k, v) for k, v in node.iteritems()])
        return '"%s" [%s]' % (name, node)

    f.write("""
digraph G {
    rankdir="BT"
    ratio=0.5625
    node [shape="box"]
""")
    groups = {}

    # look for keys that aren't linked
    inputs = set(influences.keys())
    for k, v in influences.iteritems():
        for t in v:
            inputs.discard(t)

    # cluster labels
    labels = {
        "cluster_inputs": "Input",
        "cluster_result": "Result",
        "cluster_not_implemented": "Not implemented",
        "cluster_order_only": "Order only",
        "cluster_tools": "Tools"
    }

    for key, value in influences.iteritems():
        group = ("_".join(key.split('/', 2)[:2])).replace('.','')
        if key in inputs:
            group = "cluster_inputs"
        if not value:
            group = "cluster_result"
            if key in inputs:
                group = "cluster_tools"
                if key in order_only:
                    group = "cluster_order_only"
        if key not in dependencies:
            group = "cluster_not_implemented"
        if group not in groups:
            groups[group] = []
        groups[group].append(key)
    for k, v in sorted(groups.iteritems()):
        label = ""
        if k in labels:
            label = 'label="%s"' % labels[k]
        nodes = [dot_node(t, performance) for t in v]
        nodes.append("%s_DUMMY [shape=point style=invis]" % k)
        f.write('subgraph "%s" { %s graph[style=dotted] %s }\n' % (k, label, ';\n'.join(nodes)))
    for k, v in influences.iteritems():
        for t in sorted(v):
            f.write('"%s" -> "%s";\n' % (k, t))
    f.write('cluster_inputs_DUMMY -> cluster_tools_DUMMY -> cluster_result_DUMMY [ style=invis ];')
    if 'cluster_not_implemented' in groups:
        f.write('cluster_inputs_DUMMY -> cluster_not_implemented_DUMMY -> cluster_tools_DUMMY [ style=invis ];')
        f.write('cluster_result_DUMMY -> cluster_not_implemented_DUMMY -> cluster_order_only_DUMMY [ style=invis ];')
    f.write('}')


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

performance = parse_timing_db()

deps = instrument_makefile(args.filename, 'Makefile', {
    'start':
        'RANDOM_HASH := $(shell hexdump -e \'/1 "%02x"\' -v -n10 < /dev/urandom)\nRUN_DIRECTORY := pwd',
    'before_block':
        '\techo | awk "{ print strftime(\\"%s\\"), \\"${RANDOM_HASH}\\", \\"start\\", \\"$@\\"; }" >> make_profile.db; mkdir -p ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@',
    'after_block':
        '\techo | awk "{ print strftime(\\"%s\\"), \\"${RANDOM_HASH}\\", \\"finish\\", \\"$@\\"; }" >> make_profile.db; ln -s -f -T ${RANDOM_HASH} ${RUN_DIRECTORY}/logs/latest; touch ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/log.txt',
    'before_command':
    	'\t{ ',
    'after_command':
        """ || touch ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/failed.touch ; } 2>&1 | gawk '{print strftime("[%Y-%m-%d %H:%M:%S] ",systime()) $$0 }' | tee -a ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/log.txt; test ! -e ${RUN_DIRECTORY}/logs/${RANDOM_HASH}/$@/failed.touch"""
})

influences, order_only = get_influences(deps)
influences_direct, order_only = get_influences(deps, True)
export_dot(
    open('make.dot', 'w'),
    influences_direct,
    deps,
    order_only,
    performance)
if args.clean:
    for target in args.targets:
        for t in influences[target]:
            if os.path.exists(t):
                print 'removing', t
                if os.path.isdir(t):
                    shutil.rmtree(t)
                else:
                    os.remove(t)