import time
import os


def parse_timing_db(filename):
    lines = [i.strip().split() for i in open(filename)]
    lines.reverse()
    cur_run_bid = ''
    targets = dict()
    for l in lines:
        if len(l) != 4:
            continue
        target = l[3]
        bid = l[1]
        action = l[2]
        timestamp = float(l[0])

        if not cur_run_bid:
            cur_run_bid = bid

        if target not in targets:
            targets[target] = {
                "current": False,
                "running": False,
                "done": os.path.exists(target),
                "isdir": os.path.isdir(target),
            }

        if bid == cur_run_bid:
            targets[target]["current"] = True
            targets[target][action + "_current"] = timestamp
            if "finish_current" not in targets[target]:
                targets[target]["finish_current"] = float(time.time())
                targets[target]["running"] = True

        if not (bid == cur_run_bid):
            if "prev" not in targets[target] and action == 'finish':
                targets[target]["prev"] = bid
                targets[target][action + "_prev"] = timestamp
            elif action == 'start' and targets[target].get("prev") == bid:
                targets[target][action + "_prev"] = timestamp
    return targets
