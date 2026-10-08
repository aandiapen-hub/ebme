from assets.models import Tbljob
from .validators import validate_job

def save_job_service(*, job=None, **data):
    if job is None:
        job = Tbljob()

    for field, value in data.items():
        setattr(job, field, value)

    validate_job(job)

    job.save()

    return job

