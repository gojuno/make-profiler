import argparse

from make_profiler.parser import parse

FINAL_TAG = "[FINAL]"


def parse_args():
    parser = argparse.ArgumentParser(description="Geocint Makefile validator")
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


def validate_targets(targets, deps):
    bad_targets = []
    for t, is_final in targets:
        if t not in deps:
            if not is_final:
                bad_targets.append(t)
    return bad_targets


if __name__ == "__main__":
    args = parse_args()

    with open(args.in_filename, "r") as f:
        ast = parse(f)
    targets, deps = parse_targets(ast)
    bad_targets = validate_targets(targets, deps)

    if bad_targets:
        raise ValueError(
            f"Targets {bad_targets} are not allowed to be without dependent targets."
        )
