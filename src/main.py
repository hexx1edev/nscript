from sys import argv
from util.print import eprint
from colorama import just_fix_windows_console
from lang import lexer

def main() -> int:
    just_fix_windows_console()

    if len(argv) != 2:
        eprint(f"usage:{argv[0]} <file>")
        return 1

    source = ""

    try:
        file = open(argv[1], "r")
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

    _lexer = lexer.Lexer(source)

    tokens, error, ok = _lexer.tokenize()

    if not ok:
        eprint(f"tokenization failed: {error}")
        return 1

    print(tokens)

    return 0

if __name__ == "__main__":
    exit(main())