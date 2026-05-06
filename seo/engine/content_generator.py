"""
Deterministic programmatic SEO content generator.
Uses hashlib.md5(slug) as seed — identical output for the same slug, always.
No LLM calls, no external APIs.
"""
import hashlib
import random
from .word_lists import WORD_LISTS
from .templates import CONTENT_TEMPLATES


def generate_items(
    category_slug: str,
    topic: str,
    slug: str,
    count: int = 30,
) -> list[str]:
    """
    Generate a deterministic list of content items for a given topic slug.

    Args:
        category_slug: SEOCategory slug (e.g. 'captions', 'quotes')
        topic: Human-readable topic name (e.g. 'Travel Instagram Captions')
        slug: Unique page slug used as the random seed
        count: Number of items to generate (minimum 20 will always be returned)

    Returns:
        List of unique string items, length >= 20.
    """
    # Deterministic seed from slug — isolated RNG, no global state pollution
    seed = int(hashlib.md5(slug.encode('utf-8')).hexdigest(), 16) % (2 ** 32)
    rng = random.Random(seed)

    templates = CONTENT_TEMPLATES.get(category_slug, CONTENT_TEMPLATES['default'])
    words = WORD_LISTS.get(category_slug, WORD_LISTS['default'])

    def _pick(key: str) -> str:
        lst = words.get(key, [key])
        return rng.choice(lst) if lst else key

    def _render(template: str) -> str:
        try:
            return template.format(
                topic=topic,
                adj=_pick('adjectives'),
                noun=_pick('nouns'),
                verb=_pick('verbs'),
                emotion=_pick('emotions'),
                number=rng.randint(1, 100),
            )
        except (KeyError, IndexError):
            return template

    # Generate initial batch
    raw_items = [_render(rng.choice(templates)) for _ in range(count * 2)]

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for item in raw_items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
        if len(unique) >= count:
            break

    # Guarantee minimum 20 items
    extra_seed = seed
    while len(unique) < 20:
        extra_seed = (extra_seed + 1) % (2 ** 32)
        rng2 = random.Random(extra_seed)
        item = _render(rng2.choice(templates))
        if item not in seen:
            seen.add(item)
            unique.append(item)

    return unique[:count]
