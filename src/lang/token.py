from enum import Enum
from lang.span import Span


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
    Colon = 10

class Token:
    kind: TokenKind
    value: any
    span: Span | None

    def __init__(self, kind: TokenKind, value: any, span: Span | None = None) -> None:
        self.kind = kind
        self.value = value
        self.span = span

    def __repr__(self) -> str:
        match self.kind:
            case TokenKind.Keyword:
                return f"Keyword({self.value})"
            case TokenKind.Identifier:
                return f"Identifier({self.value})"
            case TokenKind.Operator:
                return f"Operator({self.value})"
            case TokenKind.LParen:
                return "LParen"
            case TokenKind.RParen:
                return "RParen"
            case TokenKind.LBrace:
                return "LBrace"
            case TokenKind.RBrace:
                return "RBrace"
            case TokenKind.Number:
                return f"Number({self.value})"
            case TokenKind.Semicolon:
                return "Semicolon"
            case TokenKind.Colon:
                return "Colon"

    def name(self) -> str:
        match self.kind:
            case TokenKind.Keyword:
                return "keyword"
            case TokenKind.Identifier:
                return "identifier"
            case TokenKind.Operator:
                return "operator"
            case TokenKind.LParen:
                return "left parenthesis"
            case TokenKind.RParen:
                return "right parenthesis"
            case TokenKind.LBrace:
                return "left bracket"
            case TokenKind.RBrace:
                return "right bracket"
            case TokenKind.Number:
                return "number"
            case TokenKind.Semicolon:
                return "semicolon"
            case TokenKind.Colon:
                return "colon"