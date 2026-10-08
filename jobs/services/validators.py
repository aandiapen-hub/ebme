from django.core.exceptions import ValidationError
from django.db.models import Q

def validate_dates(job, errors):
    if job.jobenddate and job.jobstartdate:
        if job.jobstartdate > job.jobenddate:
            errors.setdefault('jobenddate', []).append('End date has to be on or after start date')
            errors.setdefault('jobstartdate', []).append('start date has to be on or before end date')


    if job.jobenddate and not job.jobstartdate:
        errors.setdefault('jobstartdate', []).append('Job start date missing')

def validate_status(job, errors):
    if job.jobstatusid.is_closed:
        if not job.jobenddate:
            errors.setdefault('jobenddate', []).append('Job end date missing')
        if not job.jobstartdate:
            errors.setdefault('jobstartdate', []).append('Job start date missing')

    if job.jobenddate and not job.jobstatusid.is_closed:
        errors.setdefault('jobstatusid', []).append('Update job status or remove end date')

def validate_job_type(job, errors):
    # filter open jobs
    asset_open_jobs = job.assetid.jobs.filter(
        Q(jobstatusid__is_closed=False) | Q(jobstatusid__is_closed__isnull=True)
    )

    #exclude current job
    if job.pk:
        asset_open_jobs = asset_open_jobs.exclude(pk=job.pk)

    same_job_type = asset_open_jobs.filter(
        jobtypeid=job.jobtypeid
    )

    open_job_dates = same_job_type.values_list('jobstartdate', flat=True)

    # allow logging of old jobs even if newer job of same type exists
    if open_job_dates.exists():
        earliest_open_job_date = min(open_job_dates)
        if job.jobenddate and job.jobenddate > earliest_open_job_date:
            errors.setdefault('jobtypeid', []).append('Another open job of this type already exists on this asset')

    # prevent logging of old jobs if open jobs do not have a start date
    if same_job_type.exists() and not same_job_type.exists():
            errors.setdefault('jobtypeid', []).append('Another open job of this type already exists on this asset. Update the existing open jobs.')


def validate_job(job):
    errors = {}
    validate_dates(job, errors)
    validate_status(job, errors)
    validate_job_type(job, errors)
    
    if errors:
        raise ValidationError(errors)


