#!/usr/bin/python3

import collections
import datetime
import os
import math
from subprocess import Popen, PIPE

def critical_path(influences, dependencies, inputs, timing):
    targets = dict()
    update_queue = list(inputs)
    results = list()

    # forward: early start
    while update_queue:
        t = update_queue.pop(0)
        if t not in targets:
            targets[t] = {"early_start": 0.0}
        if t in timing:
            duration = timing[t].get('timing_sec', 1)
        else:
            duration = 1
        targets[t]["duration"] = duration
        targets[t]["early_end"] = targets[t]["early_start"] + duration
        # add timing tag as hour number from very start
        targets[t]["timing_tag"] = math.ceil(targets[t]["early_end"]/60/10)
        targets[t]["pin_timing_tag"] = True
        for z in influences[t]:
            update_queue.append(z)
            if z not in targets:
                targets[z] = {"early_start": targets[t]["early_end"]}
            else:
                targets[z]["early_start"] = max(targets[z]["early_start"], targets[t]["early_end"])
        if not influences[t]:
            results.append(t)
            # don't pin the final targets to the timeline
            targets[t]["pin_timing_tag"] = False

    # backward: late start
    update_queue = set(results)
    while update_queue:
        t = update_queue.pop()
        if "late_end" not in targets[t]:
            targets[t]["late_end"] = targets[t]["early_end"]
        targets[t]["late_start"] = targets[t]["late_end"] - targets[t]["duration"]
        for d in dependencies.get(t, []):
            for z in d:
                # don't pin timing tags for dependencies if they're at the same tag
                if targets[z]["timing_tag"] == targets[t]["timing_tag"]:
                    targets[z]["pin_timing_tag"] = False
                if z not in update_queue:
                    update_queue.add(z)
                if "late_end" not in targets[z]:
                    targets[z]["late_end"] = targets[t]["late_start"]
                else:
                    targets[z]["late_end"] = min(targets[t]["late_start"], targets[z]["late_end"])

    cp = set()
    timing_tags = {}
    for t, z in targets.items():
        if z["early_start"] == z["late_start"]:
            cp.add(t)
        if z["pin_timing_tag"]:
            if z["timing_tag"] not in timing_tags:
                timing_tags[z["timing_tag"]] = [t]
            else:
                timing_tags[z["timing_tag"]].append(t)

    return cp, timing_tags


def classify_target(name, influences, dependencies, inputs, order_only):
    group = ''
    if name not in dependencies:
        group = 'cluster_not_implemented'
    elif name in inputs:
        if influences:
            group = 'cluster_inputs'
        else:
            if name in order_only:
                group = 'cluster_order_only'
            else:
                group = 'cluster_tools'
    elif not influences:
        group = 'cluster_result'
    return group


def dot_node(name, performance, docstring, cp):
    node = {'label': name, 'fontsize': 10, 'color': 'black', 'fillcolor': '#d3d3d3'}
    if name in performance:
        target_performance = performance[name]
        if target_performance['done']:
            node['fillcolor'] = '.7 .3 1.0'
            if target_performance['isdir']:
                node['fillcolor'] = '.2 .3 1.0'
        if target_performance['failed']:
            node['fillcolor'] = '.05 .3 1.0'
        timing_sec = target_performance.get('timing_sec', 0)
        timing = str(datetime.timedelta(seconds=int(timing_sec)))
        if 'log' in target_performance:
            node['URL'] = target_performance['log']
        if timing != '0:00:00':
            node['label'] += '\\n%s\\r' % timing
            node['fontsize'] = min(max(timing_sec ** .5, node['fontsize']), 150)
    if name in cp:
        node['color'] = '#cc0000'
    node['group'] = '/'.join(name.split('/')[:2])
    node['shape'] = 'box'
    node['style'] = 'filled'
    # generate title as target name when docstring is empty
    node['tooltip'] = docstring if docstring else name
    if name[-4:] == '.png' and os.path.exists(name):
        node['image'] = name
        node['imagescale'] = 'true'
        node['width'] = '1'
    node = ','.join(['%s="%s"' % (k, v) for k, v in node.items()])
    return '"%s" [%s]' % (name, node)


def export_dot(f, influences, dependencies, order_only, performance, indirect_influences, docs):
    f.write("""
digraph G {
    rankdir="BT"
    ratio=0.5625
    node [shape="box"]
    newrank=true
""")
    groups = collections.defaultdict(set)

    # look for keys that aren't linked
    inputs = set(influences.keys())
    for k, v in influences.items():
        for t in v:
            inputs.discard(t)

    cp, timing_tags = critical_path(influences, dependencies, inputs, performance)

    # cluster labels
    labels = {
        'cluster_inputs': 'Input',
        'cluster_result': 'Result',
        'cluster_not_implemented': 'Not implemented',
        'cluster_order_only': 'Order only',
        'cluster_tools': 'Tools'
    }

    hidden_nodes = []

    for target, infls in influences.items():
        group = classify_target(target, infls, dependencies, inputs, order_only)
        groups[group].add(target)

    for k, v in sorted(groups.items()):
        label = ''
        if k in labels:
            label = 'label="%s"' % labels[k]

        nodes = [dot_node(t, performance, docs.get(t, t), cp) for t in v]
        nodes.append('\"%s_DUMMY\" [shape=point style=invis]' % k)
        if k == 'cluster_result':
            nodes.append('rank=sink;')
        #if k == 'cluster_inputs':
            #nodes.append('rank=source;')
        if k == 'cluster_tools':
            nodes.append('rank=source;')
        if k == 'cluster_order_only':
            hidden_nodes = v
            continue

            nodes.append('style=invis;')


        f.write('subgraph "%s" { %s graph[style=dotted] %s }\n' % (k, label, ';\n'.join(nodes)))

    for k, v in influences.items():
        for t in sorted(v):
            if t in indirect_influences[k]:
                f.write('"%s" -> "%s" [color="#00000033",weight="0",style="dashed"];\n' % (k, t))
            elif k in cp and t in cp:
                f.write('"%s" -> "%s" [color="#cc0000",weight="10",penwidth="3",headclip="true"];\n' % (k, t))
            else:
                f.write('"%s" -> "%s";\n' % (k, t))

    f.write('cluster_inputs_DUMMY -> cluster_tools_DUMMY -> cluster_result_DUMMY [ style=invis ];')

    if 'cluster_not_implemented' in groups:
        f.write('cluster_inputs_DUMMY -> cluster_not_implemented_DUMMY -> cluster_tools_DUMMY [ style=invis ];')
        f.write('cluster_not_implemented_DUMMY -> cluster_order_only_DUMMY [ style=invis ];')

    def format_deciminutes(k):
        hrs = math.floor(k / 6)
        min = (k %6)*10
        return '%s:%02d'%(hrs,min)

    for k,v in timing_tags.items():
        f.write('{ rank=same; ' + '%s [label="%s"]'%(k,format_deciminutes(k)) + ' [fontsize=50];' + ';'.join(['"%s"' % t for t in v if t not in hidden_nodes]) + '}')
    tags = sorted(timing_tags.keys())

    f.write('->'.join([ '%s' % k  for k in tags]))

    f.write('}')


def render_dot(dot_fd, image_filename):
    unflatten = Popen('unflatten', stdin=PIPE, stdout=PIPE)
    dot = Popen(['dot', '-Tsvg'], stdin=unflatten.stdout, stdout=PIPE)
    unflatten.stdin.write(dot_fd.read().encode('utf-8'))
    unflatten.stdin.close()
    unflatten.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    svg, _ = dot.communicate()
    svg = svg.replace(b'svg width', b'svg disabled-width').replace(b'height', b'disabled-height')
    open(image_filename, 'wb').write(svg)
