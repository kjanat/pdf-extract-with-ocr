"""
Tests for PDF processing services
"""
import os
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from services import PDFProcessor
from db import OCRJob


@pytest.fixture
def processor():
    """Create a PDFProcessor instance"""
    return PDFProcessor()


@pytest.fixture
def sample_pdf():
    """Create a temporary PDF file for testing"""
    # Create a minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000262 00000 n
0000000355 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
433
%%EOF
"""

    fd, path = tempfile.mkstemp(suffix='.pdf')
    with os.fdopen(fd, 'wb') as f:
        f.write(pdf_content)

    yield path

    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = MagicMock()
    return session


class TestPDFProcessor:
    """Tests for PDFProcessor service"""

    @patch('services.SessionLocal')
    @patch('services.calculate_file_hash')
    @patch('services.is_scanned')
    @patch('services.extract_text_pymupdf')
    @patch('services.clean_text')
    @patch('services.get_pdf_page_count')
    def test_process_pdf_success(
        self,
        mock_page_count,
        mock_clean_text,
        mock_extract_text,
        mock_is_scanned,
        mock_hash,
        mock_session_local,
        processor,
        sample_pdf
    ):
        """Test successful PDF processing"""
        # Setup mocks for text extraction
        mock_hash.return_value = "abc123"
        mock_is_scanned.return_value = False
        mock_extract_text.return_value = "Sample text"
        mock_clean_text.return_value = "Sample text"
        mock_page_count.return_value = 1

        # Mock database session and job
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        mock_job = Mock(spec=OCRJob)
        mock_job.status = "PENDING"
        mock_job.method = None
        mock_job.result_text = None

        # First call returns existing job, second call returns None (no cache)
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_job,  # existing job
            None       # no cached result
        ]

        # Process PDF
        result = processor.process_pdf(sample_pdf, "test-task-id", cleanup=False)

        # Verify result structure
        assert result["status"] == "completed"
        assert "method" in result
        assert "text" in result
        assert "page_count" in result
        assert "cached" in result
        assert "duration_ms" in result
        assert "file_size_kb" in result

    @patch('services.SessionLocal')
    @patch('services.calculate_file_hash')
    def test_process_pdf_with_cache(
        self,
        mock_hash,
        mock_session_local,
        processor,
        sample_pdf
    ):
        """Test PDF processing with cached result"""
        # Setup mocks
        mock_hash.return_value = "abc123"

        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        # Current job
        mock_current_job = Mock(spec=OCRJob)
        mock_current_job.id = "test-task-id"
        mock_current_job.status = "PENDING"

        # Cached job with completed status
        mock_cached_job = Mock(spec=OCRJob)
        mock_cached_job.status = "COMPLETED"
        mock_cached_job.method = "PYMUPDF"
        mock_cached_job.result_text = "Cached text"
        mock_cached_job.duration_ms = 1000
        mock_cached_job.page_count = 2

        # Configure query to return current job first, then cached job
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_current_job,  # First call for existing job
            mock_cached_job     # Second call for cache check
        ]

        # Process PDF
        result = processor.process_pdf(sample_pdf, "test-task-id", cleanup=False)

        # Verify result uses cached data
        assert result["status"] == "completed"
        assert "method" in result
        assert "text" in result
        assert "cached" in result
        assert result["cached"] is True

    @patch('services.SessionLocal')
    @patch('services.calculate_file_hash')
    @patch('services.is_scanned')
    @patch('services.extract_text_from_scanned_pdf')
    @patch('services.clean_text')
    @patch('services.get_pdf_page_count')
    def test_process_scanned_pdf(
        self,
        mock_page_count,
        mock_clean_text,
        mock_extract_text_ocr,
        mock_is_scanned,
        mock_hash,
        mock_session_local,
        processor,
        sample_pdf
    ):
        """Test processing a scanned PDF with OCR"""
        # Setup mocks
        mock_hash.return_value = "abc123"
        mock_is_scanned.return_value = True  # Scanned PDF
        mock_extract_text_ocr.return_value = "OCR extracted text"
        mock_clean_text.return_value = "OCR extracted text"
        mock_page_count.return_value = 1

        # Mock database session
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)

        mock_job = Mock(spec=OCRJob)
        mock_job.status = "PENDING"

        # First call returns existing job, second call returns None (no cache)
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_job,
            None
        ]

        # Process PDF
        result = processor.process_pdf(sample_pdf, "test-task-id", cleanup=False)

        # Verify OCR was used
        assert result["status"] == "completed"
        assert "method" in result
        assert "text" in result
        mock_extract_text_ocr.assert_called_once()

    def test_process_pdf_cleanup(self, processor, sample_pdf):
        """Test that cleanup removes the PDF file"""
        assert os.path.exists(sample_pdf)

        # Process with cleanup enabled
        with patch('services.SessionLocal'), \
             patch('services.calculate_file_hash'), \
             patch('services.is_scanned'), \
             patch('services.extract_text_pymupdf'), \
             patch('services.clean_text'), \
             patch('services.get_pdf_page_count'):

            processor.process_pdf(sample_pdf, "test-task-id", cleanup=True)

        # File should be deleted
        assert not os.path.exists(sample_pdf)
