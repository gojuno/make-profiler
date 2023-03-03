import argparse
import io
import logging
import subprocess
import sys
import tempfile
from datetime import datetime

from make_profiler.dot_export import export_dot, render_dot
from make_profiler.parser import parse, get_dependencies_influences
from make_profiler.preprocess import generate_makefile
from make_profiler.timing import parse_timing_db
from make_profiler.report_export import export_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('make_profiler')


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Advanced Makefile processor')
    parser.add_argument(
        '--preprocess_only',
        dest='preprocess_only',
        action='store_true',
        help='Preprocess only')
    parser.add_argument(
        '-f',
        action='store',
        dest='in_filename',
        type=str,
        default='Makefile',
        help='Makefile to read (default %(default)s)')
    parser.add_argument(
        '-fD',
        action='store',
        dest='dot_filename',
        type=str,
        default='dot_file',
        help='dot file debug (default %(default)s)')
    parser.add_argument(
        '-db',
        action='store',
        dest='db_filename',
        type=str,
        default='make_profile.db',
        help='Profile with timings')
    parser.add_argument(
        '-p',
        action='store',
        dest='svg_filename',
        type=str,
        default='make.svg',
        help='rendered report image filename (default: make.svg)')
    parser.add_argument(
        '-a',
        action='store',
        dest='after_date',
        type=datetime.fromisoformat,
        default=None,
        help='Render report image with full target time only after the specified date in iso format (other targets will have a time of 1s)')
    parser.add_argument(
        '--disable_loop_detection',
        dest='disable_loop_detection',
        action='store_false',
        help='Disable cycle detection for include instructions')
    parser.add_argument(
        '--include_depth',
        action='store',
        dest='include_depth',
        type=int,
        default=20,
        help='Depth of the nesting includes')

    parser.add_argument('target', nargs='?')

    args, unknown_args = parser.parse_known_args(argv)

    in_file = open(args.in_filename, 'r')
    if args.preprocess_only:
        out_file = io.StringIO()
    else:
        out_file = tempfile.NamedTemporaryFile(mode='w+')

    ast = parse(in_file, args.disable_loop_detection, args.include_depth)
    generate_makefile(ast, out_file, args.db_filename)
    out_file.flush()

    if args.preprocess_only:
        print(out_file.getvalue())
        return

    if args.target is not None:
        cmd = ['make'] + unknown_args + ['-f', out_file.name, args.target]
        logger.info(' '.join(cmd))
        subprocess.call(cmd)

    docs = dict([
        (i[1]['target'], i[1]['docs'])
        for i in ast if i[0] == 'target'
    ])
    performance = parse_timing_db(args.db_filename, args.after_date)
    deps, influences, order_only, indirect_influences = get_dependencies_influences(ast)

    dot_file = io.StringIO()

    export_dot(
        dot_file,
        influences,
        deps,
        order_only,
        performance,
        indirect_influences,
        docs
    )
    dot_file.seek(0)
    with open(args.dot_filename, 'w') as fd:
        print(dot_file.getvalue(), file=fd)

    render_dot(
        dot_file,
        args.svg_filename
    )

    export_report(
        performance,
        docs,
        influences.keys()
    )


if __name__ == '__main__':
    main()
