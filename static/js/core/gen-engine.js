/**
 * LamGen Dynamic Generation Engine v2.0
 * Centralized engine for all generator-style tools.
 * Provides: weighted randomness, synonym rotation, phrase mutation,
 * archetype styles, duplicate prevention, platform adaptation.
 */

const GenEngine = (() => {

  // ── Core RNG ──────────────────────────────────────────────────────────────
  // Uses crypto.getRandomValues for true unpredictability on every call
  function rand(min, max) {
    const arr = new Uint32Array(1);
    crypto.getRandomValues(arr);
    return min + (arr[0] % (max - min + 1));
  }

  function pick(arr) {
    if (!arr || !arr.length) return '';
    return arr[rand(0, arr.length - 1)];
  }

  // Weighted pick: weights array must match items array length
  function pickWeighted(items, weights) {
    const total = weights.reduce((a, b) => a + b, 0);
    const arr = new Uint32Array(1);
    crypto.getRandomValues(arr);
    let r = (arr[0] / 0xFFFFFFFF) * total;
    for (let i = 0; i < items.length; i++) {
      r -= weights[i];
      if (r <= 0) return items[i];
    }
    return items[items.length - 1];
  }

  // Shuffle array in-place (Fisher-Yates with crypto RNG)
  function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = rand(0, i);
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  // Pick N unique items from array
  function pickN(arr, n) {
    return shuffle(arr).slice(0, Math.min(n, arr.length));
  }

  // ── Synonym Engine ────────────────────────────────────────────────────────
  const SYNONYMS = {
    // Action verbs
    'help':      ['help', 'empower', 'enable', 'support', 'guide', 'assist', 'fuel'],
    'build':     ['build', 'craft', 'create', 'develop', 'engineer', 'architect', 'shape'],
    'grow':      ['grow', 'scale', 'expand', 'accelerate', 'amplify', 'elevate', 'boost'],
    'drive':     ['drive', 'lead', 'power', 'propel', 'champion', 'spearhead', 'steer'],
    'transform': ['transform', 'reshape', 'reinvent', 'revolutionize', 'redefine', 'evolve'],
    'deliver':   ['deliver', 'execute', 'produce', 'achieve', 'generate', 'unlock'],
    'connect':   ['connect', 'bridge', 'unite', 'link', 'align', 'integrate'],
    'improve':   ['improve', 'optimize', 'enhance', 'refine', 'elevate', 'sharpen'],
    'create':    ['create', 'design', 'produce', 'build', 'craft', 'develop', 'launch'],
    'share':     ['share', 'spread', 'amplify', 'broadcast', 'publish', 'distribute'],
    // Adjectives
    'passionate': ['passionate', 'driven', 'dedicated', 'committed', 'obsessed', 'focused'],
    'experienced': ['experienced', 'seasoned', 'skilled', 'expert', 'accomplished', 'proven'],
    'innovative': ['innovative', 'creative', 'forward-thinking', 'visionary', 'pioneering'],
    'strategic':  ['strategic', 'data-driven', 'results-oriented', 'impact-focused', 'intentional'],
    'dynamic':    ['dynamic', 'versatile', 'adaptable', 'agile', 'resourceful', 'multifaceted'],
    // Nouns
    'results':   ['results', 'outcomes', 'impact', 'value', 'growth', 'success'],
    'solutions': ['solutions', 'strategies', 'systems', 'frameworks', 'approaches'],
    'team':      ['team', 'organization', 'company', 'business', 'brand', 'startup'],
    'audience':  ['audience', 'community', 'followers', 'readers', 'customers', 'users'],
    'content':   ['content', 'stories', 'ideas', 'insights', 'narratives', 'work'],
  };

  function synonym(word) {
    const key = word.toLowerCase();
    const list = SYNONYMS[key];
    if (!list) return word;
    return pick(list);
  }

  // Replace all [word] placeholders in a template string with synonyms
  function mutate(template, ctx = {}) {
    return template
      .replace(/\[(\w+)\]/g, (_, key) => {
        if (ctx[key] !== undefined) return ctx[key];
        return synonym(key) || key;
      })
      .replace(/\{([^}]+)\}/g, (_, options) => pick(options.split('|')));
  }

  // ── Phrase Mutation ───────────────────────────────────────────────────────
  // Randomly vary sentence structure
  function varyLength(text, style) {
    // style: 'short' | 'medium' | 'long'
    const sentences = text.split(/(?<=[.!?])\s+/);
    if (style === 'short' && sentences.length > 2) return sentences.slice(0, 2).join(' ');
    if (style === 'long' && sentences.length < 3) return text + ' ' + text.split(' ').slice(0, 5).join(' ') + '.';
    return text;
  }

  // ── Platform Archetypes ───────────────────────────────────────────────────
  const ARCHETYPES = {
    linkedin: {
      tone: 'professional',
      emojiDensity: 0.2,      // 0-1 probability of emoji per sentence
      sentenceLength: 'medium',
      openers: [
        '{Excited|Thrilled|Proud|Honored} to share',
        'After {years|months} of {work|building|learning}',
        'Here\'s what I\'ve learned about',
        'The truth about {[results]|success|growth} that nobody talks about',
        'I used to think {X|this|that}. I was wrong.',
        'Hot take:',
        '{3|5|7} things I wish I knew earlier about',
        'We just {hit|reached|achieved|crossed}',
      ],
      closers: [
        'What\'s your experience with this?',
        'Drop your thoughts below 👇',
        'Tag someone who needs to see this.',
        'Save this for later.',
        'Follow for more insights like this.',
        'What would you add?',
      ],
      emojis: ['🚀', '💡', '🎯', '📈', '✅', '🔥', '💪', '🌟', '👇', '🤝'],
    },
    instagram: {
      tone: 'aesthetic',
      emojiDensity: 0.6,
      sentenceLength: 'short',
      openers: [
        'not all who {wander|dream|create} are lost ✨',
        'reminder:',
        'this is your sign to',
        'living for {moments|vibes|days} like this',
        'the {aesthetic|vibe|energy} is {immaculate|unmatched|everything}',
        'soft life era 🌸',
        'main character energy 💫',
        'plot twist:',
      ],
      closers: [
        '💛 save this',
        'tag your person 🤍',
        'double tap if you agree ✨',
        'link in bio 🔗',
        'which one are you? 👇',
        'share with someone who needs this 🌸',
      ],
      emojis: ['✨', '🌸', '💫', '🤍', '🌙', '🦋', '🌿', '💛', '🫶', '🌊'],
    },
    tiktok: {
      tone: 'trendy',
      emojiDensity: 0.5,
      sentenceLength: 'short',
      openers: [
        'POV:',
        'tell me why',
        'no because',
        'the way that',
        'not me',
        'okay but',
        'wait—',
        'this is your sign',
        'hot take but',
        'unpopular opinion:',
      ],
      closers: [
        'follow for more 🫶',
        'stitch this',
        'comment your thoughts 👇',
        'duet if you agree',
        'save this for later ✨',
        'which side are you on?',
      ],
      emojis: ['💀', '😭', '✨', '🫶', '🔥', '💅', '👀', '🤣', '😩', '🙏'],
    },
    twitter: {
      tone: 'punchy',
      emojiDensity: 0.15,
      sentenceLength: 'short',
      openers: [
        'unpopular opinion:',
        'hot take:',
        'thread 🧵',
        'nobody talks about this but',
        'the real reason',
        'controversial but',
        'this is important:',
        'reminder:',
        'fact:',
      ],
      closers: [
        'RT if you agree.',
        'Thoughts?',
        'Change my mind.',
        'Am I wrong?',
        'Discuss.',
        'Save this.',
      ],
      emojis: ['🧵', '👇', '🔥', '💯', '🤔', '👀', '✅', '❌', '🚨', '💡'],
    },
    academic: {
      tone: 'formal',
      emojiDensity: 0,
      sentenceLength: 'long',
      openers: [
        'This paper examines',
        'The present study investigates',
        'Drawing on',
        'Building upon existing literature,',
        'This research explores',
        'A critical analysis of',
        'The intersection of',
        'Emerging evidence suggests',
      ],
      closers: [
        'Further research is warranted.',
        'These findings have significant implications for the field.',
        'This study contributes to the growing body of literature on',
        'The results underscore the importance of',
      ],
      emojis: [],
    },
    viral: {
      tone: 'curiosity',
      emojiDensity: 0.4,
      sentenceLength: 'medium',
      openers: [
        'Nobody is talking about this.',
        'This changed everything for me.',
        'I can\'t believe this works.',
        'The secret they don\'t want you to know:',
        'I tested this so you don\'t have to.',
        'This one thing made all the difference.',
        'Stop doing this immediately.',
        'The {#1|biggest|most overlooked} mistake people make with',
      ],
      closers: [
        'Share this before it gets taken down.',
        'Save this. You\'ll thank me later.',
        'Tell me if this worked for you 👇',
        'Who else needed to hear this?',
        'Bookmark this now.',
      ],
      emojis: ['🚨', '🔥', '💡', '👀', '⚡', '🎯', '💥', '🤯', '✅', '👇'],
    },
  };

  function getArchetype(platform) {
    return ARCHETYPES[platform] || ARCHETYPES.linkedin;
  }

  // ── Emoji Logic ───────────────────────────────────────────────────────────
  function maybeEmoji(platform) {
    const arch = getArchetype(platform);
    if (!arch.emojis.length) return '';
    const arr = new Uint32Array(1);
    crypto.getRandomValues(arr);
    if ((arr[0] / 0xFFFFFFFF) < arch.emojiDensity) {
      return ' ' + pick(arch.emojis);
    }
    return '';
  }

  // ── Duplicate Prevention ──────────────────────────────────────────────────
  // Tracks generated outputs per session to avoid repeats
  const _memory = new Map();

  function rememberBatch(key, items) {
    if (!_memory.has(key)) _memory.set(key, new Set());
    const mem = _memory.get(key);
    items.forEach(i => mem.add(i.trim().toLowerCase().slice(0, 40)));
    // Keep memory bounded
    if (mem.size > 200) {
      const arr = [...mem];
      _memory.set(key, new Set(arr.slice(-100)));
    }
  }

  function isDuplicate(key, item) {
    const mem = _memory.get(key);
    if (!mem) return false;
    return mem.has(item.trim().toLowerCase().slice(0, 40));
  }

  function dedup(key, items) {
    const unique = items.filter(i => !isDuplicate(key, i));
    rememberBatch(key, unique.length ? unique : items);
    return unique.length >= Math.min(3, items.length) ? unique : items;
  }

  // ── Sentence Variation ────────────────────────────────────────────────────
  // Vary capitalization style
  function applyCase(text, style) {
    switch (style) {
      case 'lower': return text.toLowerCase();
      case 'upper': return text.toUpperCase();
      case 'title': return text.replace(/\b\w/g, c => c.toUpperCase());
      case 'sentence': return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
      default: return text;
    }
  }

  // Add random punctuation variation
  function varyPunctuation(text) {
    const r = rand(0, 9);
    if (r < 2 && !text.endsWith('?') && !text.endsWith('!')) {
      return text.replace(/\.$/, '!');
    }
    if (r === 2) return text.replace(/\.$/, '...');
    return text;
  }

  // ── Core Generation API ───────────────────────────────────────────────────

  /**
   * Generate N unique outputs from a pool of template functions.
   * @param {string} key - Unique key for duplicate memory
   * @param {Function[]} generators - Array of functions that return a string
   * @param {number} count - How many to generate
   * @param {Object} ctx - Context variables
   * @returns {string[]}
   */
  function generate(key, generators, count, ctx = {}) {
    const shuffled = shuffle(generators);
    const results = [];
    const seen = new Set();

    for (const gen of shuffled) {
      if (results.length >= count) break;
      try {
        let output = gen(ctx);
        if (!output || typeof output !== 'string') continue;
        output = output.trim();
        const norm = output.toLowerCase().slice(0, 50);
        if (seen.has(norm) || isDuplicate(key, output)) continue;
        seen.add(norm);
        results.push(output);
      } catch (e) {
        // Skip failed generators silently
      }
    }

    // If we didn't get enough, run generators again with mutation
    let attempts = 0;
    while (results.length < count && attempts < count * 3) {
      attempts++;
      const gen = pick(shuffled);
      try {
        let output = gen(ctx);
        if (!output) continue;
        output = varyPunctuation(output.trim());
        const norm = output.toLowerCase().slice(0, 50);
        if (seen.has(norm)) continue;
        seen.add(norm);
        results.push(output);
      } catch (e) {}
    }

    rememberBatch(key, results);
    return results.slice(0, count);
  }

  /**
   * Build a sentence from parts with random connectors.
   */
  function compose(...parts) {
    return parts.filter(Boolean).join(' ').replace(/\s{2,}/g, ' ').trim();
  }

  /**
   * Pick a random opener for a platform.
   */
  function opener(platform) {
    const arch = getArchetype(platform);
    return mutate(pick(arch.openers));
  }

  /**
   * Pick a random closer/CTA for a platform.
   */
  function closer(platform) {
    const arch = getArchetype(platform);
    return pick(arch.closers);
  }

  // ── Vocabulary Banks ──────────────────────────────────────────────────────
  const VOCAB = {
    powerVerbs: ['accelerate','achieve','amplify','architect','build','champion','craft',
      'cultivate','deliver','design','develop','drive','elevate','empower','engineer',
      'execute','expand','forge','fuel','generate','grow','guide','harness','ignite',
      'implement','innovate','inspire','launch','lead','leverage','maximize','optimize',
      'pioneer','produce','propel','reshape','scale','shape','spearhead','streamline',
      'transform','unlock','validate'],
    powerAdj: ['actionable','agile','bold','breakthrough','compelling','comprehensive',
      'cutting-edge','data-driven','dynamic','effective','efficient','elite','exceptional',
      'forward-thinking','high-impact','impactful','innovative','intentional','measurable',
      'next-level','outcome-focused','proven','results-driven','scalable','strategic',
      'transformative','visionary'],
    emotions: ['excited','inspired','grateful','proud','motivated','energized','focused',
      'determined','passionate','curious','optimistic','confident','humbled','thrilled'],
    transitions: ['Additionally,','Moreover,','Furthermore,','Beyond that,','What\'s more,',
      'On top of that,','Equally important,','At the same time,','In parallel,'],
    numbers: ['3','5','7','10','12','15','20','25','30','50','100'],
  };

  function powerVerb() { return pick(VOCAB.powerVerbs); }
  function powerAdj()  { return pick(VOCAB.powerAdj); }
  function emotion()   { return pick(VOCAB.emotions); }
  function transition(){ return pick(VOCAB.transitions); }
  function number()    { return pick(VOCAB.numbers); }

  // ── Public API ────────────────────────────────────────────────────────────
  return {
    rand, pick, pickWeighted, pickN, shuffle,
    synonym, mutate,
    getArchetype, maybeEmoji,
    opener, closer,
    generate, compose,
    dedup, rememberBatch, isDuplicate,
    varyPunctuation, applyCase, varyLength,
    powerVerb, powerAdj, emotion, transition, number,
    VOCAB, ARCHETYPES, SYNONYMS,
  };

})();

// Make available globally
window.GenEngine = GenEngine;
