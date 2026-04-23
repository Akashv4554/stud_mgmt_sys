from django.contrib import admin
from .models import Department, Subject


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "hod_name", "created_at"]
    search_fields = ["code", "name"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "department", "semester", "credits", "subject_type"]
    list_filter = ["department", "semester", "subject_type", "is_elective"]
    search_fields = ["code", "name"]
