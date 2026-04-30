"""
Unit tests for thesis services.
"""
import io
from unittest.mock import MagicMock, patch

import pytest


class TestPDFService:
    """Unit tests for PDFService."""

    def test_clean_text_removes_nonprintable(self):
        from thesis.services.pdf_service import PDFService
        raw = 'Hello\x00World\x01\x02'
        result = PDFService.clean_text(raw)
        assert '\x00' not in result
        assert '\x01' not in result
        assert 'Hello' in result
        assert 'World' in result

    def test_clean_text_normalises_whitespace(self):
        from thesis.services.pdf_service import PDFService
        raw = 'Hello   World\n\n\n\nEnd'
        result = PDFService.clean_text(raw)
        assert '   ' not in result
        assert '\n\n\n' not in result

    def test_chunk_text_respects_token_limit(self):
        from thesis.services.pdf_service import PDFService
        import tiktoken
        # Create text that is definitely more than 2000 tokens
        long_text = 'word ' * 5000
        chunks = PDFService.chunk_text(long_text)
        enc = tiktoken.get_encoding('cl100k_base')
        for chunk in chunks:
            assert len(enc.encode(chunk)) <= PDFService.MAX_TOKENS_PER_CHUNK

    def test_chunk_text_empty_string(self):
        from thesis.services.pdf_service import PDFService
        chunks = PDFService.chunk_text('')
        assert isinstance(chunks, list)

    def test_chunk_text_short_text_single_chunk(self):
        from thesis.services.pdf_service import PDFService
        text = 'Short text that fits in one chunk.'
        chunks = PDFService.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_extract_text_calls_fitz(self):
        from thesis.services.pdf_service import PDFService
        mock_page = MagicMock()
        mock_page.get_text.return_value = 'Page text'
        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        with patch('fitz.open', return_value=mock_doc):
            result = PDFService.extract_text('/fake/path.pdf')
        assert 'Page text' in result

    def test_process_returns_list_of_strings(self):
        from thesis.services.pdf_service import PDFService
        with patch.object(PDFService, 'extract_text', return_value='Some text content'):
            chunks = PDFService.process('/fake/path.pdf')
        assert isinstance(chunks, list)
        assert all(isinstance(c, str) for c in chunks)


class TestLLMService:
    """Unit tests for LLMService."""

    def test_generate_thesis_success(self):
        from thesis.services.llm_service import LLMService
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='Generated thesis content')]
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client
            service = LLMService(api_key='test-key')
            result = service.generate_thesis(['chunk1', 'chunk2'], 'Test Title')
        assert result == 'Generated thesis content'

    def test_generate_thesis_retries_on_transient_error(self):
        import anthropic as anthropic_module
        from thesis.services.llm_service import LLMService
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='Success after retry')]
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            # Fail twice, succeed on third
            mock_client.messages.create.side_effect = [
                anthropic_module.APIConnectionError(request=MagicMock()),
                anthropic_module.APIConnectionError(request=MagicMock()),
                mock_message,
            ]
            mock_anthropic.return_value = mock_client
            service = LLMService(api_key='test-key')
            with patch('time.sleep'):  # Don't actually sleep in tests
                result = service.generate_thesis(['chunk1'], 'Test Title')
        assert result == 'Success after retry'
        assert mock_client.messages.create.call_count == 3

    def test_generate_thesis_raises_after_max_retries(self):
        import anthropic as anthropic_module
        from thesis.services.llm_service import LLMService, LLMServiceError
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = anthropic_module.APIConnectionError(
                request=MagicMock()
            )
            mock_anthropic.return_value = mock_client
            service = LLMService(api_key='test-key')
            with patch('time.sleep'):
                with pytest.raises(LLMServiceError):
                    service.generate_thesis(['chunk1'], 'Test Title')
        assert mock_client.messages.create.call_count == 3


class TestThesisPDFGenerator:
    """Unit tests for ThesisPDFGenerator."""

    def test_build_html_contains_title(self):
        from thesis.services.thesis_pdf import ThesisPDFGenerator
        html = ThesisPDFGenerator._build_html('# Abstract\n\nContent.', 'My Test Thesis')
        assert 'My Test Thesis' in html

    def test_build_html_converts_markdown(self):
        from thesis.services.thesis_pdf import ThesisPDFGenerator
        html = ThesisPDFGenerator._build_html('# Section\n\nParagraph text.', 'Title')
        assert '<h1>' in html
        assert '<p>' in html

    def test_render_returns_bytes(self):
        from thesis.services.thesis_pdf import ThesisPDFGenerator
        thesis_text = '# Abstract\n\nThis is a test.\n\n# Introduction\n\nContent here.'
        result = ThesisPDFGenerator.render(thesis_text, 'Test Thesis')
        assert isinstance(result, bytes)
        assert len(result) > 0
        # PDF magic bytes
        assert result[:4] == b'%PDF'
