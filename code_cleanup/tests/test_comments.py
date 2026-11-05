from ..comments import space_comment


def test_puts_a_space_after_the_hash_of_a_word_comment() -> None:
    assert space_comment("#note") == "# note"
    assert space_comment("# note") == "# note"
    assert space_comment("#####") == "#####"
