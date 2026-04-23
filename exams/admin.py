from django.contrib import admin
from .models import Exam, Marks, Result


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ["name", "exam_type", "semester", "academic_year", "max_marks"]
    list_filter = ["exam_type", "semester", "academic_year"]
    search_fields = ["name"]


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ["student", "subject", "exam", "marks_obtained", "is_absent"]
    list_filter = ["exam", "subject", "is_absent"]
    search_fields = ["student__usn", "subject__code"]


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ["student", "semester", "academic_year", "sgpa", "cgpa", "is_published"]
    list_filter = ["semester", "academic_year", "is_published"]
    search_fields = ["student__usn"]
