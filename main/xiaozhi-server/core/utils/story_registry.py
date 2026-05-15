"""
StoryRegistry — Dynamic story catalog auto-populated from Qdrant.

Replaces the hardcoded _KNOWN_STORIES list. Generates Vietnamese ASR-variant
aliases automatically so new stories are fuzzy-matchable without code changes.

Usage:
    from core.utils.story_registry import story_registry

    # Build (call once at startup or after document changes)
    await story_registry.build(qdrant_provider)

    # Fuzzy match a garbled ASR query
    canonical, story_id = story_registry.fuzzy_match("chầu câu")
"""

import json
import os
import re
import threading
import unicodedata
from itertools import product
from typing import Dict, List, Optional, Tuple

from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

# Vietnamese ASR confusion pairs: correct → common ASR mis-transcriptions.
# Each tuple is (correct_substring, [wrong_variants]).
# Applied at the syllable level after splitting on spaces.
_ONSET_CONFUSIONS: List[Tuple[str, List[str]]] = [
    ("tr", ["ch", "t"]),
    ("ch", ["tr"]),
    ("gi", ["d", "z"]),
    ("d", ["gi", "z"]),
    ("s", ["x"]),
    ("x", ["s"]),
    ("kh", ["k"]),
    ("ng", ["n"]),
    ("nh", ["n"]),
    ("th", ["t"]),
    ("ph", ["f"]),
]

# Vowel / rhyme confusions (substring replace inside syllable)
_VOWEL_CONFUSIONS: List[Tuple[str, List[str]]] = [
    ("ầu", ["âu", "au"]),
    ("âu", ["ầu", "au"]),
    ("au", ["âu", "ầu"]),
    ("ưa", ["ua"]),
    ("ua", ["ưa"]),
    ("ươ", ["uo"]),
    ("iê", ["ie", "yê"]),
    ("ê", ["e"]),
    ("ư", ["u"]),
    ("ơ", ["o"]),
    ("ô", ["o"]),
    ("ầ", ["â", "a"]),
    ("ấ", ["â", "a"]),
    ("ắ", ["a"]),
    ("ả", ["a"]),
    ("à", ["a"]),
    ("á", ["a"]),
    ("ã", ["a"]),
    ("ồ", ["o"]),
    ("ố", ["o"]),
    ("ổ", ["o"]),
    ("ỗ", ["o"]),
    ("ù", ["u"]),
    ("ú", ["u"]),
    ("ủ", ["u"]),
    ("ũ", ["u"]),
    ("ụ", ["u"]),
    ("ừ", ["u"]),
    ("ứ", ["u"]),
    ("ử", ["u"]),
    ("ữ", ["u"]),
    ("ự", ["u"]),
    ("è", ["e"]),
    ("é", ["e"]),
    ("ẻ", ["e"]),
    ("ẽ", ["e"]),
    ("ề", ["e"]),
    ("ế", ["e"]),
    ("ể", ["e"]),
    ("ễ", ["e"]),
    ("ì", ["i"]),
    ("í", ["i"]),
    ("ỉ", ["i"]),
    ("ĩ", ["i"]),
    ("ị", ["i"]),
    ("ò", ["o"]),
    ("ó", ["o"]),
    ("ỏ", ["o"]),
    ("õ", ["o"]),
    ("ọ", ["o"]),
]

_SU_TICH_PREFIXES = re.compile(
    r"^(sự tích|sự thích|sở thích|sử thích|sư tích|sứ tích|su tich"
    r"|cổ tích|co tich|cỗ tích)\s*"
)


def _generate_onset_variants(syllable: str) -> List[str]:
    """Generate onset-confusion variants for a single Vietnamese syllable."""
    variants = set()
    s_lower = syllable.lower()
    for correct, wrongs in _ONSET_CONFUSIONS:
        if s_lower.startswith(correct):
            rest = s_lower[len(correct):]
            for w in wrongs:
                variants.add(w + rest)
    return list(variants)


def _generate_vowel_variants(syllable: str) -> List[str]:
    """Generate vowel/tone-confusion variants for a single syllable."""
    variants = set()
    s_lower = syllable.lower()
    for correct, wrongs in _VOWEL_CONFUSIONS:
        if correct in s_lower:
            for w in wrongs:
                variants.add(s_lower.replace(correct, w, 1))
    return list(variants)


def _generate_syllable_variants(syllable: str) -> List[str]:
    """All plausible ASR mis-transcription variants for one syllable."""
    s = syllable.lower()
    variants = {s}
    variants.update(_generate_onset_variants(s))
    variants.update(_generate_vowel_variants(s))
    return list(variants)


def generate_aliases(canonical_name: str, max_aliases: int = 40) -> List[str]:
    """Generate ASR-variant aliases for a Vietnamese story name.

    Given "sự tích trầu cau", produces aliases like:
    ["trầu cau", "chầu cau", "chầu câu", "trâu cau", ...]

    The canonical name itself (with and without "sự tích" prefix) is always
    included. Per-syllable variants are combined pairwise (not full cartesian
    product) to keep the list manageable.
    """
    name_lower = canonical_name.lower().strip()

    # Strip "sự tích" prefix to get the core name
    core = _SU_TICH_PREFIXES.sub("", name_lower).strip()
    if not core:
        core = name_lower

    syllables = core.split()
    aliases = set()

    # Always include the core and full name
    aliases.add(core)
    aliases.add(name_lower)

    if len(syllables) == 1:
        aliases.update(_generate_syllable_variants(syllables[0]))
        return list(aliases)[:max_aliases]

    # Generate per-syllable variant lists
    per_syllable = [_generate_syllable_variants(s) for s in syllables]

    # Pairwise substitution: vary one syllable at a time, keep others original
    for i, variants in enumerate(per_syllable):
        for v in variants:
            parts = list(syllables)
            parts[i] = v
            aliases.add(" ".join(parts))

    # Limited 2-syllable combinations for short names (2-3 syllables)
    if len(syllables) <= 3:
        for i in range(len(syllables)):
            for j in range(i + 1, len(syllables)):
                for vi in per_syllable[i][:3]:
                    for vj in per_syllable[j][:3]:
                        parts = list(syllables)
                        parts[i] = vi
                        parts[j] = vj
                        aliases.add(" ".join(parts))
                        if len(aliases) >= max_aliases:
                            return list(aliases)

    return list(aliases)[:max_aliases]


def _strip_diacritics(text: str) -> str:
    """Remove Vietnamese diacritics via NFKD normalization."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _char_overlap_score(a: str, b: str) -> float:
    """Bigram Dice coefficient with diacritic-stripped normalization."""
    a = _strip_diacritics(a)
    b = _strip_diacritics(b)
    if len(a) < 2 or len(b) < 2:
        return 0.0
    bigrams_a = set(a[i:i + 2] for i in range(len(a) - 1))
    bigrams_b = set(b[i:i + 2] for i in range(len(b) - 1))
    if not bigrams_a or not bigrams_b:
        return 0.0
    overlap = bigrams_a & bigrams_b
    return 2.0 * len(overlap) / (len(bigrams_a) + len(bigrams_b))


def _humanize_story_name(story_name: str) -> str:
    """Convert filename-style story_name to readable Vietnamese.

    E.g. "SuTichTrauCau" → "sự tích trầu cau"  (best-effort, lowercased)
         "009_SỰ TÍCH CHIM ĐA ĐA" → "sự tích chim đa đa"
    """
    name = story_name.strip()
    # Strip leading digits + underscore/space (e.g. "009_")
    name = re.sub(r"^\d+[_\s]*", "", name)
    # If name has spaces or Vietnamese chars, it's already readable
    if " " in name or any(c in name for c in "àáảãạăắằẳẵặâấầẩẫậ"):
        return name.lower()
    # CamelCase → space-separated
    name = re.sub(r"(?<=[a-zà-ỹ])(?=[A-ZÀ-Ỹ])", " ", name)
    name = re.sub(r"[_-]", " ", name)
    return re.sub(r"\s+", " ", name).strip().lower()


class StoryRegistry:
    """Dynamic story catalog with fuzzy ASR matching.

    Thread-safe. Call `build()` once at startup, then `fuzzy_match()` on
    every incoming query.  Call `rebuild()` after adding/removing stories.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # list of (canonical_name, story_id, [aliases], [tags])
        self._entries: List[Tuple[str, str, List[str], List[str]]] = []
        self._built = False
        self._aliases_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "story_aliases.json"
        )

    @property
    def is_built(self) -> bool:
        return self._built

    @property
    def story_count(self) -> int:
        with self._lock:
            return len(self._entries)

    def get_all_story_names(self) -> List[str]:
        """Return list of canonical story names for greeting suggestions."""
        with self._lock:
            return [canonical for canonical, _, _, _ in self._entries]

    async def build(self, provider) -> int:
        """Populate registry from Qdrant. Returns number of stories found."""
        stories = await provider.list_unique_stories()
        manual_aliases = self._load_manual_aliases()

        entries = []
        for s in stories:
            sid = s["story_id"]
            sname = s["story_name"]
            official_title = s.get("official_title", "")
            tags = s.get("tags", [])

            if official_title:
                canonical = official_title.lower()
            else:
                canonical = _humanize_story_name(sname)

            aliases = generate_aliases(canonical)
            if sid in manual_aliases:
                aliases.extend(manual_aliases[sid])
            aliases = list(set(aliases))
            entries.append((canonical, sid, aliases, tags))

        with self._lock:
            self._entries = entries
            self._built = True

        logger.bind(tag=TAG).info(
            f"StoryRegistry built: {len(entries)} stories, "
            f"total aliases={sum(len(a) for _, _, a, _ in entries)}"
        )
        return len(entries)

    async def rebuild(self, provider) -> int:
        """Re-populate after document add/delete."""
        return await self.build(provider)

    def fuzzy_match(self, extracted_query: str) -> Tuple[Optional[str], Optional[str]]:
        """Match query against all stories using bigram Dice coefficient.

        Returns (canonical_name, story_id) if confident match, else (None, None).
        """
        q = extracted_query.lower().strip()
        q_core = _SU_TICH_PREFIXES.sub("", q).strip()

        best_score = 0.0
        best_match: Tuple[Optional[str], Optional[str]] = (None, None)

        with self._lock:
            for canonical, story_id, aliases, _tags in self._entries:
                for alias in aliases:
                    score = _char_overlap_score(q_core, alias)
                    if score > best_score:
                        best_score = score
                        best_match = (canonical, story_id)
                    score_full = _char_overlap_score(q, alias)
                    if score_full > best_score:
                        best_score = score_full
                        best_match = (canonical, story_id)

        if best_score >= 0.50:
            return best_match
        return (None, None)

    def get_stories_by_tags(
        self,
        include_tags: List[str],
        exclude_tags: Optional[List[str]] = None,
    ) -> List[Tuple[str, str, List[str]]]:
        """Filter stories by tags. Returns list of (canonical, story_id, tags)."""
        exclude = set(t.lower() for t in (exclude_tags or []))
        include_lower = [t.lower() for t in include_tags]
        results = []
        with self._lock:
            for canonical, story_id, _aliases, tags in self._entries:
                tags_lower = [t.lower() for t in tags]
                if exclude and any(t in exclude for t in tags_lower):
                    continue
                if any(t in tags_lower for t in include_lower):
                    results.append((canonical, story_id, tags))
        return results

    def get_story_tags(self, story_id: str) -> List[str]:
        """Return tags for a specific story."""
        with self._lock:
            for _canonical, sid, _aliases, tags in self._entries:
                if sid == story_id:
                    return tags
        return []

    def _load_manual_aliases(self) -> Dict[str, List[str]]:
        """Load optional manual alias overrides from data/story_aliases.json."""
        path = os.path.normpath(self._aliases_path)
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                logger.bind(tag=TAG).info(
                    f"Loaded manual aliases for {len(data)} stories from {path}"
                )
                return data
        except Exception as e:
            logger.bind(tag=TAG).warning(f"Failed to load story_aliases.json: {e}")
        return {}


# Global singleton
story_registry = StoryRegistry()
