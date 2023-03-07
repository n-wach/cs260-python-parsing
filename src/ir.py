from __future__ import annotations

import abc
import enum
from typing import Dict, List


class Type:
    indirection: int = 0
    base_type: str

    def __init__(self, base_type, indirection=0):
        self.base_type = base_type
        self.indirection = indirection

    def as_fake_var(self):
        return f"any_of({self})"

    def __str__(self):
        return f"{self.base_type}{'*' * self.indirection}"


class StructField:
    name: str
    type: Type

    def __init__(self, name, type_):
        self.name = name
        self.type = type_


class Struct:
    name: str
    fields: List[StructField]

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields


class Variable:
    name: str
    type: Type

    def __init__(self, name, type_):
        self.name = name
        self.type = type_

    def __str__(self):
        return self.name

    def output(self):
        return f"{self.name}:{self.type}"


class Operand:
    def output(self):
        raise NotImplementedError


class VarOperand(Operand):
    variable: Variable

    def __init__(self, variable):
        self.variable = variable

    def output(self):
        return f"{self.variable.name}:{self.variable.type}"


class ConstIntOperand(Operand):
    value: int

    def __init__(self, value):
        self.value = value

    def output(self):
        return f"{self.value}"


class ConstFuncOperand(Operand):
    function: str
    type: Type

    def __init__(self, function, type_):
        self.function = function
        self.type = type_

    def __str__(self):
        return f"@{self.function}"

    def output(self):
        return f"@{self.function}:{self.type}"


class ConstNullPtrOperand(Operand):
    type: Type

    def __init__(self, type_):
        self.type = type_

    def __str__(self):
        return "@nullptr"

    def output(self):
        return f"@nullptr:{self.type}"


class Program:
    structs: List[Struct]
    functions: List[Function]

    def __init__(self, structs, functions):
        self.structs = structs
        self.functions = functions

    def get_function(self, func_name):
        for func in self.functions:
            if func.name == func_name:
                return func
        return None

    def get_inst(self, program_point) -> Instruction:
        # program point is "<function name>.<block label containing .>.<inst index>"
        func_name = program_point.split(".")[0]
        block_label = ".".join(program_point.split(".")[1:-1])
        inst_index = program_point.split(".")[-1]
        func = self.get_function(func_name)
        if func is None:
            raise ValueError(f"Program point {program_point} has invalid function name {func_name}")
        block = func.basic_blocks.get(block_label)
        if block is None:
            raise ValueError(f"Program point {program_point} has invalid block label {block_label}")
        if int(inst_index) >= len(block.body):
            raise ValueError(f"Program point {program_point} has invalid instruction index {inst_index}")
        return block.body[int(inst_index)]

    def output(self) -> str:
        out = ""
        for struct in self.structs:
            out += f"struct {struct.name} {{\n"
            for field in struct.fields:
                out += f"  {field.name}: {field.type}\n"
            out += "}\n\n"
        for func in self.functions:
            out += func.output()
        return out


class Function:
    name: str
    return_type: Type
    parameters: List[Variable]
    basic_blocks: Dict[str, BasicBlock]
    entry: BasicBlock
    exit: BasicBlock
    type: Type
    address_taken: bool

    def __init__(self, name, return_type, parameters, basic_blocks):
        self.name = name
        self.return_type = return_type
        self.parameters = parameters
        self.basic_blocks = {}
        for basic_block in basic_blocks:
            self.basic_blocks[basic_block.label] = basic_block
            basic_block.parent_function = self
        self.entry = self.basic_blocks.get("entry")
        for basic_block in self.basic_blocks.values():
            basic_block.resolve_labels()
            if isinstance(basic_block.terminal, RetInst):
                self.exit = basic_block
        type_str = f"{return_type}[{','.join(str(p.type) for p in parameters)}]"
        self.type = Type(type_str)
        self.address_taken = False

    def __repr__(self):
        return f"<Function {self.name}>"

    def output(self) -> str:
        out = ""
        out += f"function {self.name}({', '.join(p.output() for p in self.parameters)}) -> {self.return_type} {{\n"
        sorted_blocks = sorted(self.basic_blocks.values(), key=lambda b: b.label)
        out += "\n".join(basic_block.output() for basic_block in sorted_blocks)
        out += f"}}\n\n"
        return out


class BasicBlock:
    label: str
    body: List[Instruction]
    parent_function: Function
    terminal: TerminalInst

    def __init__(self, label, body):
        self.entry_store = None
        self.terminal_store = None
        self.label = label
        self.body = body
        self.terminal = body[-1]
        for i, inst in enumerate(body):
            inst.parent_block = self
            inst.index = i

    def resolve_labels(self):
        if isinstance(self.terminal, JumpInst):
            self.terminal.target = self.parent_function.basic_blocks.get(self.terminal.label)
        if isinstance(self.terminal, BranchInst):
            self.terminal.target_true = self.parent_function.basic_blocks.get(self.terminal.label_true)
            self.terminal.target_false = self.parent_function.basic_blocks.get(self.terminal.label_false)

    @property
    def name(self):
        return f"{self.parent_function.name}.{self.label}"

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"<BasicBlock {self.name}>"

    def __eq__(self, other):
        return self.name == other.name

    def output(self) -> str:
        out = ""
        out += f"{self.label}:\n"
        for inst in self.body:
            out += f"  {inst.output()}\n"
        return out


class Instruction:
    index: int
    parent_block: BasicBlock

    @property
    def program_point(self):
        return f"{self.parent_block.name}.{self.index}"

    def output(self):
        raise NotImplementedError


class Aop(enum.Enum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"


class ArithInst(Instruction):
    lhs: Variable
    left_op: Operand
    right_op: Operand
    operation: Aop

    def __init__(self, lhs, left_op, right_op, operation):
        self.lhs = lhs
        self.left_op = left_op
        self.right_op = right_op
        self.operation = operation

    def output(self):
        return f"{self.lhs.output()} = $arith {self.operation.value} {self.left_op.output()} {self.right_op.output()}"


class Rop(enum.Enum):
    EQ = "eq"
    NEQ = "neq"
    LT = "lt"
    GT = "gt"
    LTE = "lte"
    GTE = "gte"


class CmpInst(Instruction):
    lhs: Variable
    left_op: Operand
    right_op: Operand
    operation: Rop

    def __init__(self, lhs, left_op, right_op, operation):
        self.lhs = lhs
        self.left_op = left_op
        self.right_op = right_op
        self.operation = operation

    def output(self):
        return f"{self.lhs.output()} = $cmp {self.operation.value} {self.left_op.output()} {self.right_op.output()}"


class PhiInst(Instruction):
    lhs: Variable
    ops: List[Operand]

    def __init__(self, lhs, ops):
        self.lhs = lhs
        self.ops = ops

    def output(self):
        return f"{self.lhs.output()} = $phi({', '.join(op.output() for op in self.ops)})"


class CopyInst(Instruction):
    lhs: Variable
    rhs: Operand

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def output(self):
        return f"{self.lhs.output()} = $copy {self.rhs.output()}"


class AllocInst(Instruction):
    lhs: Variable

    def __init__(self, lhs):
        self.lhs = lhs

    def output(self):
        return f"{self.lhs.output()} = $alloc"


class AddrofInst(Instruction):
    lhs: Variable
    target: Operand

    def __init__(self, lhs, target):
        self.lhs = lhs
        self.target = target

    def output(self):
        return f"{self.lhs.output()} = $addrof {self.target.output()}"


class LoadInst(Instruction):
    lhs: Variable
    src_ptr: VarOperand

    def __init__(self, lhs, src_ptr):
        self.lhs = lhs
        self.src_ptr = src_ptr

    def output(self):
        return f"{self.lhs.output()} = $load {self.src_ptr.output()}"


class StoreInst(Instruction):
    dest: Variable
    value: Operand

    def __init__(self, dest, value):
        self.dest = dest
        self.value = value

    def output(self):
        return f"$store {self.dest.output()} {self.value.output()}"


class GepInst(Instruction):
    lhs: Variable
    src_ptr: Operand
    array_index: Operand
    field_name: str

    def __init__(self, lhs, src_ptr, array_index, field_name):
        self.lhs = lhs
        self.src_ptr = src_ptr
        self.array_index = array_index
        self.field_name = field_name

    def output(self):
        return f"{self.lhs.output()} = $gep {self.src_ptr.output()} {self.array_index.output()} {self.field_name}".strip()


class SelectInst(Instruction):
    lhs: Variable
    condition: Operand
    true_op: Operand
    false_op: Operand

    def __init__(self, lhs, condition, true_op, false_op):
        self.lhs = lhs
        self.condition = condition
        self.true_op = true_op
        self.false_op = false_op

    def output(self):
        return f"{self.lhs.output()} = $select {self.condition.output()} {self.true_op.output()} {self.false_op.output()}"


class CallInst(Instruction):
    # direct function call "lhs = func_name(args)".
    lhs: Variable
    callee: str
    args: List[Operand]

    def __init__(self, lhs, callee, args):
        self.lhs = lhs
        self.callee = callee
        self.args = args

    def output(self):
        return f"{self.lhs.output()} = $call {self.callee}({', '.join(arg.output() for arg in self.args)})"


class ICallInst(Instruction):
    # indirect function call "lhs = (*func_ptr)(args)".
    lhs: Variable
    function: Operand
    args: List[Operand]

    def __init__(self, lhs, function, args):
        self.lhs = lhs
        self.function = function
        self.args = args

    def output(self):
        return f"{self.lhs.output()} = $icall {self.function.output()}({', '.join(arg.output() for arg in self.args)})"


class TerminalInst(Instruction):
    @abc.abstractmethod
    def targets(self) -> [BasicBlock]:
        raise NotImplementedError


class RetInst(TerminalInst):
    retval: Operand

    def __init__(self, retval):
        self.retval = retval

    def targets(self):
        return []

    def output(self):
        return f"$ret {self.retval.output()}"


class JumpInst(TerminalInst):
    label: str
    target: BasicBlock

    def __init__(self, label):
        self.label = label

    def targets(self):
        return [self.target]

    def output(self):
        return f"$jump {self.label}"


class BranchInst(TerminalInst):
    condition: Operand
    label_true: str
    label_false: str
    target_true: BasicBlock
    target_false: BasicBlock

    def __init__(self, condition, label_true, label_false):
        self.condition = condition
        self.label_true = label_true
        self.label_false = label_false

    def targets(self):
        return [self.target_true, self.target_false]

    def output(self):
        return f"$branch {self.condition.output()} {self.label_true} {self.label_false}"

