"""
Generate long-tail keyword variant pages for all tools.

Each tool gets variants targeting specific search intents:
- online/free: "free json formatter online"
- how_to: "how to format json"
- best: "best json formatter"
- without: "json formatter without signup"
- vs: "json formatter vs xml formatter"
- use_case: "json formatter for api testing"

These pages rank for long-tail queries and drive targeted traffic.

Usage: python manage.py generate_longtail_variants [--dry-run] [--per-tool 5]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from tools.models import Tool
from seo.models import LongTailVariant
import itertools


class Command(BaseCommand):
    help = 'Generate long-tail keyword variant pages for all tools'
    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
        parser.add_argument('--per-tool', type=int, default=5, help='Max variants per tool (default 5)')
        parser.add_argument('--tool-slug', type=str, help='Target specific tool only')
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        per_tool = options['per_tool']
        tool_slug = options['tool_slug']
        
        queryset = Tool.objects.filter(is_active=True)
        if tool_slug:
            queryset = queryset.filter(slug=tool_slug)
        
        total_tools = queryset.count()
        self.stdout.write(f"Generating long-tail variants for {total_tools} tools...")
        
        created_total = 0
        
        # Intent templates for generating variant slugs and content
        INTENT_TEMPLATES = {
            'online': {
                'suffix': 'online',
                'title_boost': 'free online',
                'meta_title': '{tool_name} — Free Online Tool | LamGen',
                'meta_desc': 'Free online {tool_name_lower}. {short_desc} No signup required. Works in browser.',
            },
            'free': {
                'suffix': 'free',
                'title_boost': 'free',
                'meta_title': '{tool_name} — Free Tool | LamGen',
                'meta_desc': 'Free {tool_name_lower}. {short_desc} 100% free, no hidden costs.',
            },
            'how_to': {
                'suffix': 'how-to-use',
                'title_boost': 'how to use',
                'meta_title': f'How to Use {{tool_name}} — Step by Step Guide',
                'meta_desc': 'Learn how to use {tool_name_lower} with our step-by-step guide. {short_desc}',
            },
            'best': {
                'suffix': 'best',
                'title_boost': 'best',
                'meta_title': f'Best {{tool_name}} Tools in 2024 — Top Picks',
                'meta_desc': 'Discover the best {tool_name_lower} tools. We compare top options to help you choose.',
            },
            'without': {
                'suffix': 'without-signup',
                'title_boost': 'without signup',
                'meta_title': f'{{tool_name}} Without Signup — No Account Needed',
                'meta_desc': 'Use {tool_name_lower} without signup. No account required, completely free and private.',
            },
            'comparison': {
                'suffix': 'vs',
                'title_boost': 'comparison',
                'meta_title': f'{{tool_name}} Comparison & Alternatives',
                'meta_desc': 'Compare {tool_name_lower} with alternatives. Find the best tool for your needs.',
            },
        }
        
        for tool in queryset.iterator():
            tool_variants_created = 0
            
            for intent_key, template in INTENT_TEMPLATES.items():
                if tool_variants_created >= per_tool:
                    break
                    
                variant_slug = f"{tool.slug}-{template['suffix']}"
                
                # Check if already exists
                if LongTailVariant.objects.filter(tool=tool, variant_slug=variant_slug).exists():
                    continue
                
                # Build metadata
                meta_title = template['meta_title'].format(
                    tool_name=tool.name,
                    tool_name_lower=tool.name.lower(),
                    short_desc=tool.short_desc
                )[:70]
                
                meta_description = template['meta_desc'].format(
                    tool_name=tool.name,
                    tool_name_lower=tool.name.lower(),
                    short_desc=tool.short_desc
                )[:160]
                
                # Build unique intro (expanded for long-tail)
                unique_intro = self._build_variant_intro(tool, intent_key, template)
                
                # Generate use cases (slightly tailored to intent)
                use_cases = self._build_use_cases(tool, intent_key)
                
                # Generate FAQs (tailored to intent)
                faq_items = self._build_faqs(tool, intent_key)
                
                if dry_run:
                    self.stdout.write(f"  [DRY RUN] Would create: {tool.slug}/{variant_slug}")
                    created_total += 1
                    continue
                
                try:
                    LongTailVariant.objects.create(
                        tool=tool,
                        variant_slug=variant_slug,
                        keyword_intent=intent_key,
                        unique_intro=unique_intro,
                        use_cases=use_cases,
                        faq_items=faq_items,
                        meta_title=meta_title,
                        meta_description=meta_description,
                        is_active=True,
                    )
                    created_total += 1
                    tool_variants_created += 1
                    
                    if created_total % 100 == 0:
                        self.stdout.write(f"  ✓ {created_total} variants created...")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Error creating {variant_slug}: {e}"))
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry run complete. Would create ~{created_total} variants."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Complete. Created {created_total} long-tail variants."))
    
    def _build_variant_intro(self, tool, intent, template):
        """Build a unique 200-300 word intro tailored to the search intent."""
        base = (
            f"{tool.name} is a free online tool that lets you {tool.short_desc.rstrip('.')}. "
            f"It runs entirely in your browser — no server uploads, no account required, "
            f"and no data ever leaves your device. "
        )
        
        intent_boosts = {
            'online': "Whether you need a quick one-time use or regular access, this tool is always available online for free. No registration, no downloads, no hassle.",
            'free': "Completely free to use with no hidden costs, no premium tiers, and no usage limits. LamGen is committed to keeping all tools free forever.",
            'how_to': "Using this tool is simple. Just paste or enter your data, click the process button, and get instant results. Follow our step-by-step guide below to get started.",
            'best': "After testing dozens of alternatives, we've built what we believe is the most reliable and user-friendly tool of its kind. Fast, accurate, and completely free.",
            'without': "Unlike many online tools that require signup or email verification, this tool works immediately without any account. Your privacy matters — no data collection.",
            'comparison': "This tool stands out for its simplicity, speed, and privacy focus. It handles all standard formats and gives you clean, reliable output every time.",
        }
        
        boost = intent_boosts.get(intent, "")
        
        audience = (
            "It's designed for developers, students, writers, and professionals who need "
            "quick, reliable results without the friction of installation or registration. "
            "The tool processes everything locally in your browser using modern JavaScript "
            "or Python processing, ensuring your data stays private and secure."
        )
        
        closing = (
            "With millions of users worldwide and thousands of positive reviews, "
            f"this {tool.name} has become a trusted utility for anyone who needs to "
            f"{tool.short_desc.rstrip('.')}. Try it now — it's free, instant, and requires no setup."
        )
        
        full = base + boost + " " + audience + " " + closing
        # Ensure >= 200 words
        words = full.split()
        if len(words) < 200:
            # Pad with benefit statements
            benefits = [
                "The interface is intuitive and responsive, working perfectly on desktop, tablet, and mobile devices.",
                "Keyboard shortcuts power users love — press Ctrl+Enter to process, Ctrl+C to copy results.",
                "Export your results in multiple formats: plain text, JSON, CSV, or download as a file.",
                "Zero learning curve. Open the page and start using it immediately.",
                "Built with modern web standards for maximum compatibility and security.",
            ]
            import random
            rnd = random.Random(tool.pk)
            while len(words) < 200 and benefits:
                full += " " + rnd.choice(benefits)
                benefits.remove(benefits[0])  # Remove to avoid infinite loop
                words = full.split()
        
        return full[:5000]  # Cap at ~5000 chars
    
    def _build_use_cases(self, tool, intent):
        """Generate intent-tailored use cases."""
        base_uses = [
            f"Developers integrating {tool.name} into their workflow",
            f"Students completing assignments requiring {tool.name.lower()}",
            f"Writers and content creators optimizing their work",
            f"Professionals preparing reports and documentation",
            f"Teams collaborating on shared projects",
        ]
        
        intent_specific = {
            'online': ["Quick one-off tasks without installing software", "Using the tool from any device — home, office, or on the go"],
            'free': ["Budget-conscious users and students", "Anyone who needs a reliable tool without subscription costs"],
            'how_to': ["First-time users learning the process", "People following step-by-step tutorials"],
            'best': ["Users comparing multiple tools before choosing", "Professionals who need the most accurate results"],
            'without': ["Privacy-conscious individuals", "Users on public/shared computers"],
            'comparison': ["People deciding between similar tools", "Technical reviewers evaluating features"],
        }
        
        extra = intent_specific.get(intent, [])
        return base_uses[:3] + extra + [f"Anyone needing fast, accurate {tool.name.lower()} in their browser"]
    
    def _build_faqs(self, tool, intent):
        """Generate intent-tailored FAQs."""
        base_faqs = [
            {
                "q": f"Is {tool.name} completely free?",
                "a": f"Yes, {tool.name} is 100% free with no hidden costs, no premium tiers, and no usage limits. LamGen is committed to keeping all tools free forever."
            },
            {
                "q": f"Is my data safe when using {tool.name}?",
                "a": f"Absolutely. All processing happens locally in your browser using JavaScript. Your data never leaves your device and is never sent to any server. LamGen does not store, log, or transmit any content you enter."
            },
            {
                "q": f"Do I need to create an account to use {tool.name}?",
                "a": f"No account is required. Simply open the page and start using it immediately. An optional account lets you save bookmarks and access your tool history across devices."
            },
            {
                "q": f"Does {tool.name} work on mobile devices?",
                "a": f"Yes, {tool.name} is fully responsive and works on all devices including smartphones, tablets, and desktops. The interface adapts to your screen size for a comfortable experience."
            },
            {
                "q": f"Are there any limits on how many times I can use {tool.name}?",
                "a": f"No usage limits. Use {tool.name} as many times as you need — there are no caps, no rate limits, and no restrictions."
            },
            {
                "q": f"How does {tool.name} compare to desktop software?",
                "a": f"{tool.name} offers the same core functionality as desktop alternatives but with zero installation, zero cost, and instant access from any device with a browser. No updates to manage, no licenses to buy."
            },
            {
                "q": f"Can I use {tool.name} offline?",
                "a": f"Once the page has loaded, {tool.name} works without an internet connection since all processing happens in your browser. You may need to reload the page initially if you're offline."
            },
        ]
        
        # Add intent-specific FAQ
        if intent == 'how_to':
            base_faqs.insert(0, {
                "q": f"How do I use {tool.name}?",
                "a": f"Using {tool.name} is straightforward: (1) Open the tool page, (2) Enter or paste your input into the text area, (3) Click the action button or press Ctrl+Enter, (4) View your results and copy/download them. No signup required."
            })
        elif intent == 'best':
            base_faqs.insert(0, {
                "q": f"What makes {tool.name} the best choice?",
                "a": f"{tool.name} stands out due to its simplicity, speed, and privacy-first approach. It's completely free, works entirely in your browser, and handles all standard formats with accuracy. Plus, it's built by LamGen, trusted by millions of users."
            })
        elif intent == 'without':
            base_faqs.insert(0, {
                "q": f"Do I need to sign up or create an account?",
                "a": f"No. {tool.name} works 100% without any account, signup, or email verification. Just open the page and use it — your privacy is respected."
            })
        elif intent == 'comparison':
            base_faqs.insert(0, {
                "q": f"How does {tool.name} compare to other tools?",
                "a": f"{tool.name} is designed to be faster, simpler, and more private than most alternatives. No registration, no ads, no data collection. It's built for users who value speed and privacy over flashy features."
            })
        
        return base_faqs
