from colorama import Style, Fore
from lang.span import Span

CONTEXT_LINES = 2


def render(source: str, span: Span, message: str, path: str = "") -> str:
    lines = source.split("\n")
    line, column = span.location(source)

    first = max(1, line - CONTEXT_LINES)
    last = min(len(lines), line + CONTEXT_LINES)
    width = len(str(last))

    out = [
        f"{Fore.RED}{Style.BRIGHT}error{Fore.WHITE}{Style.NORMAL}: {message}",
        f"{Fore.CYAN}{' ' * width}--> {Style.RESET_ALL}{path}:{line}:{column}",
        f"{Fore.CYAN}{' ' * width} |{Style.RESET_ALL}",
    ]

    for number in range(first, last + 1):
        text = lines[number - 1].rstrip("\r").replace("\t", " ")
        gutter = f"{Fore.CYAN}{str(number).rjust(width)} |{Style.RESET_ALL}"

        if number == line:
            col = column - 1
            length = max(1, min(span.end - span.start, len(text) - col))
            highlighted = (
                text[:col]
                + f"{Fore.RED}{Style.BRIGHT}{text[col:col + length]}{Style.RESET_ALL}"
                + text[col + length:]
            )
            out.append(f"{gutter} {highlighted}")
            out.append(
                f"{Fore.CYAN}{' ' * width} |{Style.RESET_ALL} "
                f"{' ' * col}{Fore.RED}{Style.BRIGHT}{'^' * length}{Style.RESET_ALL}"
            )
        else:
            out.append(f"{gutter} {text}")

    return "\n".join(out)
