"""Curated word lists for deterministic SEO content generation."""

WORD_LISTS: dict[str, dict[str, list[str]]] = {
    'captions': {
        'adjectives': [
            'breathtaking', 'golden', 'serene', 'vibrant', 'timeless', 'radiant',
            'electric', 'dreamy', 'bold', 'effortless', 'iconic', 'wild', 'pure',
            'luminous', 'fierce', 'tranquil', 'magnetic', 'vivid', 'endless', 'raw',
        ],
        'nouns': [
            'adventure', 'memory', 'journey', 'moment', 'story', 'dream', 'soul',
            'horizon', 'chapter', 'vibe', 'energy', 'spirit', 'path', 'light',
            'wave', 'spark', 'echo', 'pulse', 'glow', 'vision',
        ],
        'verbs': [
            'explore', 'discover', 'embrace', 'chase', 'capture', 'create',
            'wander', 'inspire', 'celebrate', 'live', 'feel', 'shine', 'rise',
            'build', 'share', 'grow', 'dream', 'seek', 'find', 'own',
        ],
        'emotions': [
            'joy', 'wonder', 'gratitude', 'excitement', 'peace', 'bliss',
            'pride', 'love', 'hope', 'freedom', 'courage', 'passion',
            'serenity', 'awe', 'delight', 'warmth', 'clarity', 'strength',
        ],
    },
    'quotes': {
        'adjectives': [
            'powerful', 'inspiring', 'profound', 'timeless', 'wise', 'uplifting',
            'motivating', 'deep', 'meaningful', 'transformative', 'honest', 'bold',
        ],
        'nouns': [
            'success', 'failure', 'growth', 'change', 'courage', 'wisdom',
            'purpose', 'resilience', 'mindset', 'action', 'vision', 'truth',
        ],
        'verbs': [
            'achieve', 'overcome', 'persist', 'believe', 'strive', 'lead',
            'inspire', 'transform', 'create', 'build', 'rise', 'succeed',
        ],
        'emotions': [
            'determination', 'hope', 'confidence', 'strength', 'clarity',
            'focus', 'ambition', 'gratitude', 'resilience', 'courage',
        ],
    },
    'interview-questions': {
        'adjectives': [
            'common', 'tricky', 'advanced', 'fundamental', 'practical',
            'real-world', 'technical', 'behavioral', 'situational', 'critical',
        ],
        'nouns': [
            'algorithm', 'data structure', 'design pattern', 'architecture',
            'performance', 'scalability', 'security', 'testing', 'debugging',
            'optimization', 'concurrency', 'API', 'database', 'framework',
        ],
        'verbs': [
            'implement', 'design', 'optimize', 'debug', 'refactor',
            'explain', 'compare', 'analyze', 'build', 'test',
        ],
        'emotions': ['confidence', 'clarity', 'precision', 'depth', 'insight'],
    },
    'bios': {
        'adjectives': [
            'passionate', 'creative', 'driven', 'innovative', 'dedicated',
            'experienced', 'skilled', 'enthusiastic', 'results-oriented', 'dynamic',
        ],
        'nouns': [
            'developer', 'designer', 'entrepreneur', 'creator', 'leader',
            'professional', 'expert', 'specialist', 'consultant', 'strategist',
        ],
        'verbs': [
            'build', 'create', 'design', 'lead', 'develop', 'innovate',
            'transform', 'deliver', 'drive', 'inspire',
        ],
        'emotions': ['passion', 'dedication', 'enthusiasm', 'commitment', 'purpose'],
    },
    'usernames': {
        'adjectives': [
            'dark', 'neon', 'cyber', 'shadow', 'ghost', 'pixel', 'ultra',
            'hyper', 'turbo', 'mega', 'alpha', 'omega', 'void', 'nova',
        ],
        'nouns': [
            'wolf', 'fox', 'hawk', 'blade', 'storm', 'fire', 'ice',
            'byte', 'code', 'node', 'flux', 'core', 'edge', 'wave',
        ],
        'verbs': ['run', 'fly', 'strike', 'hunt', 'code', 'hack', 'build'],
        'emotions': ['fierce', 'bold', 'sharp', 'swift', 'silent'],
    },
    'hashtags': {
        'adjectives': [
            'trending', 'viral', 'popular', 'top', 'best', 'daily',
            'weekly', 'monthly', 'ultimate', 'essential',
        ],
        'nouns': [
            'content', 'creator', 'lifestyle', 'motivation', 'inspiration',
            'business', 'marketing', 'growth', 'success', 'community',
        ],
        'verbs': ['grow', 'create', 'share', 'inspire', 'connect', 'build'],
        'emotions': ['passion', 'energy', 'focus', 'drive', 'hustle'],
    },
    'thesis-topics': {
        'adjectives': [
            'emerging', 'critical', 'comparative', 'systematic', 'empirical',
            'theoretical', 'applied', 'interdisciplinary', 'longitudinal', 'qualitative',
        ],
        'nouns': [
            'impact', 'analysis', 'framework', 'model', 'approach',
            'strategy', 'system', 'perspective', 'evaluation', 'assessment',
        ],
        'verbs': [
            'analyze', 'evaluate', 'examine', 'investigate', 'explore',
            'assess', 'compare', 'develop', 'propose', 'review',
        ],
        'emotions': ['rigor', 'depth', 'clarity', 'precision', 'insight'],
    },
    'project-ideas': {
        'adjectives': [
            'innovative', 'practical', 'scalable', 'open-source', 'full-stack',
            'real-time', 'AI-powered', 'mobile-first', 'cloud-native', 'beginner-friendly',
        ],
        'nouns': [
            'app', 'platform', 'tool', 'system', 'dashboard', 'API',
            'bot', 'extension', 'library', 'framework',
        ],
        'verbs': [
            'build', 'create', 'develop', 'design', 'implement',
            'automate', 'integrate', 'deploy', 'optimize', 'launch',
        ],
        'emotions': ['creativity', 'ambition', 'curiosity', 'innovation', 'impact'],
    },
    'default': {
        'adjectives': ['amazing', 'useful', 'powerful', 'simple', 'effective'],
        'nouns': ['tool', 'resource', 'guide', 'example', 'template'],
        'verbs': ['use', 'create', 'build', 'explore', 'discover'],
        'emotions': ['value', 'quality', 'clarity', 'ease', 'speed'],
    },
}
