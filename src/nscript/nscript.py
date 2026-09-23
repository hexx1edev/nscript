from util.print import eprint
from util.diagnostic import render
from colorama import just_fix_windows_console
import lang.lexer
import lang.parser
import lang.semantic
from backend import codegen, compiler
import argparse
import pprint
import os

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nscript")
    parser.add_argument("source", help="path to the source file")
    parser.add_argument("-o", "--output", default="a.out", help="output file path")
    parser.add_argument("-ast", "--export-ast", help="output file path", action="store_true")
    return parser

def program_name(source: str) -> str:
    return os.path.splitext(os.path.basename(source))[0]

def run() -> int:
    just_fix_windows_console()

    parser = build_parser()
    args = parser.parse_args()

    source = ""

    try:
        with open(args.source, encoding="utf-8") as file:
            source = file.read()
    except FileNotFoundError:
        eprint(f"failed to open `{args.source}`: file not found")
        return 1
    except PermissionError:
        eprint(f"failed to open `{args.source}`: permission denied")
        return 1
    except OSError as err:
        eprint(f"failed to open `{args.source}`: OS error: {err}")
        return 1

    lexer = lang.lexer.Lexer(source)

    tokens, error = lexer.tokenize()
    if error is not None:
        print(render(source, error.span, str(error), args.source))
        return 1

    parser = lang.parser.Parser(tokens)

    program, error = parser.parse()
    if error is not None:
        print(render(source, error.span, str(error), args.source))
        return 1

    errors = lang.semantic.Analyzer(program).analyze()
    for error in errors:
        print(render(source, error.span, str(error), args.source))
    if errors:
        eprint(f"aborting due to {len(errors)} error(s)")
        return 1

    if args.export_ast:
        pprint.pprint(program)
        return 0

    generator = codegen.IRGenerator(program, program_name(args.source))
    module = generator.generate()

    compiler.compile_to_object(module, args.output)

    return 0

