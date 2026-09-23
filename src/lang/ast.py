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
class Type(ASTNode):
    type: str | types.Type
    const: bool
    pointer: bool

@dataclass
class Argument(ASTNode):
    name: str
    type: Type

@dataclass
class Function(ASTNode):
    name: str
    return_type: Type
    args: list[Argument]
    body: list[ASTNode]

@dataclass
class Return(ASTNode):
    value: ASTNode | None

@dataclass
class NumberLiteral(ASTNode):
    value: int
    type: types.Type | None = field(default=None, kw_only=True, compare=False, repr=False)

@dataclass
class BooleanLiteral(ASTNode):
    value: bool
    type: types.Type | None = field(default=None, kw_only=True, compare=False, repr=False)

@dataclass
class Identifier(ASTNode):
    name: str
    type: types.Type | None = field(default=None, kw_only=True, compare=False, repr=False)

@dataclass
class Dereference(ASTNode):
    value: ASTNode

@dataclass
class Pointer(ASTNode):
    name: str
    type: types.Type | None = field(default=None, kw_only=True, compare=False, repr=False)

@dataclass
class BinaryOperation(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode
    type: types.Type | None = field(default=None, kw_only=True, compare=False, repr=False)

@dataclass
class UnaryOperation(ASTNode):
    operator: str
    right: ASTNode
    type: types.Type | None = field(default=None, kw_only=True, compare=False, repr=False)

@dataclass
class Let(ASTNode):
    name: str
    type: Type
    value: ASTNode

@dataclass
class Assignment(ASTNode):
    source: ASTNode
    op: str
    destination: Identifier

@dataclass
class FuncCall(ASTNode):
    name: "Identifier"
    args: list[ASTNode]
    type: types.Type | None = field(default=None, kw_only=True, compare=False, repr=False)

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

@dataclass
class While(ASTNode):
    condition: ASTNode
    body: list[ASTNode]

@dataclass
class Break(ASTNode):
    pass

@dataclass
class Continue(ASTNode):
    pass