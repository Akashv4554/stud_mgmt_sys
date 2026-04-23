"""
academics/views.py
"""

from rest_framework import viewsets, permissions
from django.db.models import Count

from .models import Department, Subject
from .serializers import DepartmentSerializer, SubjectSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """CRUD for Departments. Annotates counts of students, faculty, subjects."""
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["code"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]

    def get_queryset(self):
        return Department.objects.annotate(
            student_count=Count("students", distinct=True),
            faculty_count=Count("faculty_members", distinct=True),
            subject_count=Count("subjects", distinct=True),
        )


class SubjectViewSet(viewsets.ModelViewSet):
    """CRUD for Subjects with filtering by department, semester, type."""
    queryset = Subject.objects.select_related("department").all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["department", "semester", "subject_type", "is_elective"]
    search_fields = ["code", "name"]
    ordering_fields = ["code", "semester", "credits"]
