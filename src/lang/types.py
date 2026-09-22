from dataclasses import dataclass


@dataclass(frozen=True)
class Type:
    name: str

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

U8  = Type("u8")
U16 = Type("u16")
U32 = Type("u32")
U64 = Type("u64")
I8  = Type("i8")
I16 = Type("i16")
I32 = Type("i32")
I64 = Type("i64")
BOOL = Type("bool")
VOID = Type("void")
ERROR = Type("<error>")

NUMERIC = (U8, U16, U32, U64, I8, I16, I32, I64)

BUILTIN = {t.name: t for t in (U8, U16, U32, U64, I8, I16, I32, I64, BOOL, VOID, ERROR)}

IMPLICIT_CONVERSIONS = set()

# auto-generate conversions
for source in NUMERIC:
    for target in NUMERIC:
        if source != target:
            IMPLICIT_CONVERSIONS.add((source, target))

    IMPLICIT_CONVERSIONS.add((source, BOOL))
    IMPLICIT_CONVERSIONS.add((BOOL, source))