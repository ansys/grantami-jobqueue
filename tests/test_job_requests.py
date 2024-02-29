import pytest

from ansys.grantami.jobqueue import ExcelImportJobRequest
from common import TEST_ARTIFACT_DIR


def test_no_data_combined():
    with pytest.raises(ValueError, match="Excel import jobs must contain either"):
        ExcelImportJobRequest(name="ExcelImportTest", description="Import test no data")


def test_both_combined_and_template():
    with pytest.raises(ValueError) as excinfo:
        _ = ExcelImportJobRequest(
            name="ExcelImportTest",
            description="Import test with too much data",
            combined_files=[TEST_ARTIFACT_DIR / "TextDataTest.dat"],
            template_files=[TEST_ARTIFACT_DIR / "TextDataTest.dat"],
        )
    assert "Cannot create Excel import job with both" in str(excinfo.value)
