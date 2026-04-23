"""
backend/urls.py
Root URL configuration. 
Includes both legacy API routes and fixed Django Template routes.
"""

from django.contrib import admin
from django.urls import path, include
from . import views

template_urlpatterns = [
    path('', views.index_redirect, name='index'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/faculty/', views.faculty_dashboard, name='faculty_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    
    path('students/', views.students_view, name='students'),
    path('faculty/', views.faculty_view, name='faculty'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('attendance/student/<int:student_id>/', views.student_attendance_detail, name='student_attendance_detail'),
    path('departments/', views.departments_view, name='departments'),
    path('departments/<int:id>/', views.department_detail, name='department_detail'),


    
    # PDF
    path('reports/student/<int:student_id>/pdf/', views.student_report_pdf, name='student_pdf'),
    path('reports/attendance/pdf/', views.attendance_pdf_report, name='attendance_pdf_report'),

    
    # Fixed Auth (Custom views)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(template_urlpatterns)),
]
