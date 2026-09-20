from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    start: int
    end: int

    def to(self, other: "Span") -> "Span":
        return Span(self.start, other.end)

    def location(self, source: str) -> tuple[int, int]:
        start = min(self.start, len(source))
        line = source.count("\n", 0, start) + 1
        column = start - (source.rfind("\n", 0, start) + 1) + 1
        return line, column
