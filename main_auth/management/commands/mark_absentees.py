# your_app/management/commands/mark_absentees.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from main_auth.models import Attendance

User = get_user_model()

class Command(BaseCommand):
    help = 'Mark students absent if they haven’t checked in by 22:59'

    def handle(self, *args, **options):
        today = timezone.localdate()
        present_ids = Attendance.objects.filter(date=today).values_list('user_id', flat=True)
        absentees = User.objects.exclude(id__in=present_ids)
        for user in absentees:
            Attendance.objects.create(user=user, date=today, status='absent')
        self.stdout.write(f"Marked {absentees.count()} absentees for {today}")
