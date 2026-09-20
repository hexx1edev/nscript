from lang import ast
from enum import Enum
from lang.token import TokenKind, Token

class ParserErrorKind(Enum):
    InvalidSyntax = 1
    UnexpectedEOF = 2


class ParserError(Exception):
    kind: ParserErrorKind
    value: str
    message: str

    def __init__(
        self,
        kind: ParserErrorKind,
        value: str = "",
        message: str = ""
    ) -> None:
        self.kind = kind
        self.value = value
        self.message = message

    def __str__(self) -> str:
        match self.kind:
            case ParserErrorKind.InvalidSyntax:
                return f"invalid syntax: {self.value}, {self.message}"
            case ParserErrorKind.UnexpectedEOF:
                return "unexpected EOF"

    def __repr__(self) -> str:
        return str(self)


class UnexpectedEOF(ParserError):
    def __init__(self) -> None:
        super().__init__(ParserErrorKind.UnexpectedEOF)


class InvalidSyntax(ParserError):
    def __init__(self, value: str, message: str) -> None:
        super().__init__(
            ParserErrorKind.InvalidSyntax,
            value,
            message
        )


class Parser:
    pos: int
    tokens: list[Token]

    def __init__(self, tokens: list[Token]) -> None:
        self.pos = 0
        self.tokens = tokens

    def peek(self) -> Token:
        if self.pos >= len(self.tokens):
            raise UnexpectedEOF()

        return self.tokens[self.pos]

    def advance(self) -> Token:
        token = self.peek()
        self.pos += 1
        return token

    def expect(
        self,
        kind: TokenKind,
        value: any = None,
        message: str = None,
        advance: bool = True
    ) -> Token:
        token = self.peek()

        if token.kind != kind or (
            value is not None and token.value != value
        ):
            expected = value if value is not None else Token(
                kind, None
            ).name()

            msg = f"expected {expected}"

            if message is not None:
                msg = message

            raise InvalidSyntax(token.value, msg)

        if advance:
            self.advance()

        return token

    def parse(self) -> tuple[ast.Program, ParserError]:
        try:
            return self.parse_program(), None
        except ParserError as error:
            return None, error

    def parse_program(self) -> ast.Program:
        program = ast.Program([])

        while self.pos < len(self.tokens):
            func = self.parse_function()
            program.functions.append(func)

        return program

    def parse_function(self) -> ast.Function:
        func = ast.Function("", "?", [])

        self.expect(TokenKind.Keyword, "fn")

        name = self.expect(
            TokenKind.Identifier,
            message="expected function name"
        )

        func.name = name.value

        self.expect(TokenKind.LParen)
        self.expect(TokenKind.RParen)

        token = self.peek()

        match token.kind:
            case TokenKind.Operator:
                self.expect(TokenKind.Operator, "->")

                ret_type = self.expect(
                    TokenKind.Identifier,
                    message="expected return type"
                )

                func.return_type = ret_type.value

            case TokenKind.LBrace:
                pass

            case _:
                raise InvalidSyntax(
                    token.value,
                    "expected function body"
                )

        self.expect(
            TokenKind.LBrace,
            message="expected function body",
            advance=False
        )

        func.body = self.parse_block()

        return func

    def parse_block(self) -> list[ast.ASTNode]:
        block = []

        self.expect(TokenKind.LBrace, message="expected block")

        while True:
            token = self.peek()

            if token.kind == TokenKind.RBrace:
                self.advance()
                break

            block.append(self.parse_statement())

        return block

    def parse_statement(self) -> ast.ASTNode:
        token = self.peek()

        match token.kind:
            case TokenKind.Keyword:
                match token.value:
                    case "return":
                        return self.parse_return()
                    case "let":
                        return self.parse_let()

        raise InvalidSyntax(
            token.value,
            "expected statement"
        )

    def parse_return(self) -> ast.Return:
        self.expect(TokenKind.Keyword, "return")

        expression = self.parse_expression()
        self.expect(TokenKind.Semicolon)

        return ast.Return(expression)

    def parse_expression(self) -> ast.ASTNode:
        return self.parse_additive()

    def parse_primary(self) -> ast.ASTNode:
        token = self.advance()
        if token.kind == TokenKind.Number:
            return ast.NumberLiteral(token.value)
        if token.kind == TokenKind.Identifier:
            return ast.Identifier(token.value)
        if token.kind == TokenKind.LParen:
            expr = self.parse_expression()
            self.expect(TokenKind.RParen)
            return expr
        raise InvalidSyntax(
            token.value,
            "expected expression"
        )

    def parse_unary(self) -> ast.ASTNode:
        token = self.peek()
        if token.kind == TokenKind.Operator and token.value in ("+", "-"):
            op = self.advance().value
            right = self.parse_unary()

            if isinstance(right, ast.NumberLiteral):
                return ast.NumberLiteral(-right.value if op == "-" else right.value)
            return ast.UnaryOperation(op, right)
        return self.parse_primary()

    def parse_multiplicative(self) -> ast.ASTNode:
        left = self.parse_unary()
        while self.peek().kind == TokenKind.Operator and self.peek().value in ("*", "/", "%"):
            op = self.advance().value
            right = self.parse_unary()
            left = ast.BinaryOperation(left, op, right)
        return left

    def parse_additive(self) -> ast.ASTNode:
        left = self.parse_multiplicative()
        while self.peek().kind == TokenKind.Operator and self.peek().value in ("+", "-"):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = ast.BinaryOperation(left, op, right)
        return left

    def parse_let(self) -> ast.Let:
        self.expect(TokenKind.Keyword, "let")
        name = self.expect(TokenKind.Identifier, message="expected variable name").value
        type = "?"
        value = None

        if self.peek().kind == TokenKind.Colon:
            self.advance()
            type = self.expect(
                TokenKind.Identifier,
                message="expected type"
            ).value

        token = self.peek()
        if token.kind == TokenKind.Operator and token.value == "=":
            self.advance()
            value = self.parse_expression()
        elif type == "?":
            raise InvalidSyntax(
                token.value,
                "expected type annotation or initializer"
            )

        self.expect(TokenKind.Semicolon)

        return ast.Let(name, type, value)
