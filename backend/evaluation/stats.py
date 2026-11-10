"""Değerlendirme istatistikleri. Tanımsız durumlar hata vermez: değer None, `note` nedenini söyler.

Kappa ve güven aralığı (Fleiss, Cohen ve Everitt, 1969): basit ve ağırlıklı kappa
için aynı genel formül kullanılır. Uyum ağırlıkları w_ij (basitte birim matris,
doğrusalda 1 - |i-j| / (k-1)), satır ve sütun oranları r_i, c_j, gözlenen uyum
po = Σ w_ij p_ij, beklenen uyum pe = Σ w_ij r_i c_j, kappa = (po - pe) / (1 - pe).
Varyans = [Σ p_ij (w_ij - (w̄_i + w̄_j)(1 - κ))² - (κ - pe(1 - κ))²] / [n (1 - pe)²];
burada w̄_i = Σ_j c_j w_ij ve w̄_j = Σ_i r_i w_ij. Aralık κ ± z·SE, [-1, 1] içine
kırpılır. Bu büyük örneklem yaklaşımıdır; az soruda aralık güvenilir olmayabilir.

Eşleştirilmiş oran farkı için Newcombe (1998) 10. yöntem: iki oranın Wilson
aralıkları, çiftler arası phi korelasyonuyla birleştirilir. Wald aralığından farkı,
oran 0 ya da 1'e yakınken ve uyumsuz çift azken de makul sınır vermesidir.
"""

import math

import numpy as np
from scipy.stats import binomtest, norm, rankdata

from evaluation.common import DEFAULT_ALPHA


def z_value(alpha: float = DEFAULT_ALPHA) -> float:
    return float(norm.ppf(1 - alpha / 2))


def kappa(a: list, b: list, categories: list, weighted: bool = False, alpha: float = DEFAULT_ALPHA) -> dict:
    """İki değerlendiricinin etiketlerinden kappa ve aralık.

    `categories` sıralıdır ve kullanılmayanlar dahil bütün kategorileri içerir:
    doğrusal ağırlıklar kategori sırasına göre hesaplanır.

    Tanımsız durumlar:
    - Hiç veri yoksa kappa None.
    - İki değerlendirici de aynı tek kategoriyi kullandıysa beklenen uyum 1 olur,
      kappa 0/0'dır: None döner. Oransal uyum (`agreement`) yine 1 olarak verilir.
    Birden çok kategoride tam uyum varsa kappa 1 ve SE 0'dır; aralık [1; 1] olur.
    """
    n = len(a)
    if n != len(b):
        raise ValueError("Etiket listeleri aynı uzunlukta olmalı.")
    result = {"n": n, "kappa": None, "se": None, "ci_low": None, "ci_high": None, "agreement": None, "note": None}
    if n == 0:
        result["note"] = "veri yok"
        return result
    k = len(categories)
    index = {c: i for i, c in enumerate(categories)}
    counts = np.zeros((k, k))
    for x, y in zip(a, b):
        counts[index[x], index[y]] += 1
    p = counts / n
    row, col = p.sum(axis=1), p.sum(axis=0)
    w = np.eye(k)
    if weighted:
        steps = np.arange(k)
        w = 1 - np.abs(steps[:, None] - steps) / (k - 1)
    result["agreement"] = float(np.trace(p))
    po = float((w * p).sum())
    pe = float((w * np.outer(row, col)).sum())
    if abs(1 - pe) < 1e-12:
        result["note"] = "tanımsız: iki değerlendirici de tek kategori kullandı (beklenen uyum 1)"
        return result
    value = (po - pe) / (1 - pe)
    w_row = w @ col  # w̄_i
    w_col = row @ w  # w̄_j
    term = (p * (w - (w_row[:, None] + w_col[None, :]) * (1 - value)) ** 2).sum()
    variance = (term - (value - pe * (1 - value)) ** 2) / (n * (1 - pe) ** 2)
    se = math.sqrt(max(float(variance), 0.0))
    if se < 1e-12:
        se = 0.0
        result["note"] = "standart hata 0; aralık bilgi vermez"
    margin = z_value(alpha) * se
    result.update(kappa=float(value), se=se, ci_low=max(-1.0, value - margin), ci_high=min(1.0, value + margin))
    return result


def wilson(successes: int, n: int, alpha: float = DEFAULT_ALPHA) -> dict:
    """Oran ve Wilson aralığı; n = 0 ise oran ve aralık None."""
    if n == 0:
        return {"k": 0, "n": 0, "rate": None, "ci_low": None, "ci_high": None}
    z = z_value(alpha)
    rate = successes / n
    denominator = 1 + z**2 / n
    center = (rate + z**2 / (2 * n)) / denominator
    half = z * math.sqrt(rate * (1 - rate) / n + z**2 / (4 * n**2)) / denominator
    return {"k": successes, "n": n, "rate": rate, "ci_low": max(0.0, center - half), "ci_high": min(1.0, center + half)}


def mcnemar_exact(first_only: int, second_only: int) -> dict:
    """Kesin McNemar: uyumsuz çiftlerde iki yönlü binom testi (p = 0,5).

    Hiç uyumsuz çift yoksa iki koşul arasında fark gözlenmemiştir: p = 1.
    """
    discordant = first_only + second_only
    if discordant == 0:
        return {"first_only": 0, "second_only": 0, "discordant": 0, "p_value": 1.0, "note": "uyumsuz çift yok; p = 1"}
    p_value = binomtest(min(first_only, second_only), discordant, 0.5, alternative="two-sided").pvalue
    return {"first_only": first_only, "second_only": second_only, "discordant": discordant,
            "p_value": float(p_value), "note": None}


def paired_difference(both: int, first_only: int, second_only: int, neither: int, alpha: float = DEFAULT_ALPHA) -> dict:
    """Eşleştirilmiş iki oranın farkı (birinci - ikinci) ve Newcombe 10. yöntem aralığı.

    Phi'nin paydası 0 ise (ör. bir koşulda oran 0 ya da 1) phi 0 alınır (Newcombe, 1998).
    """
    n = both + first_only + second_only + neither
    if n == 0:
        return {"n": 0, "difference": None, "ci_low": None, "ci_high": None}
    first = wilson(both + first_only, n, alpha)
    second = wilson(both + second_only, n, alpha)
    p1, l1, u1 = first["rate"], first["ci_low"], first["ci_high"]
    p2, l2, u2 = second["rate"], second["ci_low"], second["ci_high"]
    denominator = (both + first_only) * (second_only + neither) * (both + second_only) * (first_only + neither)
    phi = (both * neither - first_only * second_only) / math.sqrt(denominator) if denominator else 0.0
    difference = p1 - p2
    low = difference - math.sqrt(max((p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2, 0.0))
    high = difference + math.sqrt(max((p2 - l2) ** 2 - 2 * phi * (p2 - l2) * (u1 - p1) + (u1 - p1) ** 2, 0.0))
    return {"n": n, "difference": difference, "ci_low": max(-1.0, low), "ci_high": min(1.0, high)}


def wilcoxon_signed_rank(differences: list[float]) -> dict:
    """Wilcoxon işaretli sıra testi ve etki büyüklüğü r = Z / √N.

    Sıfır farklar testten çıkarılır (Wilcoxon'un özgün yöntemi); N sıfır olmayan
    farkların sayısıdır ve sıfır fark sayısı ayrıca döner. Puanlar 1-5 olduğu için
    bağlar çoktur, kesin dağılım geçerli olmaz: bağ düzeltmeli normal yaklaşım,
    süreklilik düzeltmesiz kullanılır. Az çiftte p yaklaşıktır.
    Z ve r'nin işareti farkların yönünü gösterir (pozitif: birinci koşul yüksek).
    Bütün farklar sıfırsa test uygulanamaz: değerler None.
    """
    values = np.asarray(differences, float)
    nonzero = values[values != 0]
    n = len(nonzero)
    result = {"pairs": len(values), "zero_differences": len(values) - n, "n": n, "w_plus": None, "w_minus": None,
              "z": None, "p_value": None, "r": None, "note": None}
    if n == 0:
        result["note"] = "veri yok" if len(values) == 0 else "bütün farklar sıfır; test uygulanamadı"
        return result
    ranks = rankdata(np.abs(nonzero))
    w_plus = float(ranks[nonzero > 0].sum())
    w_minus = float(ranks[nonzero < 0].sum())
    _, tie_counts = np.unique(ranks, return_counts=True)
    variance = n * (n + 1) * (2 * n + 1) / 24 - float((tie_counts**3 - tie_counts).sum()) / 48
    z = (w_plus - n * (n + 1) / 4) / math.sqrt(variance)
    result.update(w_plus=w_plus, w_minus=w_minus, z=z, p_value=float(2 * norm.sf(abs(z))), r=z / math.sqrt(n))
    return result
