from django.contrib import admin

from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display  = ('user', 'date', 'status', 'timestamp')
    list_filter   = ('date', 'status')
    search_fields = ('user__username',)
    date_hierarchy = 'date'
# Register your models here.
