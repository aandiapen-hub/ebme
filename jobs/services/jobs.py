from assets.models import Tbljob
from .validators import validate_job, validate_formsets

def save_job_service(*, job=None, formsets=None, **data):
    if job is None:
        job = Tbljob()

    for field, value in data.items():
        setattr(job, field, value)

    validate_job(job)


    if formsets:
        validate_formsets(job, formsets)

    job.save()
    return job

