from sys import argv
from util.print import eprint
from util.diagnostic import render
from colorama import just_fix_windows_console
import lang.lexer
import lang.parser
import pprint

def main() -> int:
    just_fix_windows_console()

    if len(argv) != 2:
        eprint(f"usage:{argv[0]} <file>")
        return 1

    source = ""

    try:
        file = open(argv[1])
        source = file.read()
    except FileNotFoundError:
        eprint(f"failed to open `{argv[0]}`: file not found")
        return 1
    except PermissionError:
        eprint(f"failed to open `{argv[0]}`: permission denied")
        return 1
    except OSError as err:
        eprint(f"failed to open `{argv[0]}`: OS error: {err}")
        return 1

    lexer = lang.lexer.Lexer(source)

    tokens, error = lexer.tokenize()
    if error is not None:
        print(render(source, error.span, str(error), argv[1]))
        return 1

    parser = lang.parser.Parser(tokens)

    program, error = parser.parse()
    if error is not None:
        print(render(source, error.span, str(error), argv[1]))
        return 1

    pprint.pprint(program)

    return 0

if __name__ == "__main__":
    exit(main())