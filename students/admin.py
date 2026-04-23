from django.contrib import admin
from .models import Student, Enrollment


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["usn", "user", "department", "semester", "section", "is_active"]
    list_filter = ["department", "semester", "section", "is_active"]
    search_fields = ["usn", "user__first_name", "user__last_name"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "subject", "academic_year", "enrolled_at"]
    list_filter = ["academic_year"]
    search_fields = ["student__usn", "subject__code"]
