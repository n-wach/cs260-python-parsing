from __future__ import annotations

import re
from .ir import *


class SetVariable:
    def __init__(self, name: str):
        self.name = name
        self.projections = set()

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return str(self) == str(other)


class Constructor:
    def __init__(self, name: str, arity: int, contravariant_positions: List[int]):
        self.name = name
        self.arity = arity
        self.contravariant_positions = contravariant_positions
        self.calls = set()

    def __str__(self):
        return self.name

    def as_def(self):
        return f"def constructor {self.name}, arity {self.arity}, contravariant positions {' '.join(map(str, self.contravariant_positions))}".strip()

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)


class Proj:
    def __init__(self, constructor: Constructor, var: SetVariable, index: int):
        self.constructor = constructor
        self.var = var
        self.index = index
        var.projections.add(self)

    def __str__(self):
        return f"proj({self.constructor}, {self.var}, {self.index})"

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)


class Call:
    def __init__(self, constructor: Constructor, args: List[Union[SetVariable, Call, Proj]]):
        self.constructor = constructor
        self.args = args
        constructor.calls.add(self)

    def __str__(self):
        if len(self.args) == 0:
            return f"call({self.constructor})"
        return f"call({self.constructor}, {', '.join(map(str, self.args))})"

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == str(other)


class Constraint:
    def __init__(self, left:  Union[SetVariable, Call, Proj], right:  Union[SetVariable, Call, Proj]):
        self.left = left
        self.right = right

    def __str__(self):
        return f"{self.left} <= {self.right}"


class SetConstraints:
    def __init__(self):
        self.constructors = []
        self.set_variables = []
        self.constraints = []

    @staticmethod
    def parse(text):
        """
        INPUT GRAMMAR:
        def constructor <name>, arity <int>, contravariant positions <int> <int> ...
        def set variable <name>
        <exp> <= <exp>

        Constructor names and set variable names don't overlap (and don't include 'call' or 'proj')
        <exp> is one of:
        <set variable name>
        call(<constructor name>, <exp>, <exp>, ...)
        proj(<constructor name>, <set variable name>, <int>)
        """
        set_constraints = SetConstraints()
        for line in text.splitlines():
            line = line.strip()
            if len(line) == 0:
                continue
            if line.startswith("def constructor "):
                set_constraints.add_parsed_constructor(line)
            else:
                set_constraints.add_parsed_constraint(line)
        return set_constraints

    def add_parsed_constructor(self, line):
        match = re.match(r"def constructor (\w+), arity (\d+), contravariant positions ?(.*)", line)
        assert match is not None
        name = match.group(1)
        arity = int(match.group(2))
        contravariant_positions = [int(x) for x in match.group(3).split()]
        self.constructors.append(Constructor(name, arity, contravariant_positions))

    def add_parsed_constraint(self, line):
        match = re.match(r"(.*) <= (.*)", line)
        assert match is not None
        left = self.parse_expression(match.group(1))
        right = self.parse_expression(match.group(2))
        self.constraints.append(Constraint(left, right))

    def parse_expression(self, text):
        text = text.strip()
        if text.startswith("call("):
            return self.parse_call(text)
        elif text.startswith("proj("):
            return self.parse_proj(text)
        else:
            return self.get_set_variable(text)

    def parse_call(self, text):
        text = text.strip()
        match = re.match(r"call\((\w+)(?:, (.*))?\)", text)
        assert match is not None
        constructor = self.get_constructor(match.group(1))
        if match.group(2) is None:
            return Call(constructor, [])
        raw_args = match.group(2)
        depth = 0
        last = 0
        args = []
        for i, c in enumerate(raw_args):
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif c == "," and depth == 0:
                arg = raw_args[last:i]
                args.append(self.parse_expression(arg))
                last = i + 1
        args.append(self.parse_expression(raw_args[last:]))
        return Call(constructor, args)

    def parse_proj(self, text):
        text = text.strip()
        match = re.match(r"proj\((\w+), (\w+), (\d+)\)", text)
        assert match is not None
        constructor = self.get_constructor(match.group(1))
        var = self.get_set_variable(match.group(2))
        index = int(match.group(3))
        return Proj(constructor, var, index)

    def get_constructor(self, name):
        name = name.strip()
        for constructor in self.constructors:
            if constructor.name == name:
                return constructor
        return None

    def get_set_variable(self, name):
        name = name.strip()
        for set_variable in self.set_variables:
            if set_variable.name == name:
                return set_variable
        var = SetVariable(name)
        self.set_variables.append(var)
        return var

    def to_text(self):
        s = ""
        s += "\n".join(sorted(c.as_def() for c in self.constructors)) + "\n"
        s += "\n".join(sorted(set(str(c) for c in self.constraints))) + "\n"
        return s

