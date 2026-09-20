from lang.token import Token, TokenKind
from lang import defs
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

    def tokenize(self) -> tuple[list[Token], LexerError | None]:
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
                tokens.append(Token(TokenKind.LParen, "("))
                self.next()
            elif current == ")":
                tokens.append(Token(TokenKind.RParen, ")"))
                self.next()
            elif current == "{":
                tokens.append(Token(TokenKind.LBrace, "{"))
                self.next()
            elif current == "}":
                tokens.append(Token(TokenKind.RBrace, "}"))
                self.next()
            elif current == ";":
                tokens.append(Token(TokenKind.Semicolon, ";"))
                self.next()
            elif current == ":":
                tokens.append(Token(TokenKind.Colon, ":"))
                self.next()
            elif current in ("\n", "\r\n", " ", "\t"):
                self.next()
            else:
                token, error = self.read_operator()
                if error is not None:
                    return tokens, error
                tokens.append(token)

        return tokens, None

    def read_identifier(self) -> tuple[Token | None, LexerError | None]:
        ident = ""

        while self.current().isalnum():
            ident += self.consume()

        if ident in defs.KEYWORDS:
            return Token(TokenKind.Keyword, ident), None
        else:
            return Token(TokenKind.Identifier, ident), None

    def read_number(self) -> tuple[Token | None, LexerError | None]:
        num = ""

        while self.current().isnumeric():
            num += self.consume()

        if self.current().isalpha():
            return None, LexerError(LexerErrorKind.InvalidNumber, self.current())

        return Token(TokenKind.Number, int(num)), None

    def read_operator(self) -> tuple[Token | None, LexerError | None]:
        op = ""

        if self.current() not in defs.BASE:
            return (
                None,
                LexerError(
                    LexerErrorKind.UnknownSymbol,
                    self.current()
                )
            )

        while self.current() in defs.BASE:
            op += self.consume()

        if op not in defs.OPERATORS:
            return (
                None,
                LexerError(
                    LexerErrorKind.InvalidOperator,
                    op
                )
            )

        return Token(TokenKind.Operator, op), None