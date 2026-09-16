from lang import token as tok
from lang import keywords, operators
from enum import Enum


class LexerErrorKind(Enum):
    UnknownSymbol = 1
    InvalidNumber = 2
    InvalidOperator = 3

class LexerError:
    kind: LexerErrorKind
    value: str

    def __init__(self, kind: LexerErrorKind, value: str) -> None:
        self.kind = kind
        self.value = value

    def __repr__(self) -> str:
        match self.kind:
            case LexerErrorKind.UnknownSymbol:
                return f"unknown symbol: {self.value}"
            case LexerErrorKind.InvalidNumber:
                return f"invalid number: {self.value}"
            case LexerErrorKind.InvalidOperator:
                return f"invalid operator: {self.value}"

class Lexer:
    pos: int
    source: str

    def __init__(self, source: str):
        self.pos = 0
        self.source = source
    
    def current(self) -> str:
        if self.pos >= len(self.source):
            return ""
        return self.source[self.pos]

    def next(self) -> str:
        self.pos += 1
        return self.current()

    def consume(self) -> str:
        current = self.current()
        self.pos += 1
        return current

    def tokenize(self) -> tuple[list[tok.Token], LexerError | None]:
        tokens = []

        while self.pos < len(self.source):
            current = self.current()

            if current.isalpha():
                token, error = self.read_identifier()
                if error is not None:
                    return tokens, error
                tokens.append(token)
            elif current.isnumeric():
                token, error = self.read_number()
                if error is not None:
                    return tokens, error
                tokens.append(token)
            elif current == "(":
                tokens.append(tok.LParen())
                self.next()
            elif current == ")":
                tokens.append(tok.RParen())
                self.next()
            elif current == "{":
                tokens.append(tok.LBrace())
                self.next()
            elif current == "}":
                tokens.append(tok.RBrace())
                self.next()
            elif current == ";":
                tokens.append(tok.Semicolon())
                self.next()
            elif current in ("\n", "\r\n", " ", "\t"):
                self.next()
            else:
                token, error = self.read_operator()
                if error is not None:
                    return tokens, error
                tokens.append(token)

        return tokens, None

    def read_identifier(self) -> tuple[tok.Token | None, LexerError | None]:
        ident = ""

        while self.current().isalnum():
            ident += self.consume()

        if ident in keywords.KEYWORDS:
            return tok.Keyword(ident), None
        else:
            return tok.Identifier(ident), None

    def read_number(self) -> tuple[tok.Number | None, LexerError | None]:
        num = ""

        while self.current().isnumeric():
            num += self.consume()

        if self.current().isalpha():
            return None, LexerError(LexerErrorKind.InvalidNumber, self.current())

        return tok.Number(int(num)), None

    def read_operator(self) -> tuple[tok.Operator | None, LexerError | None]:
        op = ""

        if self.current() not in operators.BASE:
            return (
                None,
                LexerError(
                    LexerErrorKind.UnknownSymbol,
                    self.current()
                )
            )

        while self.current() in operators.BASE:
            op += self.consume()

        if op not in operators.OPERATORS:
            return (
                None,
                LexerError(
                    LexerErrorKind.InvalidOperator,
                    op
                )
            )

        return tok.Operator(op), None