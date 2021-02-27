import argparse

from make_profiler.parser import parse

FINAL_TAG = "[FINAL]"


def parse_args():
    parser = argparse.ArgumentParser(description="Makefile linter")
    parser.add_argument(
        "--in_filename",
        type=str,
        default="Makefile",
        help="Makefile to read (default %(default)s)",
    )

    return parser.parse_args()


def parse_targets(ast):
    target_data = []
    deps_targets = set()

    for token_type, data in ast:
        if token_type != "target":
            continue
        is_final = FINAL_TAG in data.get("docs", "")
        target_data.append((data["target"], is_final))
        for dep_arr in data["deps"]:
            for item in dep_arr:
                deps_targets.add(item)

    return target_data, deps_targets


def validate_orphan_targets(targets, deps):
    bad_targets = []
    for t, is_final in targets:
        if t not in deps:
            if not is_final:
                bad_targets.append(t)
    return bad_targets


if __name__ == "__main__":
    args = parse_args()
    all_ok = True

    with open(args.in_filename, "r") as f:
        ast = parse(f)
    targets, deps = parse_targets(ast)

    for target in validate_orphan_targets(targets, deps):
        print(target, "is orphan - not marked as [FINAL] and no other target depends on it")
        all_ok = False

    if not all_ok:
        raise ValueError(f"Huston, we have a problem.")
