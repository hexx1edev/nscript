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
        return f"{self.kind.name}"

class Keyword(Token):
    keyword: str

    def __init__(self, keyword: str) -> None:
        super().__init__(TokenKind.Keyword)
        self.keyword = keyword

    def __repr__(self) -> str:
        return f"Keyword({self.keyword})"

class Identifier(Token):
    name: str

    def __init__(self, name: str) -> None:
        super().__init__(TokenKind.Identifier)
        self.name = name

    def __repr__(self) -> str:
        return f"Identifier({self.name})"

class LParen(Token):
    def __init__(self) -> None:
        super().__init__(TokenKind.LParen)

    # doesn't need to override __repr__ as it will be the same

class RParen(Token):
    def __init__(self) -> None:
        super().__init__(TokenKind.RParen)

    # doesn't need to override __repr__ as it will be the same

class Operator(Token):
    operator: str

    def __init__(self, operator: str) -> None:
        super().__init__(TokenKind.Operator)
        self.operator = operator

    def __repr__(self) -> str:
        return f"Operator({self.operator})"

class LBrace(Token):
    def __init__(self) -> None:
        super().__init__(TokenKind.LBrace)

    # doesn't need to override __repr__ as it will be the same

class RBrace(Token):
    def __init__(self) -> None:
        super().__init__(TokenKind.RBrace)

    # doesn't need to override __repr__ as it will be the same

class Number(Token):
    number: int

    def __init__(self, number: int) -> None:
        super().__init__(TokenKind.Number)
        self.number = number

    def __repr__(self) -> str:
        return f"Number({self.number})"

class Semicolon(Token):
    def __init__(self) -> None:
        super().__init__(TokenKind.Semicolon)

    # doesn't need to override __repr__ as it will be the same