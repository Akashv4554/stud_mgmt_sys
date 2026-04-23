"""
students/urls.py
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, EnrollmentViewSet

router = DefaultRouter()
router.register(r"", StudentViewSet, basename="student")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollment")

urlpatterns = [
    path("", include(router.urls)),
]
