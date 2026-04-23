"""
exams/urls.py
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, MarksViewSet, ResultViewSet

router = DefaultRouter()
router.register(r"exams", ExamViewSet, basename="exam")
router.register(r"marks", MarksViewSet, basename="marks")
router.register(r"results", ResultViewSet, basename="result")

urlpatterns = [
    path("", include(router.urls)),
]
