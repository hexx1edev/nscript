from lang import ast, token as tok
from enum import Enum

class ParserErrorKind(Enum):
    InvalidSyntax = 1
    UnexpectedEOF = 2

class ParserError:
    kind: ParserErrorKind
    value: str
    message: str

    def __init__(self, kind: ParserErrorKind, value: str, message: str) -> None:
        self.kind = kind
        self.value = value
        self.message = message

    def __repr__(self) -> str:
        match self.kind:
            case ParserErrorKind.InvalidSyntax:
                return f"invalid syntax: {self.value}, {self.message}"
            case ParserErrorKind.UnexpectedEOF:
                return "unexpected EOF"

class Parser:
    pos: int
    tokens: list[tok.Token]

    def __init__(self, tokens: list[tok.Token]) -> None:
        self.pos = 0
        self.tokens = tokens

    def peek(self) -> tuple[tok.Token | None, ParserError | None]:
        if self.pos >= len(self.tokens):
            return None, ParserError(ParserErrorKind.UnexpectedEOF, "", "")

        return self.tokens[self.pos], None

    def advance(self) -> tuple[tok.Token | None, ParserError | None]:
        token, error = self.peek()
        self.pos += 1
        return token, error

    def expect(self, kind: tok.TokenKind, value: any = None, message: str = None, advance: bool = True) -> tuple[tok.Token | None, ParserError | None]:
        token, error = self.peek()

        if error is None and (token.kind != kind or (value is not None and token.value() != value)):
            suffix = ""
            if value is not None:
                suffix = f" {token.value()}"

            msg = f"expected {token.name()}{suffix}"
            if message is not None:
                msg = message

            return None, ParserError(ParserErrorKind.InvalidSyntax, token.value(), msg)

        if advance:
            self.advance()

        return token, error

    def parse(self) -> tuple[ast.Program | None, ParserError | None]:
        return self.parse_program()

    def parse_program(self) -> tuple[ast.Program | None, ParserError | None]:
        program = ast.Program([])

        while self.pos < len(self.tokens):
            func, error = self.parse_function()
            if error is not None:
                return None, error
            program.functions.append(func)

        return program, None

    def parse_function(self) -> tuple[ast.Function | None, ParserError | None]:
        func = ast.Function("", "?", [])

        _, error = self.expect(tok.TokenKind.Keyword, "fn")
        if error is not None:
            return None, error

        name, error = self.expect(tok.TokenKind.Identifier, message="expected function name")
        if error is not None:
            return None, error

        func.name = name.ident

        # skip parenthesis for now
        _, error = self.expect(tok.TokenKind.LParen)
        if error is not None:
            return None, error
        _, error = self.expect(tok.TokenKind.RParen)
        if error is not None:
            return None, error

        token, error = self.peek()
        if error is not None:
            return None, error

        match token.kind:
            case tok.TokenKind.Operator:
                _, error = self.expect(tok.TokenKind.Operator, "->")
                if error is not None:
                    return None, error

                ret_type, error = self.expect(tok.TokenKind.Identifier, message="expected return type")
                if error is not None:
                    return None, error

                func.return_type = ret_type.ident
            case tok.TokenKind.LBrace:
                pass
            case _:
                return None, ParserError(ParserErrorKind.InvalidSyntax, token.value(), "expected function body")

        _, error = self.expect(tok.TokenKind.LBrace, message="expected function body", advance=False)
        if error is not None:
            return None, error

        block, error = self.parse_block()
        if error is not None:
            return None, error

        func.body = block
        return func, None

    def parse_block(self) -> tuple[list[ast.ASTNode], ParserError | None]:
        block = []

        _, error = self.expect(tok.TokenKind.LBrace, message="expected block", advance=False)
        if error is not None:
            return [], error

        current_level = 0

        while True:
            token, error = self.advance()
            if error is not None:
                return [], error

            if token.kind == tok.TokenKind.LBrace:
                current_level += 1
                if current_level == 1:
                    continue
            elif token.kind == tok.TokenKind.RBrace:
                if current_level == 1:
                    break
                current_level -= 1

            block.append(token)

        return block, None
