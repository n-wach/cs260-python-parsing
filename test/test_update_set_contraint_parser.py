from set_constraints import SetConstraints, Call, Proj, SetVariable
# from util import diff


def test_parser():
    text = """
    def constructor c1, arity 1, contravariant positions
    def constructor c2, arity 0, contravariant positions
    def constructor c3, arity 2, contravariant positions 1
    def constructor c4, arity 1, contravariant positions
    def constructor c5, arity 3, contravariant positions 0 1 2
    call(c1, C1) <= V1
    V1 <= v2
    call(c2) <= proj(c1, v2, 0)
    proj(c1, v2, 0) <= v3
    call(c3, call(c4, x), y) <= call(c3, a, call(c2))
    call(c5, a, b, c) <= call(c5, call(c2), call(c2), call(c2))
    V1 <= a
    v2 <= b
    """
    text_with_set_def = """
    def constructor c1, arity 1, contravariant positions
    def constructor c2, arity 0, contravariant positions
    def constructor c3, arity 2, contravariant positions 1
    def constructor c4, arity 1, contravariant positions
    def constructor c5, arity 3, contravariant positions 0 1 2
    def set variable C1
    def set variable V1
    def set variable v2
    def set variable v3
    def set variable x
    def set variable y
    def set variable a
    def set variable b
    def set variable c
    call(c1, C1) <= V1
    V1 <= v2
    call(c2) <= proj(c1, v2, 0)
    proj(c1, v2, 0) <= v3
    call(c3, call(c4, x), y) <= call(c3, a, call(c2))
    call(c5, a, b, c) <= call(c5, call(c2), call(c2), call(c2))
    V1 <= a
    v2 <= b
    """
    set_constraints = SetConstraints.parse(text)
    assert len(set_constraints.constructors) == 5
    assert len(set_constraints.set_variables) == 9
    assert len(set_constraints.constraints) == 8

    # call(c1, C1) <= V1
    assert isinstance(set_constraints.constraints[0].left, Call)
    assert set_constraints.constraints[0].left.constructor is set_constraints.get_constructor("c1")
    assert set_constraints.constraints[0].left.args[0] is set_constraints.get_set_variable("C1")
    assert isinstance(set_constraints.constraints[0].right, SetVariable)
    assert set_constraints.constraints[0].right is set_constraints.get_set_variable("V1")
    
    # V1 <= v2
    assert isinstance(set_constraints.constraints[1].left, SetVariable)
    assert set_constraints.constraints[1].left is set_constraints.get_set_variable("V1")
    assert isinstance(set_constraints.constraints[1].right, SetVariable)
    assert set_constraints.constraints[1].right is set_constraints.get_set_variable("v2")

    # call(c2) <= proj(c1, v2, 0)
    assert isinstance(set_constraints.constraints[2].left, Call)
    assert set_constraints.constraints[2].left.constructor is set_constraints.get_constructor("c2")
    assert set_constraints.constraints[2].left.args == []
    assert isinstance(set_constraints.constraints[2].right, Proj)
    assert set_constraints.constraints[2].right.constructor is set_constraints.get_constructor("c1")
    assert set_constraints.constraints[2].right.var is set_constraints.get_set_variable("v2")
    assert set_constraints.constraints[2].right.index == 0

    # proj(c1, v2, 0) <= v3
    assert isinstance(set_constraints.constraints[3].left, Proj)
    assert set_constraints.constraints[3].left.constructor is set_constraints.get_constructor("c1")
    assert set_constraints.constraints[3].left.var is set_constraints.get_set_variable("v2")
    assert set_constraints.constraints[3].left.index == 0
    assert isinstance(set_constraints.constraints[3].right, SetVariable)
    assert set_constraints.constraints[3].right is set_constraints.get_set_variable("v3")

    # call(c3, call(c4, x), y) <= call(c3, a, call(c2))
    assert isinstance(set_constraints.constraints[4].left, Call)
    assert set_constraints.constraints[4].left.constructor is set_constraints.get_constructor("c3")
    assert len(set_constraints.constraints[4].left.args) == 2
    assert isinstance(set_constraints.constraints[4].left.args[0], Call)
    assert set_constraints.constraints[4].left.args[0].constructor is set_constraints.get_constructor("c4")
    assert len(set_constraints.constraints[4].left.args[0].args) == 1
    assert set_constraints.constraints[4].left.args[0].args[0] is set_constraints.get_set_variable("x")
    assert isinstance(set_constraints.constraints[4].left.args[1], SetVariable)
    assert set_constraints.constraints[4].left.args[1] is set_constraints.get_set_variable("y")

    assert isinstance(set_constraints.constraints[4].right, Call)
    assert set_constraints.constraints[4].right.constructor is set_constraints.get_constructor("c3")
    assert len(set_constraints.constraints[4].right.args) == 2
    assert isinstance(set_constraints.constraints[4].right.args[0], SetVariable)
    assert set_constraints.constraints[4].right.args[0] is set_constraints.get_set_variable("a")
    assert isinstance(set_constraints.constraints[4].right.args[1], Call)
    assert set_constraints.constraints[4].right.args[1].constructor is set_constraints.get_constructor("c2")
    assert set_constraints.constraints[4].right.args[1].args == []


    # call(c5, a, b, c) <= call(c5, call(c2), call(c2), call(c2))
    # index 5
    assert isinstance(set_constraints.constraints[5].left, Call)
    assert set_constraints.constraints[5].left.constructor is set_constraints.get_constructor("c5")
    assert len(set_constraints.constraints[5].left.args) == 3
    assert set_constraints.constraints[5].left.args[0] is set_constraints.get_set_variable("a")
    assert set_constraints.constraints[5].left.args[1] is set_constraints.get_set_variable("b")
    assert set_constraints.constraints[5].left.args[2] is set_constraints.get_set_variable("c")

    assert isinstance(set_constraints.constraints[5].right, Call)
    assert set_constraints.constraints[5].right.constructor is set_constraints.get_constructor("c5")
    assert len(set_constraints.constraints[5].right.args) == 3
    assert isinstance(set_constraints.constraints[5].right.args[0], Call)
    assert set_constraints.constraints[5].right.args[1].constructor is set_constraints.get_constructor("c2")
    assert set_constraints.constraints[5].right.args[1].args == []
    assert isinstance(set_constraints.constraints[5].right.args[1], Call)
    assert set_constraints.constraints[5].right.args[1].constructor is set_constraints.get_constructor("c2")
    assert set_constraints.constraints[5].right.args[1].args == []
    assert isinstance(set_constraints.constraints[5].right.args[2], Call)
    assert set_constraints.constraints[5].right.args[1].constructor is set_constraints.get_constructor("c2")
    assert set_constraints.constraints[5].right.args[1].args == []


    # V1 <= a
    assert isinstance(set_constraints.constraints[6].left, SetVariable)
    assert set_constraints.constraints[6].left is set_constraints.get_set_variable("V1")
    assert isinstance(set_constraints.constraints[6].right, SetVariable)
    assert set_constraints.constraints[6].right is set_constraints.get_set_variable("a")
    
    # v2 <= b
    assert isinstance(set_constraints.constraints[7].left, SetVariable)
    assert set_constraints.constraints[7].left is set_constraints.get_set_variable("v2")
    assert isinstance(set_constraints.constraints[7].right, SetVariable)
    assert set_constraints.constraints[7].right is set_constraints.get_set_variable("b")

    clean_text = "\n".join(map(lambda s: s.strip(), text_with_set_def.splitlines()))
    # d = diff(set_constraints.carl().strip(), clean_text.strip())
    d = set_constraints.carl().strip()
    print(d)
    assert d == clean_text.strip()


if __name__ == "__main__":
    test_parser()

