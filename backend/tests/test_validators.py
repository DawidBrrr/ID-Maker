import io
import pytest
from src.utils import validators

class DummyFile:
    """Prosty mock FileStorage do testów"""
    def __init__(self, content=b"", filename="test.jpg"):
        self._io = io.BytesIO(content)
        self.filename = filename

    def seek(self, *args, **kwargs):
        return self._io.seek(*args, **kwargs)

    def tell(self):
        return self._io.tell()

    def read(self, *args, **kwargs):
        return self._io.read(*args, **kwargs)

    def __enter__(self):
        return self._io.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._io.__exit__(exc_type, exc_val, exc_tb)

def test_validate_file_good_jpg():
    # Generujemy w pamięci mały obraz 50x50px w formacie JPEG
    from PIL import Image
    import io
    
    # Tworzymy obraz 50x50px z białym tłem
    img = Image.new('RGB', (50, 50), color='white')
    
    # Zapisujemy do bufora w pamięci jako JPEG
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    jpeg_data = buffer.getvalue()
    
    file = DummyFile(content=jpeg_data, filename="test.jpg")
    ok, msg = validators.validate_file(file)
    assert ok is True
    assert msg is None

def test_validate_file_bad_extension():
    file = DummyFile(content=b"abcd", filename="test.txt")
    ok, msg = validators.validate_file(file)
    assert ok is False
    assert "Niedozwolone rozszerzenie" in msg

def test_validate_file_too_large():
    file = DummyFile(content=b"a" * (validators.config.MAX_CONTENT_LENGTH + 1), filename="test.jpg")
    ok, msg = validators.validate_file(file)
    assert ok is False
    assert "Plik za duży" in msg

def test_validate_file_empty():
    file = DummyFile(content=b"", filename="test.jpg")
    ok, msg = validators.validate_file(file)
    assert ok is False
    assert "Plik jest pusty" in msg

def test_validate_document_type():
    assert validators.validate_document_type("passport") is True
    assert validators.validate_document_type("id_card") is True
    assert validators.validate_document_type("fake_type") is False

def test_sanitize_filename():
    assert validators.sanitize_filename("../../etc/passwd") == "passwd"
    assert validators.sanitize_filename("a" * 120 + ".jpg").startswith("a" * 95)
    assert validators.sanitize_filename("test file.jpg") == "test_file.jpg"
    assert validators.sanitize_filename(".hidden")[:5] == "file_"

def test_validate_session_id():
    assert validators.validate_session_id("abc-123-xyz") is True
    assert validators.validate_session_id("") is False
    assert validators.validate_session_id("!@#$$%") is False
    assert validators.validate_session_id("a" * 60) is False