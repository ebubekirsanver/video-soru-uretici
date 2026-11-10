"""Değerlendirme istatistikleri: elle hesaplanmış örnekler ve bağımsız kütüphanelerle karşılaştırma."""

import math

import numpy as np
import pytest
from scipy.stats import binomtest, wilcoxon
from statsmodels.stats.inter_rater import cohens_kappa
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.proportion import proportion_confint

from evaluation.stats import kappa, mcnemar_exact, paired_difference, wilcoxon_signed_rank, wilson


def labels_from(table, categories):
    a, b = [], []
    for i, row in enumerate(table):
        for j, count in enumerate(row):
            a += [categories[i]] * count
            b += [categories[j]] * count
    return a, b


# --- Kappa --------------------------------------------------------------------------


def test_kappa_hand_example():
    # po = 35/50 = 0,7; pe = 0,5·0,5 + 0,5·0,5 = 0,5; kappa = (0,7 - 0,5) / 0,5 = 0,4
    a, b = labels_from([[20, 5], [10, 15]], ["evet", "hayır"])
    result = kappa(a, b, ["evet", "hayır"])
    assert result["kappa"] == pytest.approx(0.4)
    assert result["agreement"] == pytest.approx(0.7)
    assert result["n"] == 50


@pytest.mark.parametrize("table", [[[20, 5], [10, 15]], [[7, 2, 1], [3, 9, 2], [0, 4, 12]], [[30, 1], [2, 3]]])
def test_kappa_and_se_match_statsmodels(table):
    categories = list(range(len(table)))
    a, b = labels_from(table, categories)
    result = kappa(a, b, categories)
    expected = cohens_kappa(np.array(table))
    assert result["kappa"] == pytest.approx(expected.kappa)
    assert result["se"] == pytest.approx(math.sqrt(expected.var_kappa))
    # statsmodels aynı normal yaklaşımı kullanır ama aralığı [-1, 1] içine kırpmaz
    assert result["ci_low"] == pytest.approx(max(-1, expected.kappa_low), abs=1e-3)
    assert result["ci_high"] == pytest.approx(min(1, expected.kappa_upp), abs=1e-3)


def test_weighted_kappa_hand_example():
    # 3 kategori; ağırlıklar 1, 0,5, 0. Satır ve sütun oranları 0,5 / 0,25 / 0,25
    table = [[2, 0, 0], [0, 1, 0], [0, 0, 1]]
    a, b = labels_from(table, [1, 2, 3])
    assert kappa(a, b, [1, 2, 3], weighted=True)["kappa"] == pytest.approx(1.0)

    # 4 soru: (1,1), (1,2), (2,2), (3,1). po = (1 + 0,5 + 1 + 0) / 4 = 0,625
    # Satır oranları 0,5 / 0,25 / 0,25; sütun oranları 0,5 / 0,5 / 0
    # pe = 0,5·(0,5 + 0,25) + 0,25·(0,25 + 0,5) + 0,25·(0 + 0,25) = 0,625; kappa = 0
    result = kappa([1, 1, 2, 3], [1, 2, 2, 1], [1, 2, 3], weighted=True)
    assert result["kappa"] == pytest.approx(0.0)


@pytest.mark.parametrize("table", [[[7, 2, 1], [3, 9, 2], [0, 4, 12]], [[5, 1, 0, 0], [2, 6, 1, 0], [0, 1, 4, 2], [1, 0, 2, 8]]])
def test_weighted_kappa_matches_statsmodels(table):
    categories = list(range(len(table)))
    a, b = labels_from(table, categories)
    assert kappa(a, b, categories, weighted=True)["kappa"] == pytest.approx(cohens_kappa(np.array(table), wt="linear").kappa)


def test_weighted_se_against_direct_formula():
    table = np.array([[7, 2, 1], [3, 9, 2], [0, 4, 12]], float)
    a, b = labels_from(table.astype(int).tolist(), [0, 1, 2])
    result = kappa(a, b, [0, 1, 2], weighted=True)
    # Fleiss, Cohen ve Everitt (1969), döngüyle açık yazım
    n = table.sum()
    p = table / n
    r, c = p.sum(1), p.sum(0)
    w = [[1 - abs(i - j) / 2 for j in range(3)] for i in range(3)]
    pe = sum(w[i][j] * r[i] * c[j] for i in range(3) for j in range(3))
    k = result["kappa"]
    total = 0.0
    for i in range(3):
        for j in range(3):
            wi = sum(c[m] * w[i][m] for m in range(3))
            wj = sum(r[m] * w[m][j] for m in range(3))
            total += p[i, j] * (w[i][j] - (wi + wj) * (1 - k)) ** 2
    variance = (total - (k - pe * (1 - k)) ** 2) / (n * (1 - pe) ** 2)
    assert result["se"] == pytest.approx(math.sqrt(variance))


def test_unused_category_changes_linear_weights():
    # Ağırlıklar kategori sırasından gelir: arada kullanılmayan kategori aralığı değiştirir
    a, b = [1, 2, 5, 1, 5], [2, 2, 5, 5, 2]
    assert kappa(a, b, [1, 2, 5], weighted=True)["kappa"] != pytest.approx(kappa(a, b, [1, 2, 3, 4, 5], weighted=True)["kappa"])


def test_kappa_single_category_is_undefined():
    result = kappa(["evet"] * 5, ["evet"] * 5, ["evet", "hayır"])
    assert result["kappa"] is None and result["ci_low"] is None and result["ci_high"] is None
    assert result["agreement"] == 1.0
    assert "tanımsız" in result["note"]


def test_kappa_perfect_agreement_two_categories_is_one():
    result = kappa(["evet", "hayır"] * 3, ["evet", "hayır"] * 3, ["evet", "hayır"])
    assert result["kappa"] == pytest.approx(1.0) and result["se"] == 0.0
    assert (result["ci_low"], result["ci_high"]) == (pytest.approx(1.0), pytest.approx(1.0))
    assert "standart hata 0" in result["note"]


def test_kappa_empty():
    result = kappa([], [], ["evet", "hayır"])
    assert result["kappa"] is None and result["agreement"] is None and result["note"] == "veri yok"


def test_kappa_alpha_changes_interval():
    a, b = labels_from([[20, 5], [10, 15]], ["evet", "hayır"])
    wide, narrow = kappa(a, b, ["evet", "hayır"], alpha=0.01), kappa(a, b, ["evet", "hayır"], alpha=0.10)
    assert wide["ci_low"] < narrow["ci_low"] and wide["ci_high"] > narrow["ci_high"]


# --- Wilson -------------------------------------------------------------------------


@pytest.mark.parametrize("k,n", [(0, 10), (10, 10), (7, 12), (1, 144), (100, 144)])
@pytest.mark.parametrize("alpha", [0.05, 0.10])
def test_wilson_matches_statsmodels(k, n, alpha):
    result = wilson(k, n, alpha)
    low, high = proportion_confint(k, n, alpha=alpha, method="wilson")
    assert result["ci_low"] == pytest.approx(low)
    assert result["ci_high"] == pytest.approx(high)
    assert result["rate"] == pytest.approx(k / n)


def test_wilson_no_data():
    assert wilson(0, 0) == {"k": 0, "n": 0, "rate": None, "ci_low": None, "ci_high": None}


# --- McNemar ------------------------------------------------------------------------


def test_mcnemar_hand_value():
    # 10 uyumsuz çift, 2'ye 8: p = 2·(1 + 10 + 45) / 1024
    result = mcnemar_exact(2, 8)
    assert result["p_value"] == pytest.approx(112 / 1024)
    assert result["discordant"] == 10 and result["first_only"] == 2 and result["second_only"] == 8


@pytest.mark.parametrize("b,c", [(2, 8), (8, 2), (5, 5), (0, 6), (13, 29)])
def test_mcnemar_matches_binomtest_and_statsmodels(b, c):
    result = mcnemar_exact(b, c)
    assert result["p_value"] == pytest.approx(binomtest(min(b, c), b + c, 0.5).pvalue)
    assert result["p_value"] == pytest.approx(mcnemar([[10, b], [c, 10]], exact=True).pvalue)


def test_mcnemar_no_discordant_pairs():
    result = mcnemar_exact(0, 0)
    assert result["p_value"] == 1.0 and result["discordant"] == 0 and "uyumsuz çift yok" in result["note"]


# --- Eşleştirilmiş oran farkı ---------------------------------------------------------


def test_paired_difference_against_explicit_formula():
    a, b, c, d = 12, 9, 2, 21
    n = a + b + c + d
    l1, u1 = proportion_confint(a + b, n, method="wilson")
    l2, u2 = proportion_confint(a + c, n, method="wilson")
    p1, p2 = (a + b) / n, (a + c) / n
    phi = (a * d - b * c) / math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    expected_low = (p1 - p2) - math.sqrt((p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2)
    expected_high = (p1 - p2) + math.sqrt((p2 - l2) ** 2 - 2 * phi * (p2 - l2) * (u1 - p1) + (u1 - p1) ** 2)
    result = paired_difference(a, b, c, d)
    assert result["difference"] == pytest.approx(7 / 44)
    assert result["ci_low"] == pytest.approx(expected_low)
    assert result["ci_high"] == pytest.approx(expected_high)
    assert result["ci_low"] < result["difference"] < result["ci_high"]


def test_paired_difference_no_discordant_contains_zero():
    result = paired_difference(10, 0, 0, 10)
    assert result["difference"] == 0 and result["ci_low"] <= 0 <= result["ci_high"]


def test_paired_difference_margin_zero_uses_phi_zero():
    # Bir koşulda hepsi evet: phi'nin paydası 0
    result = paired_difference(5, 0, 5, 0)
    assert result["difference"] == pytest.approx(-0.5) and -1 <= result["ci_low"] < -0.5 < result["ci_high"] <= 1


def test_paired_difference_empty():
    assert paired_difference(0, 0, 0, 0)["difference"] is None


# --- Wilcoxon -----------------------------------------------------------------------


def test_wilcoxon_hand_example_with_zero_and_ties():
    # 6 sıfır olmayan fark, hepsi aynı büyüklükte: sıralar 3,5. W+ = 17,5, W- = 3,5
    # Beklenen 10,5; varyans 22,75 - 210/48 = 18,375; Z = 7 / √18,375
    result = wilcoxon_signed_rank([1, 1, 1, 1, 1, -1, 0, 0])
    z = 7 / math.sqrt(18.375)
    assert result["pairs"] == 8 and result["zero_differences"] == 2 and result["n"] == 6
    assert (result["w_plus"], result["w_minus"]) == (17.5, 3.5)
    assert result["z"] == pytest.approx(z)
    assert result["r"] == pytest.approx(z / math.sqrt(6))


@pytest.mark.parametrize("d", [[1, 2, -1, 3, 0, 2, -2, 1, 4, 1], [1, 1, -2, -3, 2, 1, 1, 0, 0, 3, -1, 2]])
def test_wilcoxon_p_matches_scipy(d):
    expected = wilcoxon(d, zero_method="wilcox", correction=False, alternative="two-sided", method="asymptotic")
    assert wilcoxon_signed_rank(d)["p_value"] == pytest.approx(expected.pvalue)


def test_wilcoxon_sign_shows_direction():
    assert wilcoxon_signed_rank([1, 2, 3])["r"] > 0
    assert wilcoxon_signed_rank([-1, -2, -3])["r"] < 0


def test_wilcoxon_all_zero_and_empty():
    result = wilcoxon_signed_rank([0, 0, 0])
    assert result["p_value"] is None and result["r"] is None and result["zero_differences"] == 3
    assert "bütün farklar sıfır" in result["note"]
    assert wilcoxon_signed_rank([])["note"] == "veri yok"
