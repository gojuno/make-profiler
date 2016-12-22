import os
import datetime
import collections
import pprint


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
