from lang import ast, defs
from enum import Enum
from lang.token import TokenKind, Token
from lang.span import Span

PREFIX_OPERATORS = ("+", "-") + defs.UNARY_OPERATORS

BINARY_PRECEDENCE = {
    "||": 1,
    "^^": 2,
    "&&": 3,
    "<": 4, ">": 4, "<=": 4, ">=": 4, "==": 4, "!=": 4,
    "|": 5,
    "^": 6,
    "&": 7,
    "+": 8, "-": 8,
    "*": 9, "/": 9, "%": 9,
}
UNARY_PRECEDENCE = 10

class ParserErrorKind(Enum):
    InvalidSyntax = 1
    UnexpectedEOF = 2


class ParserError(Exception):
    kind: ParserErrorKind
    value: str
    message: str
    span: Span | None

    def __init__(
        self,
        kind: ParserErrorKind,
        value: str = "",
        message: str = "",
        span: Span | None = None
    ) -> None:
        self.kind = kind
        self.value = value
        self.message = message
        self.span = span

    def __str__(self) -> str:
        match self.kind:
            case ParserErrorKind.InvalidSyntax:
                return f"invalid syntax: `{self.value}`. {self.message}"
            case ParserErrorKind.UnexpectedEOF:
                return "unexpected EOF"

    def __repr__(self) -> str:
        return str(self)


class UnexpectedEOF(ParserError):
    def __init__(self, span: Span | None = None) -> None:
        super().__init__(ParserErrorKind.UnexpectedEOF, span=span)


class InvalidSyntax(ParserError):
    def __init__(self, value: str, message: str, span: Span | None = None) -> None:
        super().__init__(
            ParserErrorKind.InvalidSyntax,
            value,
            message,
            span
        )


class Parser:
    pos: int
    tokens: list[Token]

    def __init__(self, tokens: list[Token]) -> None:
        self.pos = 0
        self.tokens = tokens

    def peek(self, ahead: bool = False) -> Token:
        pos = self.pos + 1 if ahead else self.pos

        if pos >= len(self.tokens):
            raise UnexpectedEOF(self.eof_span())

        return self.tokens[pos]

    def eof_span(self) -> Span:
        if not self.tokens:
            return Span(0, 0)
        end = self.tokens[-1].span.end
        return Span(end, end)

    def prev_span(self) -> Span:
        return self.tokens[self.pos - 1].span

    def advance(self) -> Token:
        token = self.peek()
        self.pos += 1
        return token

    def rewind(self) -> Token:
        token = self.peek()
        self.pos -= 1
        return token

    def next(self) -> Token:
        self.pos += 1
        return self.peek()

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

            raise InvalidSyntax(token.value, msg, token.span)

        if advance:
            self.advance()

        return token

    def parse(self) -> tuple[ast.Program, ParserError]:
        try:
            return self.parse_program(), None
        except ParserError as error:
            return None, error

    def parse_program(self) -> ast.Program:
        program = ast.Program([], span=Span(0, self.eof_span().end))

        while self.pos < len(self.tokens):
            func = self.parse_function()
            program.functions.append(func)

        return program

    def parse_type(self) -> ast.Type:
        start = self.peek()
        const = False
        pointer = False

        if self.peek().kind == TokenKind.Keyword and self.peek().value == "const":
            const = True
            self.advance()

        if self.peek().kind == TokenKind.Operator and self.peek().value == "*":
            pointer = True
            self.advance()

        type_token = self.expect(TokenKind.Identifier, message="expected type")

        return ast.Type(type_token.value, const, pointer, span=start.span.to(type_token.span))

    def parse_function(self) -> ast.Function:
        func = ast.Function("", None, [], [])

        start = self.expect(TokenKind.Keyword, "fn").span

        name = self.expect(
            TokenKind.Identifier,
            message="expected function name"
        )

        func.name = name.value

        self.expect(TokenKind.LParen)

        func.args = self.parse_function_args()

        self.expect(TokenKind.RParen)

        token = self.peek()

        match token.kind:
            case TokenKind.Operator:
                self.expect(TokenKind.Operator, "->")
                func.return_type = self.parse_type()

            case TokenKind.LBrace:
                pass

            case _:
                raise InvalidSyntax(
                    token.value,
                    "expected function body",
                    token.span
                )

        self.expect(
            TokenKind.LBrace,
            message="expected function body",
            advance=False
        )

        func.body = self.parse_block()
        func.span = start.to(self.prev_span())

        return func

    def parse_function_args(self) -> list[ast.Argument]:
        args = []

        if self.peek().kind == TokenKind.RParen:
            return args

        while True:
            name = self.expect(
                TokenKind.Identifier,
                message="expected argument name"
            )
            self.expect(TokenKind.Colon, message="expected type annotation")
            type = self.parse_type()
            args.append(
                ast.Argument(name.value, type, span=name.span.to(type.span))
            )

            token = self.peek()
            if token.kind == TokenKind.Comma:
                self.advance()
            elif token.kind == TokenKind.RParen:
                break
            else:
                raise InvalidSyntax(
                    token.value,
                    "expected comma or right parenthesis",
                    token.span
                )

        return args

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
                    case "if":
                        return self.parse_if()
                    case "while":
                        return self.parse_while()
                    case "break":
                        self.advance()
                        self.expect(TokenKind.Semicolon)
                        return ast.Break()
                    case "continue":
                        self.advance()
                        self.expect(TokenKind.Semicolon)
                        return ast.Continue()
            case TokenKind.Identifier:
                next = self.peek(True)
                match next.kind:
                    case TokenKind.Operator:
                        return self.parse_assignment()
                    case TokenKind.LParen:
                        call = self.parse_func_call()
                        end = self.expect(TokenKind.Semicolon).span
                        call.span = call.span.to(end)
                        return call
            case TokenKind.Operator:
                if token.value == "*" and self.peek(True).kind == TokenKind.Identifier:
                    return self.parse_assignment()


        raise InvalidSyntax(
            token.value,
            "invalid statement",
            token.span
        )

    def parse_dereference(self) -> ast.Dereference:
        start = self.expect(TokenKind.Operator, "*")
        val = self.expect(TokenKind.Identifier)
        return ast.Dereference(ast.Identifier(val.value, span=val.span), span=start.span.to(val.span))

    def parse_return(self) -> ast.Return:
        start = self.expect(TokenKind.Keyword, "return").span

        expression = None
        if self.peek().kind != TokenKind.Semicolon:
            expression = self.parse_expression()
        end = self.expect(TokenKind.Semicolon).span

        return ast.Return(expression, span=start.to(end))

    def parse_expression(self, min_prec: int = 0) -> ast.ASTNode:
        left = self.parse_unary()
        while True:
            token = self.peek()
            if token.kind != TokenKind.Operator or token.value not in BINARY_PRECEDENCE:
                break
            precedence = BINARY_PRECEDENCE[token.value]
            if precedence < min_prec:
                break
            self.advance() # consume operator
            right = self.parse_expression(precedence + 1)
            left = ast.BinaryOperation(left, token.value, right, span=left.span.to(right.span))
        return left

    def parse_unary(self):
        token = self.peek()
        if token.kind == TokenKind.Operator and token.value in ("-", "!"):
            self.next()
            right = self.parse_expression(UNARY_PRECEDENCE)
            return ast.UnaryOperation(token.value, right, span=token.span.to(right.span))
        return self.parse_primary()

    def parse_primary(self):
        token = self.advance()
        if token.kind == TokenKind.Number:
            return ast.NumberLiteral(token.value, span=token.span)
        elif token.kind == TokenKind.Identifier:
            if self.peek().kind == TokenKind.LParen:
                self.rewind()
                return self.parse_func_call()
            return ast.Identifier(token.value, span=token.span)
        elif token.kind == TokenKind.Operator:
            if token.value == "*" and self.peek().kind == TokenKind.Identifier:
                self.rewind()
                return self.parse_dereference()
            elif token.value == "&" and self.peek().kind == TokenKind.Identifier:
                ident = self.advance()
                return ast.Pointer(ident.value, span = token.span.to(ident.span))
        elif token.kind == TokenKind.LParen:
            node = self.parse_expression(0)
            self.expect(TokenKind.RParen)
            return node
        elif token.kind == TokenKind.Boolean:
            return ast.BooleanLiteral(token.value, span=token.span)
        raise InvalidSyntax(
            token.value,
            "expected expression",
            token.span
        )

    def parse_let(self) -> ast.Let:
        type = None
        value = None

        start = self.expect(TokenKind.Keyword, "let").span

        name = self.expect(TokenKind.Identifier, message="expected variable name").value

        if self.peek().kind == TokenKind.Colon:
            self.advance()
            type = self.parse_type()

        token = self.peek()
        if token.kind == TokenKind.Operator and token.value == "=":
            self.advance()
            value = self.parse_expression()
        elif type is None:
            raise InvalidSyntax(
                token.value,
                "expected type annotation or initializer",
                token.span
            )

        end = self.expect(TokenKind.Semicolon).span

        return ast.Let(name, type, value, span=start.to(end))

    def parse_assignment(self) -> ast.Assignment:
        destination = None

        token = self.peek()
        if token.kind == TokenKind.Operator and token.value == "*":
            destination = self.parse_dereference()
        else:
            ident = self.expect(TokenKind.Identifier)
            destination = ast.Identifier(ident.value, span=ident.span)

        op_token = self.expect(TokenKind.Operator)
        op = op_token.value
        if op not in defs.ASSIGN_OPERATORS + ("=",):
            raise InvalidSyntax(
                op,
                "expected assignment operator",
                op_token.span
            )
        source = self.parse_expression()
        end = self.expect(TokenKind.Semicolon).span
        return ast.Assignment(source, op, destination, span=destination.span.to(end))

    def parse_func_call(self) -> ast.FuncCall:
        token = self.expect(TokenKind.Identifier, message="expected function name")
        name = ast.Identifier(token.value, span=token.span)
        call = ast.FuncCall(name, [])

        self.expect(TokenKind.LParen)

        if self.peek().kind != TokenKind.RParen:
            while True:
                call.args.append(self.parse_expression())

                token = self.peek()
                if token.kind == TokenKind.Comma:
                    self.advance()
                elif token.kind == TokenKind.RParen:
                    break
                else:
                    raise InvalidSyntax(
                        token.value,
                        "expected comma or right parenthesis",
                        token.span
                    )

        end = self.expect(TokenKind.RParen).span
        call.span = name.span.to(end)

        return call

    def parse_if(self) -> ast.If:
        start = self.expect(TokenKind.Keyword, "if")
        condition = self.parse_expression()
        block = self.parse_block()
        branches = []
        fallback = []

        has_else = False

        while self.pos < len(self.tokens):
            token = self.peek()
            if token.kind != TokenKind.Keyword or token.value != "else":
                break

            after = self.peek(True)
            if after.kind == TokenKind.Keyword and after.value == "if":
                branches.append(self.parse_else_if())
            elif after.kind == TokenKind.LBrace:
                if has_else:
                    raise InvalidSyntax(
                        token.value,
                        "duplicate else block",
                        token.span
                    )
                has_else = True
                fallback = self.parse_else()
            else:
                raise InvalidSyntax(
                    after.value,
                    "expected either else or else if block",
                    after.span
                )

        return ast.If(
            condition, block, branches, fallback,
            span=start.span.to(self.prev_span())
        )

    def parse_else_if(self) -> ast.ElseIf:
        start = self.expect(TokenKind.Keyword, "else")
        end = self.expect(TokenKind.Keyword, "if")
        condition = self.parse_expression()
        block = self.parse_block()

        return ast.ElseIf(condition, block, span=start.span.to(end.span))

    def parse_else(self) -> list[ast.ASTNode]:
        self.expect(TokenKind.Keyword, "else")
        block = self.parse_block()
        return block

    def parse_while(self) -> ast.While:
        start = self.expect(TokenKind.Keyword, "while")
        condition = self.parse_expression()
        block = self.parse_block()

        return ast.While(condition, block, span=start.span.to(self.prev_span()))