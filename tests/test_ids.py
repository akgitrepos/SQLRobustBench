from sqlrobustbench.ids import make_row_id


def test_make_row_id_is_stable():
    assert make_row_id("sqlcorrupt", "join", 12) == "sqlcorrupt_join_000012"
