"""
faculty/views.py
"""

from rest_framework import viewsets, permissions
from .models import Faculty, FacultySubjectAssignment
from .serializers import (
    FacultySerializer,
    FacultyCreateSerializer,
    FacultySubjectAssignmentSerializer,
)


class FacultyViewSet(viewsets.ModelViewSet):
    """CRUD for Faculty profiles."""
    queryset = Faculty.objects.select_related(
        "user", "department"
    ).all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["department", "is_active", "designation"]
    search_fields = [
        "employee_id", "user__first_name", "user__last_name", "user__username"
    ]
    ordering_fields = ["employee_id"]

    def get_serializer_class(self):
        if self.action == "create":
            return FacultyCreateSerializer
        return FacultySerializer


class FacultySubjectAssignmentViewSet(viewsets.ModelViewSet):
    """CRUD for Faculty ↔ Subject teaching assignments."""
    queryset = FacultySubjectAssignment.objects.select_related(
        "faculty__user", "subject"
    ).all()
    serializer_class = FacultySubjectAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["faculty", "subject", "academic_year", "section"]
    search_fields = ["faculty__employee_id", "subject__code"]
