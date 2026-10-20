"""Soru yazım hatalarının kodla kontrol edilebilen kısmı (Aşama 9, b).

Kaynak: Moore vd. (2023), arXiv 2307.08161, Tablo 1'deki 19 maddelik liste.
Kuralların Türkçe tanımları ve sınırları: docs/soru-yazim-hatalari.md.

Kurallar yalnızca İŞARETLER, soru atılmaz. Sonuç yalnızca çalıştırma kaydına
yazılır, API yanıtına girmez. Kontrol, seçenekler karıştırıldıktan sonraki
son sorular üzerinde çalışır (correct_index karıştırılmış sıraya göredir).

Listenin 1, 2, 5, 7, 8, 13, 15 ve 18. maddeleri bu sürümde kontrol edilmez
(model gerektirir ya da Türkçede güvenilir bir kural yok).
"""

import re
from dataclasses import asdict, dataclass

from app.services.quotes import normalize

# Kurallar ya da anahtar kelime listeleri değişirse sürüm artar (writing-rules-v2)
RULES_VERSION = "writing-rules-v1"

# Bu sürümde kodla kontrol edilen maddeler (numara: Moore vd. Tablo 1'deki ad)
RULE_NAMES = {
    3: "None of the above",
    4: "Longest option correct",
    6: "True/false question",
    9: "All of the above",
    10: "Fill-in-blank",
    11: "Absolute terms",
    12: "Word repeats",
    14: "Complex or K-type",
    16: "Lost sequence",
    17: "Vague terms",
    19: "Negative worded",
}

# --- Anahtar kelime listeleri (normalize edilmiş: Türkçe küçük harf, noktalamasız) ---

# 3 ve 9: seçenekten bu dolgu kelimeleri çıkınca geriye yalnızca hedef kelime kalıyorsa işaretlenir
FILLER_WORDS = {
    "yukarıdakilerin", "yukarıdaki", "seçeneklerin", "verilenlerin",
    "de", "da", "doğru", "doğrudur", "değil", "değildir",
}
NONE_OF_ABOVE_WORDS = {"hiçbiri", "hiçbirisi", "hiçbiridir"}
ALL_OF_ABOVE_WORDS = {"hepsi", "hepsidir", "tümü", "tümüdür"}

# 4: doğru seçenek en uzun ve ikinci en uzundan en az bu oranda uzunsa (karakter, normalize edilmiş)
LONGEST_RATIO = 1.3

# 6: en az bu kadar seçenek doğru-yanlış ifadesinden ibaretse
TRUE_FALSE_WORDS = {"doğru", "yanlış", "doğrudur", "yanlıştır", "evet", "hayır"}
TRUE_FALSE_MIN_OPTIONS = 2

# 11: kesin ifadeler (seçeneklerde, tam kelime ya da kelime öbeği olarak)
ABSOLUTE_TERMS = (
    "her zaman", "hiçbir zaman", "asla", "daima", "kesinlikle", "mutlaka",
    "tümü", "tamamı", "hiçbir",
)

# 17: belirsiz ifadeler (seçeneklerde, tam kelime ya da kelime öbeği olarak)
VAGUE_TERMS = (
    "bazen", "genellikle", "genelde", "sıklıkla", "çoğunlukla", "nadiren",
    "ara sıra", "zaman zaman", "çoğu zaman",
)

# 19: soru kökünde olumsuzluk. Tam kelimeler ve kelime sonu ekleri.
NEGATIVE_WORDS = {"değil", "değildir", "olmayan", "olmaz", "yoktur", "yanlıştır"}
NEGATIVE_SUFFIXES = (
    "maz", "mez", "mazlar", "mezler",
    "mayan", "meyen", "madığı", "mediği", "mamış", "memiş",
    "mamaktadır", "memektedir",
)

# 12: soru kökündeki içerik kelimeleri; bu kelimeler ve 4 harften kısa kelimeler sayılmaz
STEM_STOPWORDS = {
    "aşağıdakilerden", "aşağıdaki", "hangisi", "hangisidir", "hangi", "nedir", "neden",
    "nasıl", "nelerdir", "kaçtır", "için", "olarak", "göre", "gibi", "kadar", "daha",
    "olan", "olur", "olduğu", "olduğunu", "videoda", "videodaki", "anlatılan",
    "anlatıldığına", "belirtilen", "söylenen", "bahsedilen", "hakkında", "ilgili",
    "doğru", "doğrudur", "yanlış", "yanlıştır", "değil", "değildir", "verilen",
}
WORD_REPEAT_MIN_LEN = 4
WORD_REPEAT_PREFIX = 5  # Türkçe ekler yüzünden kelimeler ilk 5 harfle (kısaysa tamamıyla) karşılaştırılır

# 10: alt çizgi (__ ve fazlası), üç ya da daha fazla nokta, üç nokta karakteri
_BLANK = re.compile(r"_{2,}|\.{3,}|…")
_WORD = re.compile(r"\w", re.UNICODE)

# 14: Romen rakamı ya da büyük harfle gösterilen öncüllerin birleşimi ("I ve II", "A, B ve C", "Yalnız I").
# Özgün yazımla aranır (küçük harfe çevirmek "I" harfini "ı" yapar).
_PREMISE = r"(?:IV|V|I{1,3}|[A-E])"
_K_TYPE_PAIR = re.compile(rf"(?<!\w){_PREMISE}\s*(?:,|ve|veya|ile)\s*{_PREMISE}(?!\w)")
_K_TYPE_ONLY = re.compile(rf"^\s*(?:Yalnız|Yalnızca|Sadece)\s+{_PREMISE}(?!\w)", re.IGNORECASE)

# 16: önünde/arkasında aynı metin olan tek bir sayı ("1923", "%20", "350 °C", "1923 yılında")
_NUMBER_OPTION = re.compile(r"^(\D*?)(-?\d+(?:[.,]\d+)?)(\D*)$")


@dataclass
class WritingFlag:
    rule_id: int
    rule_name: str
    detail: str


def _flag(rule_id: int, detail: str) -> WritingFlag:
    return WritingFlag(rule_id=rule_id, rule_name=RULE_NAMES[rule_id], detail=detail)


def _contains_term(normalized: str, term: str) -> bool:
    """Tam kelime ya da kelime öbeği olarak geçiyor mu (ek almış hâller sayılmaz)."""
    return f" {term} " in f" {normalized} "


def _core_words(option: str) -> set[str]:
    return set(normalize(option).split()) - FILLER_WORDS


def _check_none_all(options: list[str]) -> list[WritingFlag]:
    flags = []
    for i, opt in enumerate(options):
        core = _core_words(opt)
        if core and core <= NONE_OF_ABOVE_WORDS:
            flags.append(_flag(3, f"Seçenek {i + 1}: {opt!r}"))
        elif core and core <= ALL_OF_ABOVE_WORDS:
            flags.append(_flag(9, f"Seçenek {i + 1}: {opt!r}"))
    return flags


def _check_longest(options: list[str], correct_index: int) -> list[WritingFlag]:
    lengths = [len(normalize(o)) for o in options]
    correct = lengths[correct_index]
    others = [n for i, n in enumerate(lengths) if i != correct_index]
    if not others:
        return []
    second = max(others)
    if correct > second and correct >= LONGEST_RATIO * second:
        return [_flag(4, f"Doğru seçenek {correct} karakter, en uzun çeldirici {second} karakter")]
    return []


def _check_true_false(options: list[str]) -> list[WritingFlag]:
    tf = [o for o in options if normalize(o) in TRUE_FALSE_WORDS]
    if len(tf) >= TRUE_FALSE_MIN_OPTIONS:
        return [_flag(6, "Doğru-yanlış seçenekleri: " + ", ".join(repr(o) for o in tf))]
    return []


def _check_blank(question: str) -> list[WritingFlag]:
    for m in _BLANK.finditer(question):
        # Kökün sonundaki üç nokta boşluk sayılmaz; ardından kelime gelmeli
        if _WORD.search(question[m.end():]):
            return [_flag(10, f"Soru kökünde boşluk: {m.group()!r}")]
    return []


def _check_terms(options: list[str], terms: tuple[str, ...], rule_id: int) -> list[WritingFlag]:
    found = []
    for i, opt in enumerate(options):
        norm = normalize(opt)
        if rule_id == 11 and _core_words(opt) <= ALL_OF_ABOVE_WORDS | NONE_OF_ABOVE_WORDS:
            continue  # "Tümü" tek başına 9. maddedir, burada tekrar sayılmaz
        hits = [t for t in terms if _contains_term(norm, t)]
        if hits:
            found.append(f"Seçenek {i + 1}: {', '.join(hits)}")
    return [_flag(rule_id, "; ".join(found))] if found else []


def _check_k_type(options: list[str]) -> list[WritingFlag]:
    hits = [f"Seçenek {i + 1}: {o!r}" for i, o in enumerate(options) if _K_TYPE_PAIR.search(o) or _K_TYPE_ONLY.search(o)]
    return [_flag(14, "; ".join(hits))] if hits else []


def _parse_number_option(option: str) -> tuple[str, float, str] | None:
    m = _NUMBER_OPTION.match(option.strip())
    if not m:
        return None
    return normalize(m.group(1)), float(m.group(2).replace(",", ".")), normalize(m.group(3))


def _check_sequence(options: list[str]) -> list[WritingFlag]:
    parsed = [_parse_number_option(o) for o in options]
    if any(p is None for p in parsed):
        return []
    # Önündeki ve arkasındaki metin bütün seçeneklerde aynı olmalı (aynı birim)
    if len({(p[0], p[2]) for p in parsed}) != 1:
        return []
    values = [p[1] for p in parsed]
    if len(set(values)) < 2 or values == sorted(values) or values == sorted(values, reverse=True):
        return []
    return [_flag(16, "Sayısal seçenekler sıralı değil: " + ", ".join(o.strip() for o in options))]


def _is_negative(word: str) -> bool:
    return word in NEGATIVE_WORDS or any(word.endswith(s) and len(word) > len(s) + 1 for s in NEGATIVE_SUFFIXES)


def _check_negative(question: str) -> list[WritingFlag]:
    hits = [w for w in normalize(question).split() if _is_negative(w)]
    return [_flag(19, "Olumsuz ifade: " + ", ".join(hits))] if hits else []


def _prefix(word: str) -> str:
    return word[:WORD_REPEAT_PREFIX]


def _check_word_repeats(question: str, options: list[str], correct_index: int) -> list[WritingFlag]:
    stem_words = {
        w for w in normalize(question).split()
        if len(w) >= WORD_REPEAT_MIN_LEN and w not in STEM_STOPWORDS
    }
    stem_prefixes = {_prefix(w): w for w in stem_words}
    option_prefixes = [{_prefix(w) for w in normalize(o).split() if len(w) >= WORD_REPEAT_MIN_LEN} for o in options]
    distractor_prefixes = set().union(*(p for i, p in enumerate(option_prefixes) if i != correct_index))
    only_correct = sorted(
        stem_prefixes[p] for p in option_prefixes[correct_index] & stem_prefixes.keys() if p not in distractor_prefixes
    )
    if only_correct:
        return [_flag(12, "Kökteki kelime yalnızca doğru seçenekte tekrar ediyor: " + ", ".join(only_correct))]
    return []


def check_question(question: str, options: list[str], correct_index: int) -> list[WritingFlag]:
    """Tek bir sorunun yazım kurallarını kontrol eder; işaretleri madde numarası sırasıyla döndürür."""
    flags = (
        _check_none_all(options)
        + _check_longest(options, correct_index)
        + _check_true_false(options)
        + _check_blank(question)
        + _check_terms(options, ABSOLUTE_TERMS, 11)
        + _check_word_repeats(question, options, correct_index)
        + _check_k_type(options)
        + _check_sequence(options)
        + _check_terms(options, VAGUE_TERMS, 17)
        + _check_negative(question)
    )
    return sorted(flags, key=lambda f: f.rule_id)


def check_questions(questions: list) -> dict:
    """Karıştırılmış son sorular için kayda yazılacak `writing_check` alanı."""
    return {
        "rules_version": RULES_VERSION,
        "results": [
            {
                "index": i,
                "question": q.question,
                "flags": [asdict(f) for f in check_question(q.question, q.options, q.correct_index)],
            }
            for i, q in enumerate(questions, 1)
        ],
    }
