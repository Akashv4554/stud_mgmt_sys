from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["student", "subject", "date", "period", "status", "marked_by"]
    list_filter = ["status", "date", "subject"]
    search_fields = ["student__usn", "subject__code"]
