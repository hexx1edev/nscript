from dataclasses import dataclass, replace

from lang import ast, types
from lang.span import Span


ARITHMETIC = {"+", "-", "*", "/", "%", "|", "&", "^"}
COMPARISON = {"<", ">", "<=", ">="}
EQUALITY   = {"==", "!="}
LOGICAL    = {"&&", "||", "^^"}


@dataclass
class SemanticError:
    span: Span | None
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class Symbol:
    name: str
    type: types.Type
    const: bool = False


@dataclass
class Signature:
    name: str
    params: list[tuple[str, types.Type]]
    return_type: types.Type


class Scope:
    def __init__(self, parent: "Scope | None" = None) -> None:
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}

    def declare(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Symbol | None:
        scope = self
        while scope is not None:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None


class Analyzer:
    prog: ast.Program
    scope: Scope
    errors: list[SemanticError]
    functions: dict[str, Signature]
    current: Signature | None

    def __init__(self, program: ast.Program) -> None:
        self.prog = program
        self.errors: list[SemanticError] = []
        self.scope = Scope()
        self.functions = {}
        self.current = None
        self.loop_depth = 0

    def error(self, node: ast.ASTNode | Span | None, message: str) -> None:
        span = node.span if isinstance(node, ast.ASTNode) else node
        self.errors.append(SemanticError(span, message))

    def push(self) -> None:
        self.scope = Scope(self.scope)

    def pop(self) -> None:
        self.scope = self.scope.parent

    def analyze(self) -> list[SemanticError]:
        self.collect_functions()
        for func in self.prog.functions:
            self.check_function(func)
        return self.errors

    def collect_functions(self) -> None:
        for func in self.prog.functions:
            if func.name in self.functions:
                self.error(func, f"function `{func.name}` is already defined")
                continue
            
            params = [(a.name, self.resolve_type(a, a.type)) for a in func.args]

            ret = types.VOID if func.return_type is None else self.resolve_type(func, func.return_type)
            func.return_type = ret
            self.functions[func.name] = Signature(func.name, params, ret)

    def check_function(self, func: ast.Function) -> None:
        sig = self.functions[func.name]
        self.current = sig
        self.push()
        for arg, (_, ty) in zip(func.args, sig.params):
            if self.scope.lookup(arg.name) is not None:
                self.error(arg, f"argument `{arg.name}` is already declared")
                continue
            self.scope.declare(Symbol(arg.name, ty, ty.const))
            arg.type = ty
        self.check_block(func.body, new_scope=False)
        self.pop()
        self.current = None

    def check_block(self, body: list[ast.ASTNode], new_scope: bool = True) -> None:
        if new_scope:
            self.push()
        for stmt in body:
            self.check_statement(stmt)
        if new_scope:
            self.pop()

    def check_statement(self, node: ast.ASTNode) -> types.Type | None:
        match node:
            case ast.Let():
                self.check_let(node)
            case ast.Assignment():
                self.check_assignment(node)
            case ast.Return():
                self.check_return(node)
            case ast.If():
                self.check_if(node)
            case ast.While():
                self.check_while(node)
            case ast.Break():
                self.check_loop_control(node, "break")
            case ast.Continue():
                self.check_loop_control(node, "continue")
            case _:
                self.check_expr(node)

    def check_return(self, node: ast.Return) -> None:
        expected = self.current.return_type
        if node.value is None:
            if not Analyzer.is_void(expected):
                self.error(node, f"expected a return value of type `{expected}`")
            return
        actual = self.check_expr(node.value)
        if Analyzer.is_void(expected):
            self.error(node.value, "cannot return a value from `void` function")
            return
        self.coerce(node.value, actual, expected)

    def check_if(self, node: ast.If) -> None:
        self.check_condition(node.condition)
        self.check_block(node.body)
        for branch in node.branches:
            self.check_condition(branch.condition)
            self.check_block(branch.body)
        self.check_block(node.fallback)

    def check_condition(self, node: ast.ASTNode) -> None:
        self.coerce(node, self.check_expr(node), types.BOOL)

    def check_assignment(self, node: ast.Assignment) -> None:
        is_deref = isinstance(node.destination, ast.Dereference)
        target = node.destination.value if is_deref else node.destination

        symbol = self.scope.lookup(target.name)
        value = self.check_expr(node.source)
        if symbol is None:
            self.error(node.destination, f"identifier `{target.name}` is not found in current scope")
            return
        elif symbol.const:
            self.error(node.destination, f"`{symbol.name}` is a constant")

        if is_deref:
            if not symbol.type.pointer:
                self.error(node.destination, f"`{symbol.name}` is not a pointer")
                return
            dest_type = replace(symbol.type, pointer=False)
        else:
            dest_type = symbol.type

        node.destination.type = dest_type

        if node.op == "=":
            self.coerce(node.source, value, dest_type)
        else:
            if not Analyzer.numeric_compatible(dest_type):
                self.error(node.destination, f"`{dest_type}` is not numeric or numeric-compatible")
            if not Analyzer.numeric_compatible(value):
                self.error(node.destination, f"`{value}` is not numeric or numeric-compatible")

    def check_expr(self, node: ast.ASTNode) -> types.Type:
        result = self.check_expr_inner(node)
        node.type = result
        return result

    def check_ident(self, node: ast.ASTNode, deref: bool = False) -> types.Type:
        symbol = self.scope.lookup(node.name)
        if symbol is None:
            self.error(node, f"identifier `{node.name}` is not found in current scope")
            return types.ERROR
        if not symbol.type.pointer and deref:
            self.error(node, f"identifier `{node.name}` type is not a pointer")
            return types.ERROR

        return symbol.type

    def check_expr_inner(self, node: ast.ASTNode) -> types.Type:
        match node:
            case ast.NumberLiteral():
                return types.I32
            case ast.BooleanLiteral():
                return types.BOOL
            case ast.Identifier():
                return self.check_ident(node)
            case ast.Pointer():
                return replace(self.check_ident(node), pointer=True)
            case ast.Dereference():
                return replace(self.check_ident(node.value), pointer=False)
            case ast.UnaryOperation():
                ty = self.check_expr(node.right)

                if Analyzer.is_void(ty):
                    self.error(node.left, "expression cannot have `void` type")

                if node.operator == "!":
                    self.coerce(node.right, ty, types.BOOL)
                    return types.BOOL
                elif node.operator in ("~", "-"):
                    if not Analyzer.numeric_compatible(ty):
                        self.error(node.right, f"`{ty}` is not numeric or numeric-compatible")
                        return types.ERROR
                    return ty

                self.error(node, f"invalid operator `{node.operator}`")
                return types.ERROR
            case ast.BinaryOperation():
                left = self.check_expr(node.left)
                right = self.check_expr(node.right)
                op = node.operator

                if Analyzer.is_void(left):
                    self.error(node.left, "expression cannot have `void` type")
                elif Analyzer.is_void(right):
                    self.error(node.right, "expression cannot have `void` type")

                if op in ARITHMETIC:
                    return self.common_type(node, left, right)
                elif op in COMPARISON:
                    self.common_type(node, left, right)
                    return types.BOOL
                elif op in EQUALITY:
                    self.common_type(node, left, right)
                    return types.BOOL
                elif op in LOGICAL:
                    self.coerce(node.left, left, types.BOOL)
                    self.coerce(node.right, right, types.BOOL)
                    return types.BOOL

                self.error(node, f"invalid operator `{op}`")
                return types.ERROR
            case ast.FuncCall():
                arg_types = [self.check_expr(a) for a in node.args]

                sig = self.functions.get(node.name.name)
                if sig is None:
                    self.error(node.name, f"function `{node.name.name}` is not found in current scope")
                    return types.ERROR

                if len(arg_types) != len(sig.params):
                    self.error(node, f"`{node.name.name}` takes {len(sig.params)} argument(s), got {len(arg_types)}")

                for (idx, type) in enumerate(arg_types):
                    self.coerce(node.args[idx], type, sig.params[idx][1])

                return sig.return_type

    def check_let(self, node: ast.Let) -> None:
        declared = None
        if node.type is not None:
            declared = self.resolve_type(node, node.type)

        if declared is not None and Analyzer.is_void(declared):
            self.error(node, "let cannot have `void` type")

        value_type = None
        if node.value is not None:
            value_type = self.check_expr(node.value)

        if value_type is not None and Analyzer.is_void(value_type):
            self.error(node.value, "initializer cannot have `void` type")

        type = declared or value_type or types.ERROR

        if declared is not None and value_type is not None:
            self.coerce(node.value, declared, value_type)

        node.type = type

        if not self.scope.declare(Symbol(node.name, type, type.const)):
            self.error(node, f"`{node.name}` is already declared in this scope")

    def resolve_type(self, node, type: ast.Type) -> types.Type:
        name = type.type
        if name in types.BUILTIN:
            base = types.BUILTIN[name]
            return types.Type(base.name, const=type.const, pointer=type.pointer)
        self.error(node, f"unknown type: `{name}`")
        return types.ERROR

    def can_convert(src: types.Type, dst: types.Type) -> bool:
        src = replace(src, const=False)
        dst = replace(dst, const=False)
        return src == dst or (src, dst) in types.IMPLICIT_CONVERSIONS

    def is_void(type: types.Type) -> bool:
        return type.name == types.VOID.name and not type.pointer

    def coerce(self, node, actual: types.Type, expected: types.Type) -> None:
        if types.ERROR in (actual, expected):
            return
        if not Analyzer.can_convert(actual, expected):
            self.error(node, f"expected `{expected}`, got `{actual}`")

    def common_type(self, node, a: types.Type, b: types.Type) -> types.Type:
        if a == b:
            return a
        elif Analyzer.can_convert(a, b):
            return b
        elif Analyzer.can_convert(b, a):
            return a
        else:
            self.error(node, f"types {a} and {b} are not compatible")
            return types.ERROR

    def numeric_compatible(type: types.Type) -> bool:
        if replace(type, const=False) in types.NUMERIC:
            return True
        else:
            for t in types.NUMERIC:
                if Analyzer.can_convert(type, t):
                    return True
        return False

    def check_while(self, node: ast.ASTNode) -> None:
        self.check_condition(node.condition)
        self.loop_depth += 1
        self.check_block(node.body)
        self.loop_depth -= 1

    def check_loop_control(self, node: ast.ASTNode, keyword: str) -> None:
        if self.loop_depth == 0:
            self.error(node, f"`{keyword}` should be used inside a loop")