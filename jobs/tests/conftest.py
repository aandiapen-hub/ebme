import pytest
from jobs.tests.factories import(
    JobFactory,
    TestsCarriedOutFactory,
    ChecklistsFactory,
    TestResultFactory,
)
from assets.tests.factories import AssetFactory


@pytest.fixture
def test_eq():
    return AssetFactory(is_test_eq=True)


@pytest.fixture
def check():
    return ChecklistsFactory


@pytest.fixture
def check_result():
    return TestResultFactory

@pytest.fixture
def jobs():
    def _create_jobs(count=10, **kwargs):
        return JobFactory.create_batch(count, **kwargs)
    return _create_jobs


@pytest.fixture
def test_carried_out():
    return TestsCarriedOutFactory

@pytest.fixture
def test_carried_out_batch():
    def _create_tests_carried_out(count=10, **kwargs):
        return TestsCarriedOutFactory.create_batch(count, **kwargs)

    return _create_tests_carried_out



