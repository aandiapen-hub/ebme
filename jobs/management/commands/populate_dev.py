from django.core.management.base import BaseCommand

from jobs.tests.factories import JobFactory


class Command(BaseCommand):
    help = "Populate the development database with test data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--jobs",
            type=int,
            default=20,
        )

    def handle(self, *args, **options):
        jobs_count = options["jobs"]

        self.stdout.write("Creating development data...")

        JobFactory.create_batch(jobs_count)

        self.stdout.write(
            self.style.SUCCESS("Development data created successfully.")
        )
