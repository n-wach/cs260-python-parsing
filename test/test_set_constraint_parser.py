from analysis.set_constraints import SetConstraints, Call, Proj, SetVariable
from util import diff


def test_parser():
    text = """
    def constructor cons1, arity 2, contravariant positions 0 1
    def constructor cons2, arity 1, contravariant positions
    def constructor cons3, arity 0, contravariant positions
    def set variable var1
    def set variable var2
    call(cons2, var1) <= var2
    var1 <= proj(cons1, var2, 1)
    call(cons3) <= var1
    call(cons2, call(cons1, call(cons3), call(cons2, call(cons3)))) <= call(cons2, proj(cons2, var1, 0))
    """
    set_constraints = SetConstraints.parse(text)
    assert len(set_constraints.constructors) == 3
    assert len(set_constraints.set_variables) == 2
    assert len(set_constraints.constraints) == 4

    # call(cons2, var1) <= var2
    assert isinstance(set_constraints.constraints[0].left, Call)
    assert set_constraints.constraints[0].left.constructor is set_constraints.get_constructor("cons2")
    assert set_constraints.constraints[0].left.args[0] is set_constraints.get_set_variable("var1")
    assert isinstance(set_constraints.constraints[0].right, SetVariable)
    assert set_constraints.constraints[0].right is set_constraints.get_set_variable("var2")

    # var1 <= proj(cons1, var2, 1)
    assert isinstance(set_constraints.constraints[1].left, SetVariable)
    assert set_constraints.constraints[1].left is set_constraints.get_set_variable("var1")
    assert isinstance(set_constraints.constraints[1].right, Proj)
    assert set_constraints.constraints[1].right.constructor is set_constraints.get_constructor("cons1")
    assert set_constraints.constraints[1].right.var is set_constraints.get_set_variable("var2")
    assert set_constraints.constraints[1].right.index == 1

    # call(cons3) <= var1
    assert isinstance(set_constraints.constraints[2].left, Call)
    assert set_constraints.constraints[2].left.constructor is set_constraints.get_constructor("cons3")
    assert set_constraints.constraints[2].left.args == []
    assert isinstance(set_constraints.constraints[2].right, SetVariable)
    assert set_constraints.constraints[2].right is set_constraints.get_set_variable("var1")

    # call(cons2, call(cons1, call(cons3), call(cons2, call(cons3)))) <= call(cons2, proj(cons2, var1, 0))
    assert isinstance(set_constraints.constraints[3].left, Call)
    assert set_constraints.constraints[3].left.constructor is set_constraints.get_constructor("cons2")
    assert len(set_constraints.constraints[3].left.args) == 1
    assert isinstance(set_constraints.constraints[3].left.args[0], Call)
    assert set_constraints.constraints[3].left.args[0].constructor is set_constraints.get_constructor("cons1")
    assert len(set_constraints.constraints[3].left.args[0].args) == 2
    assert isinstance(set_constraints.constraints[3].left.args[0].args[0], Call)
    assert set_constraints.constraints[3].left.args[0].args[0].constructor is set_constraints.get_constructor("cons3")
    assert set_constraints.constraints[3].left.args[0].args[0].args == []
    assert isinstance(set_constraints.constraints[3].left.args[0].args[1], Call)
    assert set_constraints.constraints[3].left.args[0].args[1].constructor is set_constraints.get_constructor("cons2")
    assert len(set_constraints.constraints[3].left.args[0].args[1].args) == 1
    assert isinstance(set_constraints.constraints[3].left.args[0].args[1].args[0], Call)
    assert set_constraints.constraints[3].left.args[0].args[1].args[0].constructor is set_constraints.get_constructor("cons3")
    assert set_constraints.constraints[3].left.args[0].args[1].args[0].args == []
    assert isinstance(set_constraints.constraints[3].right, Call)
    assert set_constraints.constraints[3].right.constructor is set_constraints.get_constructor("cons2")
    assert len(set_constraints.constraints[3].right.args) == 1
    assert isinstance(set_constraints.constraints[3].right.args[0], Proj)
    assert set_constraints.constraints[3].right.args[0].constructor is set_constraints.get_constructor("cons2")
    assert set_constraints.constraints[3].right.args[0].var is set_constraints.get_set_variable("var1")
    assert set_constraints.constraints[3].right.args[0].index == 0

    clean_text = "\n".join(map(lambda s: s.strip(), text.splitlines()))
    d = diff(set_constraints.carl().strip(), clean_text.strip())
    print(d)
    assert d == ""


if __name__ == "__main__":
    test_parser()

