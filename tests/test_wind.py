from mssdppg.wind.histogram import parse_histogram
from mssdppg.wind.weibull import bin_probabilities


def test_bin_probabilities_normalized():
    bins = bin_probabilities([1, 2, 3, 4, 5], k=2.0, c=8.0)
    total = sum(prob for _, prob in bins)
    assert abs(total - 1.0) < 1e-6


def test_parse_histogram():
    csv_text = "speed_mps,prob\n3,0.1\n4,0.2\n"
    parsed = parse_histogram(csv_text)
    assert parsed == [(3.0, 0.1), (4.0, 0.2)]
