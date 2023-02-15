from analysis.set_constraints import SetConstraints, Call, Proj, SetVariable
from util import diff


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
    set_constraints = SetConstraints.parse(text)
    assert len(set_constraints.constructors) == 5
    assert len(set_constraints.set_variables) == 9
    assert len(set_constraints.constraints) == 8

    # check some things...
    assert set_constraints.constraints[0].left.constructor is set_constraints.get_constructor("c1")
    assert set_constraints.constraints[0].right is set_constraints.get_set_variable("V1")

    assert set_constraints.constraints[2].right.constructor is set_constraints.get_constructor("c1")
    assert set_constraints.constraints[2].right.var is set_constraints.get_set_variable("v2")

    assert set_constraints.constraints[5].right.args[2].constructor is set_constraints.get_constructor("c2")

    # check that the output is the same (ignoring white space)
    clean_text = "\n".join(map(lambda s: s.strip(), text.splitlines()))
    d = diff(set_constraints.to_text().strip(), clean_text.strip())
    assert d == ""


if __name__ == "__main__":
    test_parser()

