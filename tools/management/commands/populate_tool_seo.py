"""
Populate SEO content for all tools.

Generates and stores unique, humanized SEO content for every active tool:
- seo_intro: 200-300 word unique introduction
- use_cases: list of 5+ contextual use cases
- faq_items: list of 7+ FAQ {q,a} dicts

Usage: python manage.py populate_tool_seo [--dry-run] [--batch-size 50]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from tools.models import Tool
from tools.utils.metadata import (
    generate_intro_paragraph,
    generate_use_cases,
    generate_faq_items,
)
import json


class Command(BaseCommand):
    help = 'Populate unique SEO content (intro, use_cases, faqs) for all tools'
    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
        parser.add_argument('--batch-size', type=int, default=50, help='Batch size for updates')
        parser.add_argument('--tool-slug', type=str, help='Target specific tool slug only')
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        tool_slug = options['tool_slug']
        
        queryset = Tool.objects.filter(is_active=True)
        if tool_slug:
            queryset = queryset.filter(slug=tool_slug)
        
        total = queryset.count()
        self.stdout.write(f"Processing {total} tools...")
        
        updated = 0
        errors = 0
        
        for i, tool in enumerate(queryset.iterator(), 1):
            try:
                # Generate if missing
                needs_update = False
                
                if not tool.seo_intro or len(tool.seo_intro) < 150:
                    intro = generate_intro_paragraph(tool.name, tool.short_desc, tool.category.name)
                    if intro and len(intro) >= 200:
                        tool.seo_intro = intro
                        needs_update = True
                
                if not tool.use_cases or len(tool.use_cases) < 3:
                    use_cases = generate_use_cases(tool.name, tool.tags or '')
                    if use_cases and len(use_cases) >= 5:
                        tool.use_cases = use_cases
                        needs_update = True
                
                if not tool.faq_items or len(tool.faq_items) < 5:
                    faq_items = generate_faq_items(tool.name, tool.short_desc, tool.category.name)
                    if faq_items and len(faq_items) >= 7:
                        tool.faq_items = faq_items
                        needs_update = True
                
                if needs_update and not dry_run:
                    tool.save(update_fields=['seo_intro', 'use_cases', 'faq_items'])
                    updated += 1
                    if updated % batch_size == 0:
                        self.stdout.write(f"  ✓ {updated}/{total} tools updated")
                elif needs_update and dry_run:
                    updated += 1
                    self.stdout.write(f"  [DRY RUN] Would update: {tool.slug}")
                    
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Error for {tool.slug}: {e}"))
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry run complete. Would update {updated} tools."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Complete. Updated {updated} tools. Errors: {errors}"))
