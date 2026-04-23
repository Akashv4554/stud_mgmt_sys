"""
students/views.py
"""

from rest_framework import viewsets, permissions
from .models import Student, Enrollment
from .serializers import (
    StudentSerializer,
    StudentCreateSerializer,
    EnrollmentSerializer,
)


class StudentViewSet(viewsets.ModelViewSet):
    """CRUD for Student profiles."""
    queryset = Student.objects.select_related(
        "user", "department"
    ).all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["department", "semester", "section", "is_active"]
    search_fields = ["usn", "user__first_name", "user__last_name", "user__username"]
    ordering_fields = ["usn", "semester"]

    def get_serializer_class(self):
        if self.action == "create":
            return StudentCreateSerializer
        return StudentSerializer


class EnrollmentViewSet(viewsets.ModelViewSet):
    """CRUD for Enrollments (Student ↔ Subject)."""
    queryset = Enrollment.objects.select_related(
        "student", "subject"
    ).all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["student", "subject", "academic_year"]
    search_fields = ["student__usn", "subject__code"]
    ordering_fields = ["enrolled_at"]
