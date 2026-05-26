import pytest
from jobs.tests.factories import(
    JobFactory,
    TestsCarriedOutFactory,
)

@pytest.fixture
def job():
    return JobFactory


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



