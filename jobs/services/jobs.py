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

def get_parts_used_cost(part_original_price):
    vat = 0.2
    mark_up = 0.1
    price_with_vat = float(part_original_price) * (1+0.2)
    price_with_markup = price_with_vat * (1+0.1)
    return round(price_with_markup, 2)
