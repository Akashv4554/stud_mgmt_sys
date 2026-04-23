"""
faculty/urls.py
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FacultyViewSet, FacultySubjectAssignmentViewSet

router = DefaultRouter()
router.register(r"", FacultyViewSet, basename="faculty")
router.register(
    r"assignments", FacultySubjectAssignmentViewSet, basename="faculty-assignment"
)

urlpatterns = [
    path("", include(router.urls)),
]
