from documents.services.document_parser import parse_gs1code
from pathlib import Path
import pytest

# test parse_gs1code output
@pytest.mark.django_db()
def test_single_image_scan_of_parse_gs1code():
    test_dir = Path(__file__).parent

    file_path = test_dir / "test_files" / "equipment_gs1.jpg"

    output = parse_gs1code(file=file_path)
    assert output
