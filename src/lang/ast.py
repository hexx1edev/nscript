from dataclasses import dataclass


class ASTNode:
    pass

@dataclass
class Program(ASTNode):
    functions: list["Function"]

@dataclass
class Function(ASTNode):
    name: str
    return_type: str
    body: list[ASTNode]

@dataclass
class Return(ASTNode):
    value: ASTNode

@dataclass
class NumberLiteral(ASTNode):
    value: int

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