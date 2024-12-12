from app.chart import generate_altair_colors


def test_generate_altair_colors_first_three() -> None:
    result = generate_altair_colors(3)
    expected_result = ["#346f9e", "#ffde56", "#2e7d32"]
    assert result == expected_result


def test_generate_altair_colors_more_than_three() -> None:
    result = len(generate_altair_colors(4))
    expected_result = 4
    assert result == expected_result
