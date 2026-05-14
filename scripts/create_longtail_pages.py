#!/usr/bin/env python3
"""
Create long-tail SEO pages for high-value keywords.
This script creates 5 targeted long-tail pages as requested.
"""
import os
import sys
from pathlib import Path

import django

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.seo.models import LongTailVariant
from apps.tools.models import Tool

def create_longtail_pages():
    """Create 5 high-value long-tail SEO pages."""
    
    # Get tools for long-tail pages
    try:
        image_compressor = Tool.objects.get(slug='image-compressor')
        word_to_pdf = Tool.objects.get(slug='word-to-pdf')
        resume_summary = Tool.objects.get(slug='resume-summary-generator')
        meta_generator = Tool.objects.get(slug='meta-title-generator')
        fake_chat = Tool.objects.get(slug='fake-chat-generator')
    except Tool.DoesNotExist as e:
        print(f"Tool not found: {e}")
        return

    # 1. compress-png-to-50kb
    variant1 = LongTailVariant.objects.create(
        tool=image_compressor,
        variant_slug='compress-png-to-50kb',
        meta_title='Compress PNG to 50KB - Free Online PNG Compressor | LamGen',
        meta_description='Compress PNG images to exactly 50KB file size. Free online PNG compressor that maintains quality while reducing file size. Perfect for web optimization.',
        unique_intro='Compress PNG to 50KB is a specialized image optimization tool designed to reduce PNG file sizes to exactly 50 kilobytes while maintaining acceptable visual quality. This tool is perfect for web developers, content creators, and digital marketers who need to meet specific file size requirements for website optimization, email attachments, or platform upload limits.',
        use_cases=[
            'Web developers optimizing PNG images for faster website loading times',
            'Email marketers reducing image sizes to avoid spam filters',
            'Social media managers compressing PNGs for platform requirements',
            'E-commerce store owners optimizing product images for better conversion',
            'Bloggers preparing images for faster page load speeds',
            'Designers creating web-optimized graphics for client delivery'
        ],
        faq_items=[
            {
                'q': 'Why compress PNG to exactly 50KB?',
                'a': '50KB is an optimal file size for web images, balancing quality and loading speed. Many websites and email platforms have specific size limits, and 50KB ensures fast loading while maintaining good visual quality.'
            },
            {
                'q': 'Will my PNG images lose quality at 50KB?',
                'a': 'Our smart compression algorithm maintains visual quality while reducing file size. For most PNGs, the quality difference is minimal and acceptable for web use.'
            },
            {
                'q': 'Can I compress multiple PNGs to 50KB at once?',
                'a': 'Yes, you can upload multiple PNG files and our tool will compress each one to approximately 50KB while maintaining the best possible quality for each image.'
            }
        ],
        is_active=True
    )

    # 2. word-to-pdf-without-upload
    variant2 = LongTailVariant.objects.create(
        tool=word_to_pdf,
        variant_slug='word-to-pdf-without-upload',
        meta_title='Word to PDF Without Upload - Free Offline Converter | LamGen',
        meta_description='Convert Word documents to PDF without uploading files. Free offline converter that works entirely in your browser. 100% private and secure.',
        unique_intro='Word to PDF Without Upload is a secure document conversion tool that transforms Word files into PDF format directly in your browser. Unlike online converters that require file uploads, our tool processes everything locally on your device, ensuring your sensitive documents never leave your computer. Perfect for confidential business documents, legal papers, and personal files.',
        use_cases=[
            'Business professionals converting confidential contracts and proposals',
            'Legal professionals transforming sensitive legal documents',
            'Students converting assignments and research papers',
            'HR professionals processing employee documents and policies',
            'Freelancers converting client work for delivery',
            'Anyone converting personal documents without privacy concerns'
        ],
        faq_items=[
            {
                'q': 'How does conversion work without upload?',
                'a': 'Our tool uses JavaScript libraries to process Word documents directly in your browser. No files are sent to external servers, ensuring complete privacy and security.'
            },
            {
                'q': 'What Word formats are supported?',
                'a': 'We support .doc, .docx, .rtf, and other common Word document formats. The tool automatically detects the format and converts it to PDF.'
            },
            {
                'q': 'Is formatting preserved during conversion?',
                'a': 'Yes, our converter preserves fonts, layouts, images, tables, and other formatting elements from your Word document in the resulting PDF file.'
            }
        ],
        is_active=True
    )

    # 3. resume-summary-for-freshers
    variant3 = LongTailVariant.objects.create(
        tool=resume_summary,
        variant_slug='resume-summary-for-freshers',
        meta_title='Resume Summary for Freshers - Free Entry-Level Summary Generator | LamGen',
        meta_description='Generate professional resume summaries for freshers and entry-level positions. Free summary creator with examples and templates. No signup required.',
        unique_intro='Resume Summary for Freshers is a specialized tool designed to help recent graduates and entry-level job seekers create compelling professional summaries. Unlike generic resume builders, this tool focuses on the unique challenges freshers face - highlighting education, internships, projects, and potential rather than extensive work experience. Our AI-powered generator creates summaries that capture recruiters attention and overcome the "no experience" barrier.',
        use_cases=[
            'Recent graduates creating their first professional resume',
            'Entry-level job seekers applying to their first full-time positions',
            'Students preparing for internship applications and campus placements',
            'Career changers entering a new field without direct experience',
            'Freshers applying to multiple companies with tailored summaries',
            'Young professionals updating their resume for better opportunities'
        ],
        faq_items=[
            {
                'q': 'What should a fresher resume summary include?',
                'a': 'A fresher resume summary should highlight education, academic achievements, internships, relevant projects, technical skills, and career goals. Focus on potential and enthusiasm rather than work experience.'
            },
            {
                'q': 'How long should a fresher resume summary be?',
                'a': 'A fresher resume summary should be 2-3 sentences or approximately 50-80 words. Keep it concise but impactful, focusing on your strongest qualifications and career aspirations.'
            },
            {
                'q': 'Can I use this for different industries?',
                'a': 'Yes, our tool generates industry-specific summaries for freshers across tech, finance, healthcare, education, marketing, and other sectors. Simply input your target role and industry.'
            }
        ],
        is_active=True
    )

    # 4. seo-meta-tags-for-shopify
    variant4 = LongTailVariant.objects.create(
        tool=meta_generator,
        variant_slug='seo-meta-tags-for-shopify',
        meta_title='SEO Meta Tags for Shopify - Free E-commerce Meta Generator | LamGen',
        meta_description='Generate optimized SEO meta tags for Shopify stores. Free e-commerce meta tag creator with product titles, descriptions, and best practices.',
        unique_intro='SEO Meta Tags for Shopify is a specialized tool designed specifically for e-commerce store owners using the Shopify platform. Unlike generic meta tag generators, our tool understands Shopify unique requirements, product page structures, and e-commerce SEO best practices. Generate compelling product titles, descriptions, and meta tags that improve your store visibility in Google search and increase click-through rates.',
        use_cases=[
            'Shopify store owners optimizing product page titles and descriptions',
            'E-commerce managers improving category page SEO for better rankings',
            'Digital marketers crafting meta tags for Shopify collections',
            'Dropshippers optimizing product listings for search visibility',
            'Shopify developers implementing SEO best practices for clients',
            'Online retailers competing in competitive e-commerce markets'
        ],
        faq_items=[
            {
                'q': 'What meta tags are important for Shopify SEO?',
                'a': 'For Shopify SEO, focus on title tags (50-60 chars), meta descriptions (150-160 chars), product titles, and collection descriptions. Include target keywords naturally and highlight unique selling points.'
            },
            {
                'q': 'How do Shopify meta tags differ from regular websites?',
                'a': 'Shopify meta tags need to account for product variants, collections, and e-commerce specific terms. Include price, availability, shipping info, and product-specific keywords that shoppers actually search for.'
            },
            {
                'q': 'Can I optimize for multiple products at once?',
                'a': 'Yes, our tool allows batch generation of meta tags for multiple Shopify products. Simply input product details and generate optimized titles and descriptions for your entire catalog.'
            }
        ],
        is_active=True
    )

    # 5. fake-chat-whatsapp-dark-mode
    variant5 = LongTailVariant.objects.create(
        tool=fake_chat,
        variant_slug='fake-chat-whatsapp-dark-mode',
        meta_title='Fake WhatsApp Chat Dark Mode - Free WhatsApp Message Generator | LamGen',
        meta_description='Create fake WhatsApp chats in dark mode. Free WhatsApp message generator with realistic dark theme. Perfect for pranks and demonstrations.',
        unique_intro='Fake WhatsApp Chat Dark Mode is a specialized tool that creates realistic WhatsApp conversation screenshots with an authentic dark theme interface. Perfect for creating demonstrations, social media content, educational materials, or harmless pranks, this tool captures the exact look and feel of WhatsApp dark mode including proper spacing, colors, message bubbles, and status indicators.',
        use_cases=[
            'Content creators creating WhatsApp conversation examples for tutorials',
            'Educators demonstrating digital communication concepts',
            'Social media managers creating engaging conversation content',
            'Developers designing messaging app interfaces and examples',
            'Marketers creating realistic customer service chat examples',
            'Individuals creating harmless pranks with friends (responsibly)'
        ],
        faq_items=[
            {
                'q': 'Does this look like real WhatsApp dark mode?',
                'a': 'Yes, our tool replicates WhatsApp dark mode with accurate colors, fonts, message bubbles, timestamps, and status indicators. The generated screenshots look identical to actual WhatsApp conversations.'
            },
            {
                'q': 'Can I customize dark theme appearance?',
                'a': 'Yes, you can adjust message colors, background shades, and text appearance while maintaining an authentic dark mode aesthetic. Customize while keeping a realistic WhatsApp look.'
            },
            {
                'q': 'Is this tool legal to use?',
                'a': 'Yes, creating fake conversations is legal for educational, creative, and entertainment purposes. However, never use generated content to mislead, defraud, or harm others. Use responsibly and ethically.'
            }
        ],
        is_active=True
    )

    print(f"✅ Successfully created 5 long-tail SEO pages:")
    print(f"   1. compress-png-to-50kb")
    print(f"   2. word-to-pdf-without-upload") 
    print(f"   3. resume-summary-for-freshers")
    print(f"   4. seo-meta-tags-for-shopify")
    print(f"   5. fake-chat-whatsapp-dark-mode")

if __name__ == '__main__':
    create_longtail_pages()
