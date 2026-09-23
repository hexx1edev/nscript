from dataclasses import replace
from llvmlite import ir
from lang import ast, types


SCALAR_TYPES: dict[str, ir.Type] = {
    "i8": ir.IntType(8),   "u8":  ir.IntType(8),
    "i16": ir.IntType(16), "u16": ir.IntType(16),
    "i32": ir.IntType(32), "u32": ir.IntType(32),
    "i64": ir.IntType(64), "u64": ir.IntType(64),
    "bool": ir.IntType(1),
    "void": ir.VoidType(),
}

SIGNED_NAMES = {"i8", "i16", "i32", "i64"}

ARITH_OPS = {"+", "-", "*", "/", "%", "|", "&", "^"}
COMPARE_OPS = {"<", ">", "<=", ">=", "==", "!="}
LOGICAL_OPS = {"&&", "||", "^^"}


def llvm_type(t: types.Type) -> ir.Type:
    base = SCALAR_TYPES[t.name]

    if t.pointer:
        if t.name == types.VOID.name:
            return ir.PointerType(ir.IntType(8))
        return base.as_pointer()
    return base


def is_signed(t: types.Type) -> bool:
    return t.name in SIGNED_NAMES


def is_void(t: types.Type) -> bool:
    return t.name == types.VOID.name and not t.pointer


def strip_const(t: types.Type) -> types.Type:
    return replace(t, const=False)


class IRGenerator:
    program: ast.Program
    module: ir.Module
    functions: dict[str, ir.Function]
    param_types: dict[str, list[types.Type]]
    builder: ir.IRBuilder | None
    scope: dict[str, ir.AllocaInstr]
    loop_stack: list[tuple[ir.Block, ir.Block]]

    def __init__(self, program: ast.Program, name: str):
        self.program = program
        self.module = ir.Module(name=name)
        self.functions = {}
        self.param_types = {}
        self.builder = None
        self.scope = {}
        self.loop_stack = []

    def generate(self) -> ir.Module:
        for func in self.program.functions:
            self.declare_function(func)
        for func in self.program.functions:
            self.gen_function(func)
        return self.module

    def declare_function(self, func: ast.Function) -> None:
        arg_types = [llvm_type(a.type) for a in func.args]
        ret_type = llvm_type(func.return_type)
        fnty = ir.FunctionType(ret_type, arg_types)
        llvm_func = ir.Function(self.module, fnty, name=func.name)

        for arg, a in zip(llvm_func.args, func.args):
            arg.name = a.name

        self.functions[func.name] = llvm_func
        self.param_types[func.name] = [a.type for a in func.args]

    def gen_function(self, func: ast.Function) -> None:
        llvm_func = self.functions[func.name]
        entry = llvm_func.append_basic_block("entry")
        self.builder = ir.IRBuilder(entry)
        self.scope = {}

        for arg, llvm_arg in zip(func.args, llvm_func.args):
            alloca = self.builder.alloca(llvm_arg.type, name=arg.name)
            self.builder.store(llvm_arg, alloca)
            self.scope[arg.name] = alloca

        self.gen_block(func.body)

        if not self.builder.block.is_terminated:
            self.builder.ret_void() if is_void(func.return_type) else self.builder.unreachable()

    def gen_block(self, body: list[ast.ASTNode]) -> None:
        for stmt in body:
            self.gen_statement(stmt)

    def gen_statement(self, node: ast.ASTNode) -> None:
        match node:
            case ast.Return():
                self.gen_return(node)
            case ast.Let():
                self.gen_let(node)
            case ast.Assignment():
                self.gen_assignment(node)
            case ast.If():
                self.gen_if(node)
            case ast.While():
                self.gen_while(node)
            case ast.Break():
                self.builder.branch(self.loop_stack[-1][1])
            case ast.Continue():
                self.builder.branch(self.loop_stack[-1][0])
            case _:
                self.gen_expr(node)

    def gen_return(self, node: ast.Return) -> None:
        if node.value is None:
            self.builder.ret_void()
            return
        value = self.gen_expr(node.value)
        self.builder.ret(value)

    def gen_let(self, node: ast.Let) -> None:
        alloca_type = llvm_type(node.type)
        alloca = self.builder.alloca(alloca_type, name=node.name)
        if node.value is not None:
            value = self.gen_expr(node.value)
            value = self.convert(value, node.value.type, node.type)
            self.builder.store(value, alloca)
        self.scope[node.name] = alloca

    def gen_assignment(self, node: ast.Assignment) -> None:
        if isinstance(node.destination, ast.Dereference):
            ptr = self.builder.load(self.scope[node.destination.value.name])
        else:
            ptr = self.scope[node.destination.name]
        dest_type = node.destination.type

        value = self.gen_expr(node.source)
        value = self.convert(value, node.source.type, dest_type)

        if node.op == "=":
            self.builder.store(value, ptr)
            return

        current = self.builder.load(ptr)
        op = node.op[:-1]
        result = self.gen_arith(op, is_signed(dest_type), current, value)
        self.builder.store(result, ptr)

    def gen_if(self, node: ast.If) -> None:
        branches = [(node.condition, node.body)] + [(b.condition, b.body) for b in node.branches]
        end_block = self.builder.append_basic_block("if.end")
        self.gen_if_chain(branches, node.fallback, end_block)
        self.builder.position_at_end(end_block)

    def gen_if_chain(self, branches: list[tuple[ast.ASTNode, list[ast.ASTNode]]],
                      fallback: list[ast.ASTNode], end_block: ir.Block) -> None:
        condition, body = branches[0]
        rest = branches[1:]

        cond_value = self.gen_expr(condition)
        cond_value = self.convert(cond_value, condition.type, types.BOOL)

        then_block = self.builder.append_basic_block("if.then")
        else_block = self.builder.append_basic_block("if.else")
        self.builder.cbranch(cond_value, then_block, else_block)

        self.builder.position_at_end(then_block)
        self.gen_block(body)
        if not self.builder.block.is_terminated:
            self.builder.branch(end_block)

        self.builder.position_at_end(else_block)
        if rest:
            self.gen_if_chain(rest, fallback, end_block)
        else:
            self.gen_block(fallback)
            if not self.builder.block.is_terminated:
                self.builder.branch(end_block)

    def gen_while(self, node: ast.While) -> None:
        cond_block = self.builder.append_basic_block("while.cond")
        body_block = self.builder.append_basic_block("while.body")
        end_block = self.builder.append_basic_block("while.end")

        self.builder.branch(cond_block)

        self.builder.position_at_end(cond_block)
        cond_value = self.gen_expr(node.condition)
        cond_value = self.convert(cond_value, node.condition.type, types.BOOL)
        self.builder.cbranch(cond_value, body_block, end_block)

        self.builder.position_at_end(body_block)
        self.loop_stack.append((cond_block, end_block))
        self.gen_block(node.body)
        self.loop_stack.pop()
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_block)

        self.builder.position_at_end(end_block)

    def gen_expr(self, node: ast.ASTNode) -> ir.Value:
        match node:
            case ast.NumberLiteral():
                return ir.Constant(ir.IntType(32), node.value)
            case ast.BooleanLiteral():
                return ir.Constant(ir.IntType(1), int(node.value))
            case ast.Identifier():
                return self.builder.load(self.scope[node.name], name=node.name)
            case ast.UnaryOperation():
                return self.gen_unary(node)
            case ast.BinaryOperation():
                return self.gen_binop(node)
            case ast.FuncCall():
                return self.gen_call(node)
            case ast.Pointer():
                return self.scope[node.name]
            case ast.Dereference():
                ptr_value = self.builder.load(self.scope[node.value.name], name=f"{node.value.name}.ptr")
                return self.builder.load(ptr_value)

    def gen_unary(self, node: ast.UnaryOperation) -> ir.Value:
        value = self.gen_expr(node.right)
        if node.operator == "!":
            value = self.convert(value, node.right.type, types.BOOL)
            return self.builder.not_(value)
        elif node.operator == "~":
            return self.builder.not_(value)
        elif node.operator == "-":
            return self.builder.neg(value)
        raise NotImplementedError(node.operator)

    def gen_binop(self, node: ast.BinaryOperation) -> ir.Value:
        op = node.operator

        if op in LOGICAL_OPS:
            lhs = self.convert(self.gen_expr(node.left), node.left.type, types.BOOL)
            rhs = self.convert(self.gen_expr(node.right), node.right.type, types.BOOL)
            match op:
                case "&&":
                    return self.builder.and_(lhs, rhs)
                case "||":
                    return self.builder.or_(lhs, rhs)
                case "^^":
                    return self.builder.xor(lhs, rhs)

        common = self.common_type(node.left.type, node.right.type)
        lhs = self.convert(self.gen_expr(node.left), node.left.type, common)
        rhs = self.convert(self.gen_expr(node.right), node.right.type, common)
        signed = is_signed(common)

        if op in ARITH_OPS:
            return self.gen_arith(op, signed, lhs, rhs)
        elif op in COMPARE_OPS:
            cmp = self.builder.icmp_signed if signed else self.builder.icmp_unsigned
            return cmp(op, lhs, rhs)

        raise NotImplementedError(op)

    def gen_arith(self, op: str, signed: bool, lhs: ir.Value, rhs: ir.Value) -> ir.Value:
        match op:
            case "+":
                return self.builder.add(lhs, rhs)
            case "-":
                return self.builder.sub(lhs, rhs)
            case "*":
                return self.builder.mul(lhs, rhs)
            case "/":
                return self.builder.sdiv(lhs, rhs) if signed else self.builder.udiv(lhs, rhs)
            case "%":
                return self.builder.srem(lhs, rhs) if signed else self.builder.urem(lhs, rhs)
            case "|":
                return self.builder.or_(lhs, rhs)
            case "&":
                return self.builder.and_(lhs, rhs)
            case "^":
                return self.builder.xor(lhs, rhs)
        raise NotImplementedError(op)

    def gen_call(self, node: ast.FuncCall) -> ir.Value:
        llvm_func = self.functions[node.name.name]
        params = self.param_types[node.name.name]

        args = []
        for arg_node, param_type in zip(node.args, params):
            value = self.gen_expr(arg_node)
            args.append(self.convert(value, arg_node.type, param_type))

        return self.builder.call(llvm_func, args)

    def common_type(self, a: types.Type, b: types.Type) -> types.Type:
        if strip_const(a) == strip_const(b):
            return a
        if (strip_const(a), strip_const(b)) in types.IMPLICIT_CONVERSIONS:
            return b
        return a

    def convert(self, value: ir.Value, src: types.Type, dst: types.Type) -> ir.Value:
        if strip_const(src) == strip_const(dst):
            return value

        llvm_src = llvm_type(src)
        llvm_dst = llvm_type(dst)

        if dst.name == types.BOOL.name:
            zero = ir.Constant(llvm_src, 0)
            return self.builder.icmp_signed("!=", value, zero)

        if src.name == types.BOOL.name:
            return self.builder.zext(value, llvm_dst)

        if llvm_dst.width > llvm_src.width:
            return self.builder.sext(value, llvm_dst) if is_signed(src) else self.builder.zext(value, llvm_dst)
        elif llvm_dst.width < llvm_src.width:
            return self.builder.trunc(value, llvm_dst)
        else:
            return value
