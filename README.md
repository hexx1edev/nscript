# NScript

NScript is a simple C-like compiled programming language, that was designed to be a better and mixed version of C, C++ and Rust while keeping simplicity and beginner-friendly syntax.

The language's compiler is currently written in Python(because I want to finish it ASAP), but after first release I'll start working on rewriting it to itself.  
It uses LLVM(not ready yet) as a backend.

## Building

Install `python >=3.12, uv`, run `uv sync`.

## Usage

Run `uv run nscript <path/to/file.ns>`, compiler will parse the file and generate an AST. Later, I'll implement actual compilation with LLVM.

You can run some examples from `examples` directory to see what AST comes out.

## Features

These are features of nscript:

- [x] Type inference
- [x] Implicit type conversion(see `src/lang/types.py` to see compatible pairs)
- [x] Rust-like easy to read syntax
- [x] (WIP) Full C compatibility
- [ ] Ligthweight RTTI
- [ ] Static compile-time reflection

These are language things:

- [x] Comments
- [x] Functions
- [x] Let definitions
- [x] Constants
- [x] Numeric types
- [x] Boolean type
- [x] If->else if->else statements
- [ ] While loops
- [ ] For loops
- [ ] String pointers
- [ ] Raw pointers
- [ ] References
- [ ] Structs
- [ ] Iterators
- [ ] Struct methods
- [ ] Interfaces
- [ ] Generics
- [ ] Decorators
- [ ] Modules
- [ ] Standart library

## License

The project is licensed under Apache-2.0 license.