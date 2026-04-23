"""
academics/urls.py
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, SubjectViewSet

router = DefaultRouter()
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"subjects", SubjectViewSet, basename="subject")

urlpatterns = [
    path("", include(router.urls)),
]
