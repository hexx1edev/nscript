from enum import Enum


class TokenKind(Enum):
    Keyword = 1
    Identifier = 2
    LParen = 3
    RParen = 4
    Operator = 5
    LBrace = 6
    RBrace = 7
    Number = 8
    Semicolon = 9

class Token:
    kind: TokenKind

    def __init__(self, kind: TokenKind) -> None:
        self.kind = kind

    def __repr__(self) -> str:
        return self.kind.name

    def name(self) -> str:
        return self.kind.name

    def value(self) -> None:
        pass

class Keyword(Token):
    keyword: str

    def __init__(self, keyword: str) -> None:
        super().__init__(TokenKind.Keyword)
        self.keyword = keyword

    def __repr__(self) -> str:
        return f"Keyword({self.keyword})"

    def name(self) -> str:
        return "keyword"

    def value(self) -> str:
        return self.keyword

class Identifier(Token):
    ident: str

    def __init__(self, ident: str) -> None:
        super().__init__(TokenKind.Identifier)
        self.ident = ident

    def __repr__(self) -> str:
        return f"Identifier({self.ident})"

    def name(self) -> str:
        return "identifier"

    def value(self) -> str:
        return self.ident

class LParen(Token):
    def __init__(self) -> None:
        super().__init__(TokenKind.LParen)

    def name(self) -> str:
        return "left parenthesis"

    def value(self) -> None:
        return None

    # doesn't need to override __repr__ as it will be the same

class RParen(Token):
    def __init__(self) -> None:
        super().__init__(TokenKind.RParen)

    def name(self) -> str:
        return "right parenthesis"

    def value(self) -> None:
        return None

    # doesn't need to override __repr__ as it will be the same

class Operator(Token):
    operator: str

    def __init__(self, operator: str) -> None:
        super().__init__(TokenKind.Operator)
        self.operator = operator

    def __repr__(self) -> str:
        return f"Operator({self.operator})"

    def name(self) -> str:
        return "operator"

    def value(self) -> str:
        return self.operator

class LBrace(Token):
    def __init__(self) -> None:
        super().__init__(TokenKind.LBrace)

    def name(self) -> str:
        return "left bracket"

    def value(self) -> None:
        return None

    # doesn't need to override __repr__ as it will be the same

class RBrace(Token):
    def __init__(self) -> None:
        super().__init__(TokenKind.RBrace)

    def name(self) -> str:
        return "right bracket"

    def value(self) -> None:
        return None

    # doesn't need to override __repr__ as it will be the same

class Number(Token):
    number: int

    def __init__(self, number: int) -> None:
        super().__init__(TokenKind.Number)
        self.number = number

    def __repr__(self) -> str:
        return f"Number({self.number})"

    def name(self) -> str:
        return "number"

    def value(self) -> int:
        return self.number

class Semicolon(Token):
    def __init__(self) -> None:
        super().__init__(TokenKind.Semicolon)

    def name(self) -> str:
        return "semicolon"

    def value(self) -> None:
        return None

    # doesn't need to override __repr__ as it will be the same