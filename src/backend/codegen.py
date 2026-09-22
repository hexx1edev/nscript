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

class IRGenerator:
    program: ast.Program
    module: ir.Module
    functions: dict[str, ir.Function]
    builder: ir.IRBuilder | None
    scope: dict[str, ir.AllocaInstr]

    def __init__(self, program: ast.Program, name: str):
        self.program = program
        self.module = ir.Module(name=name)
        self.functions = {}
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
            case _:
                print(node, " is not implemented yet")

    def gen_return(self, node: ast.Return) -> None:
        if node.value is None:
            self.builder.ret_void()
            return
        value = self.gen_expr(node.value)
        self.builder.ret(value)

    def gen_expr(self, node: ast.ASTNode) -> ir.Value:
        match node:
            case ast.NumberLiteral():
                return ir.Constant(ir.IntType(32), node.value)
            case _:
                print(node, " is not implemented yet")