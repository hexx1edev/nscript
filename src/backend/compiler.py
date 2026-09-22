from llvmlite import ir
import llvmlite.binding as llvm

llvm.initialize_native_target()
llvm.initialize_native_asmprinter()


def compile_to_object(module: ir.Module, output_path: str) -> None:
    module.triple = llvm.get_process_triple()

    target = llvm.Target.from_triple(module.triple)
    # codemodel='default' avoids the '-elf' triple llvmlite forces under the
    # 'jitdefault' codemodel on Windows, so emit_object produces native COFF.
    target_machine = target.create_target_machine(codemodel="default")

    backing_module = llvm.parse_assembly(str(module))
    backing_module.verify()

    obj_code = target_machine.emit_object(backing_module)
    with open(output_path, "wb") as file:
        file.write(obj_code)
