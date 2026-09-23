# NScript

NScript is a simple C-like compiled programming language, that was designed to be a better and mixed version of C, C++ and Rust while keeping simplicity and beginner-friendly syntax.

The language's compiler is currently written in Python(because I want to finish it ASAP), but after first release I'll start working on rewriting it to itself.  
It uses LLVM as a compilation backend.

## Building

Install `python >=3.12, uv`, run `uv sync`.

## Usage

Run `uv run nscript <path/to/file.ns> -o <out.o>` to compile a program into object file. You have to link it before running it.

You can compile and run some examples from `examples` directory and see the result code, coming out from the executable.

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
- [x] While loops
- [x] Raw pointers
- [ ] String views
- [ ] References
- [ ] Floats
- [ ] Structs
- [ ] Iterators
- [ ] For loops
- [ ] Struct methods
- [ ] Interfaces
- [ ] Generics
- [ ] Decorators
- [ ] Modules
- [ ] Standart library
- [ ] Self-hosted

## License

The project is licensed under Apache-2.0 license.