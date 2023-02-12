from __future__ import annotations

from typing import List, Union
import re


class SetVariable:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name

    def carl(self):
        return f"def set variable {self.name}"


class Constructor:
    def __init__(self, name: str, arity: int, contravariant_positions: List[int]):
        self.name = name
        self.arity = arity
        self.contravariant_positions = contravariant_positions

    def __str__(self):
        return self.name

    def carl(self):
        return f"def constructor {self.name}, arity {self.arity}, contravariant positions {' '.join(map(str, self.contravariant_positions))}".strip()


class Proj:
    def __init__(self, constructor: Constructor, var: SetVariable, index: int):
        self.constructor = constructor
        self.var = var
        self.index = index

    def __str__(self):
        return f"proj({self.constructor}, {self.var}, {self.index})"


class Call:
    def __init__(self, constructor: Constructor, args: List[Union[SetVariable, Call, Proj]]):
        self.constructor = constructor
        self.args = args

    def __str__(self):
        if len(self.args) == 0:
            return f"call({self.constructor})"
        return f"call({self.constructor}, {', '.join(map(str, self.args))})"


class Constraint:
    def __init__(self, left:  Union[SetVariable, Call, Proj], right:  Union[SetVariable, Call, Proj]):
        self.left = left
        self.right = right

    def __str__(self):
        return f"{self.left} <= {self.right}"


class SetConstraints:
    def __init__(self, constructors: List[Constructor], set_variables: List[SetVariable], constraints: List[Constraint]):
        self.constructors = constructors
        self.set_variables = set_variables
        self.constraints = constraints

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
        set_constraints = SetConstraints([], [], [])
        for line in text.splitlines():
            line = line.strip()
            if len(line) == 0:
                continue
            if line.startswith("def constructor "):
                set_constraints.add_parsed_constructor(line)
            elif line.startswith("def set variable "):
                set_constraints.add_parsed_set_variable(line)
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

    def add_parsed_set_variable(self, line):
        match = re.match(r"def set variable (\w+)", line)
        assert match is not None
        name = match.group(1)
        self.set_variables.append(SetVariable(name))

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
        assert False

    def get_set_variable(self, name):
        name = name.strip()
        for set_variable in self.set_variables:
            if set_variable.name == name:
                return set_variable
        set_var = SetVariable(name)
        self.set_variables.append(set_var)
        return set_var

    def carl(self):
        s = ""
        for constructor in self.constructors:
            s += constructor.carl() + "\n"
        for set_variable in self.set_variables:
            s += set_variable.carl() + "\n"
        for constraint in self.constraints:
            s += str(constraint) + "\n"
        return s
