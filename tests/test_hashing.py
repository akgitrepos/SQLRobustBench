from sqlrobustbench.hashing import stable_hash


def test_stable_hash_order_independent_for_dict_keys():
    a = stable_hash({"x": 1, "y": 2})
    b = stable_hash({"y": 2, "x": 1})
    assert a == b
