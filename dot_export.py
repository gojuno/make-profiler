#!/usr/bin/python3

import argparse
import os
import sys
import datetime

import collections
from subprocess import Popen, PIPE

from lib.parser import parse, get_dependencies_influences, Tokens
from lib.timing import parse_timing_db


def classify_target(name, influences, dependencies, inputs, order_only):
    group = ("_".join(name.split('/', 2)[:2])).replace('.', '')
    if name not in dependencies:
        group = "cluster_not_implemented"
    elif name in inputs:
        if influences:
            group = "cluster_inputs"
        else:
            if name in order_only:
                group = "cluster_order_only"
            else:
                group = "cluster_tools"
    elif not influences:
        group = "cluster_result"
    return group


def dot_node(name, performance):
    node = {"label": name, 'fontsize': 10}
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
    node = ','.join(['%s="%s"' % (k, v) for k, v in node.items()])
    return '"%s" [%s]' % (name, node)


def export_dot(f, influences, dependencies, order_only, performance):
    f.write("""
digraph G {
    rankdir="BT"
    ratio=0.5625
    node [shape="box"]
""")
    groups = collections.defaultdict(set)

    # look for keys that aren't linked
    inputs = set(influences.keys())
    for k, v in influences.items():
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

    for target, infls in influences.items():
        group = classify_target(target, infls, dependencies, inputs, order_only)
        groups[group].add(target)

    for k, v in sorted(groups.items()):
        label = ""
        if k in labels:
            label = 'label="%s"' % labels[k]
        nodes = [dot_node(t, performance) for t in v]
        nodes.append("\"%s_DUMMY\" [shape=point style=invis]" % k)
        f.write('subgraph "%s" { %s graph[style=dotted] %s }\n' % (k, label, ';\n'.join(nodes)))

    for k, v in influences.items():
        for t in sorted(v):
            f.write('"%s" -> "%s";\n' % (k, t))

    f.write('cluster_inputs_DUMMY -> cluster_tools_DUMMY -> cluster_result_DUMMY [ style=invis ];')

    if 'cluster_not_implemented' in groups:
        f.write('cluster_inputs_DUMMY -> cluster_not_implemented_DUMMY -> cluster_tools_DUMMY [ style=invis ];')
        f.write('cluster_result_DUMMY -> cluster_not_implemented_DUMMY -> cluster_order_only_DUMMY [ style=invis ];')
    f.write('}')


def render_dot(dot_filename, image_filename):
    unflatten = Popen(["unflatten", dot_filename], stdout=PIPE)
    dot = Popen(["dot", "-Tpng"], stdin=unflatten.stdout, stdout=PIPE)
    unflatten.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    png = dot.communicate()[0]
    open(image_filename, 'wb').write(png)


def main(argv):
    options = argparse.ArgumentParser(
        description='export graph of targets from Makefile')
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
        '-d',
        action='store',
        dest='dot_filename',
        type=str,
        default=None,
        help='dot filename (default: stdout)')
    options.add_argument(
        '-p',
        action='store',
        dest='png_filename',
        type=str,
        default='make.png',
        help='rendered report image filename (default: make.png)')

    args = options.parse_args(argv)

    in_file = open(args.in_filename, 'r') if args.in_filename else sys.stdin
    dot_file = open(args.dot_filename, 'w') if args.dot_filename else sys.stdout

    ast = parse(in_file)

    performance = parse_timing_db(args.db_filename)
    deps, influences, order_only = get_dependencies_influences(ast)

    export_dot(
        dot_file,
        influences,
        deps,
        order_only,
        performance
    )

    render_dot(
        dot_file,
        args.png_filename
    )


if __name__ == '__main__':
    main(sys.argv[1:])
