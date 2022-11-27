import collections
import re
import tempfile
import sys

from enum import Enum
from typing import Any, Dict, Generator, List, Tuple

from more_itertools import peekable


class Tokens(str, Enum):
    target = "target"
    command = "command"
    expression = "expression"


def tokenizer(fd: List[str]) -> Generator[Tuple[Tokens, str], None, None]:
    it = enumerate(fd)

    def glue_multiline(line: str) -> str:
        lines = []
        strip_line = line.strip()
        while strip_line[-1] == '\\':
            lines.append(strip_line.rstrip('\\').strip())
            line_num, line = next(it)
            strip_line = line.strip()
        lines.append(strip_line.rstrip('\\').strip())
        return ' '.join(lines)

    for line_num, line in it:
        strip_line = line.strip()

        # skip empty lines
        if not strip_line:
            continue

        # skip comments, don't skip docstrings
        if strip_line[0] == '#' and line[:2] != '##':
            continue
        elif line[0] == '\t':
            yield (Tokens.command, glue_multiline(line))
        elif ':' in line and '=' not in line:
            yield (Tokens.target, glue_multiline(line))
        else:
            yield (Tokens.expression, line.strip(' ;\t'))


def parse(fd: List[str], is_check_loop: Any, loop_check_depth: int) -> List[Tuple[Tokens, Dict[str, Any]]]:
    ast = []

    def insert_included_files(open_file, is_check_include_loop, loop_check_depth):
        
        # create nested function to check if list of rows cointains include instructions
        def check_for_includes(input_make, regular_expression):
            # create list of rows from input make
            list_of_rows = input_make.split('\n')
            # find rows which consist include instruction and replace multiple spaces with one
            matches = [re.sub(' +', ' ', string) for string in list_of_rows if re.match(regular_expression, string)]

            if len(matches) != 0:
                return True
            else:
                return False

        # create nested function to be able insert included makes recursively
        def replace_include_with_file(input_make, regular_expression):
            # create list of rows from input make
            list_of_rows = input_make.split('\n')
            # iterate through input makefile
            for x in range(0,len(list_of_rows)):
                # check if string contains include instruction
                if re.match(regular_expression, list_of_rows[x]):
                    # get names of makefiles from instruction
                    instruction = re.sub(' +', ' ', list_of_rows[x].split('include ')[1])
                    # split list of included makes to support multiple entrance
                    makes = instruction.split(' ')
        
                    # initialize empty list to store included instructions as string
                    included_instructions = []   
                    # iterate through files from instruction add write them to list
                    for make in makes:
                        with open(make, 'r') as fp:
                            included_instructions.append(fp.read())
        
                    # transform list into single string
                    included_string = '\n'.join(included_instructions)
        
                    # replace include with included instruction 
                    output_make = input_make.replace(list_of_rows[x], included_string, 1)

            return output_make

        make_full_text = open_file.read()

        # compile regex to find include instructions
        regex = re.compile('include +')
        
        loop_detector = 0
        
        # recursively check makefile to check include instruction in included files
        while check_for_includes(make_full_text, regex):
            make_full_text = replace_include_with_file(make_full_text, regex)
            loop_detector += 1
            if loop_detector > loop_check_depth and is_check_include_loop:
                raise Exception('Your make chain is looped or too deep (default depth = 20). if you have nesting depth > 20 please set your value with --include_depth option or turn off loop checking with --disable_loop_detection')

        # create temporary file
        tmp = tempfile.NamedTemporaryFile(mode = 'w+t')

        # open temporary file and write composed make to them
        with open(tmp.name, 'w') as temp_input_file:
            temp_input_file.write(make_full_text)

        # open temporary file as <class '_io.TextIOWrapper'> to support type compatibiluty with tokenizer() 
        temp_make_file = open(tmp.name, 'r')
        
        return temp_make_file


    it = peekable(tokenizer(insert_included_files(fd, is_check_loop, loop_check_depth)))

    def parse_target(token: Tuple[Tokens, str]):
        line = token[1]
        target, deps, order_deps, docstring = re.match(
            r'(.+?): \s? ([^|#]+)? \s? [|]? \s? ([^##]+)? \s?  \s? ([#][#].+)?',
            line,
            re.X
        ).groups()
        body = parse_body()
        ast.append((
            token[0],
            {
                'target': target.strip(),
                'deps': [
                    sorted(deps.strip().split()) if deps else [],
                    sorted(order_deps.strip().split()) if order_deps else []
                ],
                'docs': docstring.strip().strip('#').strip() if docstring else '',
                'body': body
            })
        )

    def next_belongs_to_target() -> bool:
        token, _ = it.peek()
        return token == Tokens.command

    def parse_body() -> List[Tuple[Tokens, str]]:
        body = []
        try:
            while next_belongs_to_target():
                body.append(next(it))
        except StopIteration:
            pass
        return body

    for token in it:
        if token[0] == Tokens.target:
            parse_target(token)
        else:
            # expression
            ast.append(token)

    return ast


def get_dependencies_influences(ast: List[Tuple[Tokens, Dict[str, Any]]]):
    dependencies = {}
    influences = collections.defaultdict(set)
    order_only = set()
    indirect_influences = collections.defaultdict(set)

    for item_t, item in ast:
        if item_t != Tokens.target:
            continue
        target = item['target']
        deps, order_deps = item['deps']

        if target in ('.PHONY',):
            continue

        dependencies[target] = [deps, order_deps]

        # influences
        influences[target]
        for k in deps:
            influences[k].add(target)
        for k in order_deps:
            influences[k]
        order_only.update(order_deps)

    def recurse_indirect_influences(original_target, recurse_target):
        indirect_influences[original_target].update(influences[recurse_target])
        for t in influences[recurse_target]:
            recurse_indirect_influences(original_target, t)

    for original_target, targets in influences.items():
        for t in targets:
            recurse_indirect_influences(original_target, t)

    return dependencies, influences, order_only, indirect_influences
    