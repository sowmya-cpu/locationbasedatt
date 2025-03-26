from django.db import models

class UserProfile(models.Model):
    username = models.CharField(max_length=150, unique=True)
    smile_image = models.ImageField(upload_to='user_images/')
    angry_image = models.ImageField(upload_to='user_images/')

    def __str__(self):
        return self.username

class Attendance(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"
