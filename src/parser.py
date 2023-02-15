from .ir import *
import re


class Parser:
    remaining_text: str
    address_taken_functions: Set[str]

    def __init__(self, text: str):
        self.remaining_text = text.strip()
        self.address_taken_functions = set()

    def consume(self, expression):
        result = re.match(f"^({expression})(.*)$", self.remaining_text, flags=re.DOTALL)
        if result is None:
            raise ValueError(f"Failed to consume '{expression}'")
        token, remaining = result.groups()
        self.remaining_text = remaining.lstrip()
        return token.strip()

    def lookahead_re(self, expression):
        result = re.match(f"^({expression})(.*)$", self.remaining_text, flags=re.DOTALL)
        return result is not None

    def lookahead(self, value):
        return self.remaining_text.startswith(value)

    def parse_program(self) -> Program:
        structs = self.parse_structs()
        functions = self.parse_functions()
        for func in functions:
            if func.name in self.address_taken_functions:
                func.address_taken = True
        return Program(structs, functions)

    def parse_structs(self) -> List[Struct]:
        structs = []
        while True:
            if not self.lookahead("struct"):
                break
            struct = self.parse_struct()
            structs.append(struct)
        return structs

    def parse_struct(self) -> Struct:
        self.consume("struct")
        name = self.parse_varname()
        self.consume(r"\{")
        fields = []
        while not self.lookahead("}"):
            field_name = self.parse_varname()
            self.consume(":")
            field_type = self.parse_type()
            fields.append(StructField(field_name, field_type))
        self.consume(r"\}")
        return Struct(name, fields)

    def parse_functions(self) -> List[Function]:
        functions = []
        while True:
            if not self.lookahead("function"):
                break
            function = self.parse_function()
            functions.append(function)
        return functions

    def parse_function(self) -> Function:
        self.consume("function")
        name = self.parse_varname()
        self.consume(r"\(")
        params = []
        while not self.lookahead(")"):
            param_name = self.parse_varname()
            self.consume(":")
            param_type = self.parse_type()
            params.append(Variable(param_name, param_type))
            if self.lookahead(","):
                self.consume(",")
        self.consume(r"\)")
        self.consume("->")
        return_type = self.parse_type()
        self.consume(r"\{")
        basic_blocks = []
        while not self.lookahead("}"):
            basic_blocks.append(self.parse_basic_block())
        self.consume(r"\}")
        return Function(name, return_type, params, basic_blocks)

    def parse_basic_block(self) -> BasicBlock:
        label = self.parse_label()
        self.consume(":")
        instructions = []
        while True:
            instruction = self.parse_instruction()
            instructions.append(instruction)
            if isinstance(instruction, TerminalInst):
                break
        return BasicBlock(label, instructions)

    def parse_instruction(self) -> Instruction:
        if self.lookahead("$"):
            opcode = self.parse_opcode()

            if opcode == "store":
                value = self.parse_operand()
                address = self.parse_operand()
                return StoreInst(value, address)

            if opcode == "ret":
                operand = self.parse_operand()
                return RetInst(operand)

            if opcode == "jump":
                label = self.parse_label()
                return JumpInst(label)

            if opcode == "branch":
                condition = self.parse_operand()
                true_label = self.parse_label()
                false_label = self.parse_label()
                return BranchInst(condition, true_label, false_label)

            raise ValueError(f"Unknown instruction '{opcode}'")

        lhs = self.parse_variable()
        self.consume("=")
        opcode = self.parse_opcode()
        if opcode == "icall":
            function = self.parse_operand()
            self.consume(r"\(")
            args = []
            while not self.lookahead(")"):
                args.append(self.parse_operand())
                if self.lookahead(","):
                    self.consume(",")
            self.consume(r"\)")
            return ICallInst(lhs, function, args)

        if opcode == "call":
            function = self.parse_varname()
            self.consume(r"\(")
            args = []
            while not self.lookahead(")"):
                args.append(self.parse_operand())
                if self.lookahead(","):
                    self.consume(",")
            self.consume(r"\)")
            return CallInst(lhs, function, args)

        if opcode == "select":
            condition = self.parse_operand()
            true_op = self.parse_operand()
            false_op = self.parse_operand()
            return SelectInst(lhs, condition, true_op, false_op)

        if opcode == "gep":
            src = self.parse_operand()
            index = self.parse_operand()
            field_name = ""
            if self.lookahead_re(r"[\w\.]+\s"):  # field name, no type
                field_name = self.parse_varname()
            return GepInst(lhs, src, index, field_name)

        if opcode == "load":
            src = self.parse_operand()
            return LoadInst(lhs, src)

        if opcode == "addrof":
            rhs = self.parse_operand()
            return AddrofInst(lhs, rhs)

        if opcode == "alloc":
            return AllocInst(lhs)

        if opcode == "copy":
            rhs = self.parse_operand()
            return CopyInst(lhs, rhs)

        if opcode == "phi":
            self.consume(r"\(")
            args = []
            while not self.lookahead(")"):
                args.append(self.parse_operand())
                if self.lookahead(","):
                    self.consume(",")
            self.consume(r"\)")
            return PhiInst(lhs, args)

        if opcode == "cmp":
            operation = self.parse_rop()
            left_op = self.parse_operand()
            right_op = self.parse_operand()
            return CmpInst(lhs, left_op, right_op, operation)

        if opcode == "arith":
            operation = self.parse_aop()
            left_op = self.parse_operand()
            right_op = self.parse_operand()
            return ArithInst(lhs, left_op, right_op, operation)

        raise ValueError(f"Unknown instruction '{opcode}'")

    def parse_rop(self) -> Rop:
        rop = self.consume(r"\w+")
        return Rop(rop)

    def parse_aop(self) -> Aop:
        aop = self.consume(r"\w+")
        return Aop(aop)

    def parse_operand(self) -> Operand:
        if self.lookahead_re(r"-?\d+"):
            return self.parse_const_int()
        if self.lookahead("@nullptr"):
            return self.parse_const_nullptr()
        if self.lookahead("@"):
            return self.parse_const_func()
        return VarOperand(self.parse_variable())

    def parse_opcode(self) -> str:
        self.consume(r"\$")
        return self.consume(r"\w+")

    def parse_varname(self) -> str:
        return self.consume(r"[\w\.]+")

    def parse_label(self) -> str:
        return self.consume(r"[\w\.]+")

    def parse_type(self):
        type_ = self.consume(r"[\w\[\]\*,]+[\s\(\),]")
        if type_[-1] in "(),":
            self.remaining_text = type_[-1] + self.remaining_text
            type_ = type_[:-1]
        indirection = 0
        while type_.endswith("*"):
            indirection += 1
            type_ = type_[:-1]
        return Type(type_, indirection)

    def parse_const_int(self) -> ConstIntOperand:
        value = self.consume(r"-?\d+")
        return ConstIntOperand(int(value))

    def parse_const_nullptr(self) -> ConstNullPtrOperand:
        self.consume("@nullptr")
        self.consume(":")
        type_ = self.parse_type()
        return ConstNullPtrOperand(type_)

    def parse_const_func(self) -> ConstFuncOperand:
        self.consume("@")
        name = self.parse_varname()
        self.consume(":")
        type_ = self.parse_type()
        self.address_taken_functions.add(name)
        return ConstFuncOperand(name, type_)

    def parse_variable(self) -> Variable:
        name = self.parse_varname()
        self.consume(":")
        type_ = self.parse_type()
        return Variable(name, type_)


if __name__ == "__main__":
    import sys
    import glob

    for path in glob.glob(sys.argv[1]):
        with open(path, "r") as f:
            ir_text = f.read()

        prog = Parser(ir_text).parse_program()
        print(f"Parsed '{path}' without errors")
