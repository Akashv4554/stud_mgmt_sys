from django.contrib import admin
from .models import Faculty, FacultySubjectAssignment


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ["employee_id", "user", "department", "designation", "is_active"]
    list_filter = ["department", "is_active", "designation"]
    search_fields = ["employee_id", "user__first_name", "user__last_name"]


@admin.register(FacultySubjectAssignment)
class FacultySubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ["faculty", "subject", "academic_year", "section"]
    list_filter = ["academic_year", "section"]
