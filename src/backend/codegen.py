from llvmlite import ir
from lang import ast, types


TYPE_MAP: dict[types.Type, ir.Type] = {
    types.I8: ir.IntType(8),   types.U8:  ir.IntType(8),
    types.I16: ir.IntType(16), types.U16: ir.IntType(16),
    types.I32: ir.IntType(32), types.U32: ir.IntType(32),
    types.I64: ir.IntType(64), types.U64: ir.IntType(64),
    types.BOOL: ir.IntType(1),
    types.VOID: ir.VoidType(),
}

SIGNED = {types.I8, types.I16, types.I32, types.I64}

ARITH_OPS = {"+", "-", "*", "/", "%", "|", "&", "^"}
COMPARE_OPS = {"<", ">", "<=", ">=", "==", "!="}
LOGICAL_OPS = {"&&", "||", "^^"}


class IRGenerator:
    program: ast.Program
    module: ir.Module
    functions: dict[str, ir.Function]
    param_types: dict[str, list[types.Type]]
    builder: ir.IRBuilder | None
    scope: dict[str, ir.AllocaInstr]

    def __init__(self, program: ast.Program, name: str):
        self.program = program
        self.module = ir.Module(name=name)
        self.functions = {}
        self.param_types = {}
        self.builder = None
        self.scope = {}

    def generate(self) -> ir.Module:
        for func in self.program.functions:
            self.declare_function(func)
        for func in self.program.functions:
            self.gen_function(func)
        return self.module

    def declare_function(self, func: ast.Function) -> None:
        arg_types = [TYPE_MAP[a.type] for a in func.args]
        ret_type = TYPE_MAP[func.return_type]
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
            self.builder.ret_void() if func.return_type == types.VOID else self.builder.unreachable()

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
            case _:
                self.gen_expr(node)

    def gen_return(self, node: ast.Return) -> None:
        if node.value is None:
            self.builder.ret_void()
            return
        value = self.gen_expr(node.value)
        self.builder.ret(value)

    def gen_let(self, node: ast.Let) -> None:
        llvm_type = TYPE_MAP[node.type]
        alloca = self.builder.alloca(llvm_type, name=node.name)
        if node.value is not None:
            value = self.gen_expr(node.value)
            value = self.convert(value, node.value.type, node.type)
            self.builder.store(value, alloca)
        self.scope[node.name] = alloca

    def gen_assignment(self, node: ast.Assignment) -> None:
        ptr = self.scope[node.destination.name]
        dest_type = node.destination.type

        value = self.gen_expr(node.source)
        value = self.convert(value, node.source.type, dest_type)

        if node.op == "=":
            self.builder.store(value, ptr)
            return

        current = self.builder.load(ptr)
        op = node.op[:-1]
        result = self.gen_arith(op, dest_type in SIGNED, current, value)
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

    def gen_unary(self, node: ast.UnaryOperation) -> ir.Value:
        value = self.gen_expr(node.right)
        if node.operator == "!":
            value = self.convert(value, node.right.type, types.BOOL)
            return self.builder.not_(value)
        elif node.operator == "~":
            return self.builder.not_(value)
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
        signed = common in SIGNED

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
        if a == b:
            return a
        if (a, b) in types.IMPLICIT_CONVERSIONS:
            return b
        return a

    def convert(self, value: ir.Value, src: types.Type, dst: types.Type) -> ir.Value:
        if src == dst:
            return value

        llvm_src = TYPE_MAP[src]
        llvm_dst = TYPE_MAP[dst]

        if dst == types.BOOL:
            zero = ir.Constant(llvm_src, 0)
            return self.builder.icmp_signed("!=", value, zero)

        if src == types.BOOL:
            return self.builder.zext(value, llvm_dst)

        if llvm_dst.width > llvm_src.width:
            return self.builder.sext(value, llvm_dst) if src in SIGNED else self.builder.zext(value, llvm_dst)
        elif llvm_dst.width < llvm_src.width:
            return self.builder.trunc(value, llvm_dst)
        else:
            return value
