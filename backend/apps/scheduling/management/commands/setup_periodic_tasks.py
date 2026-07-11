from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Registers Celery Beat periodic tasks in the database. Run once after first migrate."

    def handle(self, *args, **options):
        from django_celery_beat.models import IntervalSchedule, PeriodicTask

        # Every 1 minute — expire stale payment holds
        every_minute, _ = IntervalSchedule.objects.get_or_create(
            every=1, period=IntervalSchedule.MINUTES
        )
        PeriodicTask.objects.update_or_create(
            name="Release expired payment holds",
            defaults={
                "interval": every_minute,
                "task": "apps.scheduling.tasks.release_expired_payment_holds",
            },
        )

        # Every 24 hours at midnight — generate upcoming slots
        every_day, _ = IntervalSchedule.objects.get_or_create(
            every=24, period=IntervalSchedule.HOURS
        )
        PeriodicTask.objects.update_or_create(
            name="Generate upcoming session slots",
            defaults={
                "interval": every_day,
                "task": "apps.scheduling.tasks.generate_upcoming_slots",
            },
        )

        self.stdout.write(self.style.SUCCESS("Periodic tasks registered successfully."))
