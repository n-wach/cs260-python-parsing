from __future__ import annotations

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


class Operand:
    pass


class VarOperand(Operand):
    variable: Variable

    def __init__(self, variable):
        self.variable = variable


class ConstIntOperand(Operand):
    value: int

    def __init__(self, value):
        self.value = value


class ConstFuncOperand(Operand):
    function: str
    type: Type

    def __init__(self, function, type_):
        self.function = function
        self.type = type_

    def __str__(self):
        return f"@{self.function}"


class ConstNullPtrOperand(Operand):
    type: Type

    def __init__(self, type_):
        self.type = type_

    def __str__(self):
        return "@nullptr"


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


class Function:
    name: str
    return_type: Type
    parameters: List[Variable]
    basic_blocks: Dict[str, BasicBlock]
    entry: BasicBlock
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
        self.entry = self.basic_blocks["entry"]
        for basic_block in self.basic_blocks.values():
            basic_block.resolve_labels()
        type_str = f"{return_type}[{','.join(str(p.type) for p in parameters)}]"
        self.type = Type(type_str)
        self.address_taken = False

    def __repr__(self):
        return f"<Function {self.name}>"


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
            self.terminal.target = self.parent_function.basic_blocks[self.terminal.label]
        if isinstance(self.terminal, BranchInst):
            self.terminal.target_true = self.parent_function.basic_blocks[self.terminal.label_true]
            self.terminal.target_false = self.parent_function.basic_blocks[self.terminal.label_false]

    @property
    def name(self):
        return f"{self.parent_function.name}.{self.label}"

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"<BasicBlock {self.name}>"


class Instruction:
    index: int
    parent_block: BasicBlock

    @property
    def program_point(self):
        return f"{self.parent_block.name}.{self.index}"


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


class PhiInst(Instruction):
    lhs: Variable
    ops: List[Operand]

    def __init__(self, lhs, ops):
        self.lhs = lhs
        self.ops = ops


class CopyInst(Instruction):
    lhs: Variable
    rhs: Operand

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs


class AllocInst(Instruction):
    lhs: Variable

    def __init__(self, lhs):
        self.lhs = lhs

    def abstract_execute(self, abstract_store):
        raise NotImplementedError


class AddrofInst(Instruction):
    lhs: Variable
    target: Operand

    def __init__(self, lhs, target):
        self.lhs = lhs
        self.target = target


class LoadInst(Instruction):
    lhs: Variable
    src_ptr: Operand

    def __init__(self, lhs, src_ptr):
        self.lhs = lhs
        self.src_ptr = src_ptr


class StoreInst(Instruction):
    dest: Variable
    value: Operand

    def __init__(self, dest, value):
        self.dest = dest
        self.value = value


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


class CallInst(Instruction):
    # direct function call "lhs = func_name(args)".
    lhs: Variable
    callee: str
    args: List[Operand]

    def __init__(self, lhs, callee, args):
        self.lhs = lhs
        self.callee = callee
        self.args = args


class ICallInst(Instruction):
    # indirect function call "lhs = (*func_ptr)(args)".
    lhs: Variable
    function: Operand
    args: List[Operand]

    def __init__(self, lhs, function, args):
        self.lhs = lhs
        self.function = function
        self.args = args


class TerminalInst(Instruction):
    pass


class RetInst(TerminalInst):
    retval: Operand

    def __init__(self, retval):
        self.retval = retval


class JumpInst(TerminalInst):
    label: str
    target: BasicBlock

    def __init__(self, label):
        self.label = label


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
