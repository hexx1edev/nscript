from dataclasses import dataclass, field
from lang.span import Span
from lang import types


@dataclass
class ASTNode:
    span: Span | None = field(default=None, kw_only=True, compare=False, repr=False)

@dataclass
class Program(ASTNode):
    functions: list["Function"]

@dataclass
class Argument(ASTNode):
    name: str
    type: str | types.Type

@dataclass
class Function(ASTNode):
    name: str
    return_type: str | types.Type
    args: list[Argument]
    body: list[ASTNode]

@dataclass
class Return(ASTNode):
    value: ASTNode | None

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
    type: str | types.Type
    value: ASTNode
    const: bool

@dataclass
class Assignment(ASTNode):
    source: ASTNode
    op: str
    destination: Identifier

@dataclass
class FuncCall(ASTNode):
    name: "Identifier"
    args: list[ASTNode]

@dataclass
class ElseIf(ASTNode):
    condition: ASTNode
    body: list[ASTNode]

@dataclass
class If(ASTNode):
    condition: ASTNode
    body: list[ASTNode]
    branches: list[ElseIf]
    fallback: list[ASTNode]