"""
reports/urls.py
"""

from django.urls import path
from .views import DashboardView, DepartmentReportView, StudentReportView, student_report_pdf_view

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path(
        "department/<int:dept_id>/",
        DepartmentReportView.as_view(),
        name="department-report",
    ),
    path(
        "student/<int:student_id>/",
        StudentReportView.as_view(),
        name="student-report",
    ),
    path(
        "student/<int:student_id>/pdf/",
        student_report_pdf_view,
        name="student-report-pdf",
    ),
]
