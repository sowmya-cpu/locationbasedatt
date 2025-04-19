# main_auth/models.py

from django.db import models

class UserProfile(models.Model):
    username      = models.CharField(max_length=150, unique=True)
    smile_image   = models.ImageField(upload_to='user_images/')
    angry_image   = models.ImageField(upload_to='user_images/')

    def __str__(self):
        return self.username

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent',  'Absent'),
    ]

    # ← now pointing at UserProfile instead of settings.AUTH_USER_MODEL
    user      = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date      = models.DateField()
    status    = models.CharField(max_length=7, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering        = ['-date', 'user']

    def __str__(self):
        return f"{self.user.username} — {self.date} — {self.status}"
