from lang.token import Token, TokenKind
from lang import defs
from lang.span import Span
from enum import Enum


class LexerErrorKind(Enum):
    UnknownSymbol = 1
    InvalidNumber = 2
    InvalidOperator = 3

class LexerError:
    kind: LexerErrorKind
    value: str
    span: Span | None

    def __init__(self, kind: LexerErrorKind, value: str, span: Span | None = None) -> None:
        self.kind = kind
        self.value = value
        self.span = span

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
    
    def peek(self, ahead: bool = False) -> str:
        pos = self.pos
        if ahead:
            pos += 1
        
        if pos >= len(self.source):
            return ""
        return self.source[pos]

    def next(self) -> str:
        self.pos += 1
        return self.peek()

    def consume(self) -> str:
        peek = self.peek()
        self.pos += 1
        return peek

    def tokenize(self) -> tuple[list[Token], LexerError | None]:
        tokens = []

        while self.pos < len(self.source):
            peek = self.peek()

            if peek.isalpha():
                token, error = self.read_identifier()
                if error is not None:
                    return tokens, error
                tokens.append(token)
            elif peek.isnumeric():
                token, error = self.read_number()
                if error is not None:
                    return tokens, error
                tokens.append(token)
            elif peek == "(":
                tokens.append(Token(TokenKind.LParen, "(", Span(self.pos, self.pos + 1)))
                self.next()
            elif peek == ")":
                tokens.append(Token(TokenKind.RParen, ")", Span(self.pos, self.pos + 1)))
                self.next()
            elif peek == "{":
                tokens.append(Token(TokenKind.LBrace, "{", Span(self.pos, self.pos + 1)))
                self.next()
            elif peek == "}":
                tokens.append(Token(TokenKind.RBrace, "}", Span(self.pos, self.pos + 1)))
                self.next()
            elif peek == ";":
                tokens.append(Token(TokenKind.Semicolon, ";", Span(self.pos, self.pos + 1)))
                self.next()
            elif peek == ":":
                tokens.append(Token(TokenKind.Colon, ":", Span(self.pos, self.pos + 1)))
                self.next()
            elif peek == ",":
                tokens.append(Token(TokenKind.Comma, ",", Span(self.pos, self.pos + 1)))
                self.next()
            elif peek in ("\n", "\r\n", " ", "\t"):
                self.next()
            else:
                token, error = self.read_operator()
                if error is not None:
                    return tokens, error
                if token is not None:
                    tokens.append(token)

        return tokens, None

    def skip_comment(self):
        while True:
            if self.pos >= len(self.source):
                break
            peek = self.peek()
            if peek not in ("\n", "\r\n"):
                self.next()
            else:
                break

    def read_identifier(self) -> tuple[Token | None, LexerError | None]:
        start = self.pos
        ident = ""

        while self.peek().isalnum() or self.peek() == "_":
            ident += self.consume()

        if ident in defs.KEYWORDS:
            return Token(TokenKind.Keyword, ident, Span(start, self.pos)), None
        elif ident in defs.BOOLEAN:
            if ident == "true":
                return Token(TokenKind.Boolean, True, Span(start, self.pos)), None
            else:
                return Token(TokenKind.Boolean, False, Span(start, self.pos)), None
        else:
            return Token(TokenKind.Identifier, ident, Span(start, self.pos)), None

    def read_number(self) -> tuple[Token | None, LexerError | None]:
        start = self.pos
        num = ""

        while self.peek().isnumeric():
            num += self.consume()

        if self.peek().isalpha():
            return None, LexerError(
                LexerErrorKind.InvalidNumber,
                self.peek(),
                Span(start, self.pos + 1)
            )

        return Token(TokenKind.Number, int(num), Span(start, self.pos)), None

    def read_operator(self) -> tuple[Token | None, LexerError | None]:
        start = self.pos
        op = ""

        if self.peek() not in defs.BASE:
            return (
                None,
                LexerError(
                    LexerErrorKind.UnknownSymbol,
                    self.peek(),
                    Span(start, start + 1)
                )
            )

        while self.peek() in defs.BASE:
            op += self.consume()

        if op == "//":
            self.skip_comment()
            return None, None

        if op not in defs.OPERATORS:
            return (
                None,
                LexerError(
                    LexerErrorKind.InvalidOperator,
                    op,
                    Span(start, self.pos)
                )
            )

        return Token(TokenKind.Operator, op, Span(start, self.pos)), None