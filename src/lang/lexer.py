from lang import token as tok
from lang import keywords, operators
from enum import Enum


class LexerErrorKind(Enum):
    UnexpectedToken = 1
    UnknownSymbol = 2
    InvalidNumber = 3
    InvalidOperator = 4

class LexerError:
    kind: LexerErrorKind
    value: str

    def __init__(self, kind: LexerErrorKind, value: str) -> None:
        self.kind = kind
        self.value = value

    def __repr__(self) -> str:
        match self.kind:
            case LexerErrorKind.UnexpectedToken:
                return f"unexpected token: {self.value}"
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

    def tokenize(self) -> tuple[list[tok.Token], LexerError | None, bool]:
        tokens = []

        while self.pos < len(self.source):
            current = self.current()

            if current.isalpha():
                token, error, ok = self.read_identifier()
                if not ok:
                    return tokens, error, False
                tokens.append(token)
            elif current.isnumeric():
                token, error, ok = self.read_number()
                if not ok:
                    return tokens, error, False
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
                token, error, ok = self.read_operator()
                if not ok:
                    return tokens, error, False
                tokens.append(token)

        return tokens, None, True

    def read_identifier(self) -> tuple[tok.Token | None, LexerError | None, bool]:
        ident = ""

        while self.current().isalnum():
            ident += self.consume()

        if ident in keywords.KEYWORDS:
            return tok.Keyword(ident), None, True
        else:
            return tok.Identifier(ident), None, True

    def read_number(self) -> tuple[tok.Number | None, LexerError | None, bool]:
        num = ""

        while self.current().isnumeric():
            num += self.consume()

        if self.current().isalpha():
            return None, LexerError(LexerErrorKind.InvalidNumber, self.current()), False

        return tok.Number(int(num)), None, True

    def read_operator(self) -> tuple[tok.Operator | None, LexerError | None, bool]:
        op = ""

        while self.current() in operators.BASE:
            op += self.consume()

        if op not in operators.OPERATORS:
            return None, LexerError(LexerErrorKind.InvalidOperator, op), False

        return tok.Operator(op), None, True