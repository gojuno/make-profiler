import os
import logging
import shutil


def rm_node(node):
    if not os.path.exists(node):
        return
    logging.info('removing %s', node)
    if os.path.isdir(node):
        shutil.rmtree(node)
    else:
        os.remove(node)


def clean_target(t, deps):
    if t not in deps:
        return
    for sub_t in deps[t]:
        rm_node(sub_t)
        clean_target(sub_t, deps)
