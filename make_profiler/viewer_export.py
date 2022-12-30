#!/usr/bin/python3
import os
import argparse
import shutil


def parse_args():
    parser = argparse.ArgumentParser(description="Creation of web-dashboard for the make profiler")
    parser.add_argument(
        "-o", "--output-folder",
        type=str,
        required=True,
        action ="store",
        help="Specify the output folder",
    )
    return parser.parse_args()

def main():
    file_list = ["Kontur_logo_main.png", "script_u.js", "searchicon.png", "sorttable.js", "style.css", "favicon.png"]
    args = parse_args()
    output_folder = args.output_folder
    report_folder = os.path.join(os.path.dirname(__file__), output_folder, 'report')
    os.makedirs(report_folder, exist_ok=True )
    data_path = os.path.join(os.path.dirname(__file__), 'report', 'index.html')
    shutil.copy2(data_path, output_folder)

    for file_name in file_list:
        data_path = os.path.join(os.path.dirname(__file__), 'report', file_name)
        shutil.copy2(data_path, report_folder)


if __name__ == '__main__':
    main()