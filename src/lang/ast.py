from dataclasses import dataclass, field
from lang.span import Span


@dataclass
class ASTNode:
    span: Span | None = field(default=None, kw_only=True, compare=False, repr=False)

@dataclass
class Program(ASTNode):
    functions: list["Function"]

@dataclass
class Argument(ASTNode):
    name: str
    type: str

@dataclass
class Function(ASTNode):
    name: str
    return_type: str
    args: list[Argument]
    body: list[ASTNode]

@dataclass
class Return(ASTNode):
    value: ASTNode

@dataclass
class NumberLiteral(ASTNode):
    value: int

@dataclass
class BooleanLiteral(ASTNode):
    value: bool

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class BinaryOperation(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode

@dataclass
class UnaryOperation(ASTNode):
    operator: str
    right: ASTNode

@dataclass
class Let(ASTNode):
    name: str
    type: str
    value: ASTNode
    const: bool

@dataclass
class Assignment(ASTNode):
    source: ASTNode
    op: str
    destination: Identifier

@dataclass
class FuncCall(ASTNode):
    name: str
    args: list[ASTNode]