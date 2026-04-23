"""
reports/views.py
Dashboard and aggregation APIs.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count, Avg, Q

from django.http import HttpResponse, Http404
from accounts.models import User
from academics.models import Department, Subject
from students.models import Student, Enrollment
from faculty.models import Faculty
from attendance.models import Attendance
from exams.models import Marks, Result


class DashboardView(APIView):
    """
    GET /api/reports/dashboard/
    Returns high-level counts and stats for the admin dashboard.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = {
            "total_students": Student.objects.filter(is_active=True).count(),
            "total_faculty": Faculty.objects.filter(is_active=True).count(),
            "total_departments": Department.objects.count(),
            "total_subjects": Subject.objects.count(),
            "total_users": User.objects.filter(is_active=True).count(),
            "students_per_department": list(
                Department.objects.annotate(
                    count=Count("students")
                ).values("code", "name", "count")
            ),
            "students_per_semester": list(
                Student.objects.filter(is_active=True)
                .values("semester")
                .annotate(count=Count("id"))
                .order_by("semester")
            ),
        }
        return Response(data)


class DepartmentReportView(APIView):
    """
    GET /api/reports/department/<dept_id>/
    Detailed report for a specific department.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, dept_id):
        try:
            dept = Department.objects.get(pk=dept_id)
        except Department.DoesNotExist:
            return Response(
                {"detail": "Department not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        students = Student.objects.filter(department=dept, is_active=True)
        data = {
            "department": {"id": dept.id, "code": dept.code, "name": dept.name},
            "total_students": students.count(),
            "total_faculty": Faculty.objects.filter(department=dept, is_active=True).count(),
            "total_subjects": Subject.objects.filter(department=dept).count(),
            "students_by_semester": list(
                students.values("semester")
                .annotate(count=Count("id"))
                .order_by("semester")
            ),
            "average_sgpa_by_semester": list(
                Result.objects.filter(student__department=dept)
                .values("semester")
                .annotate(avg_sgpa=Avg("sgpa"))
                .order_by("semester")
            ),
        }
        return Response(data)


class StudentReportView(APIView):
    """
    GET /api/reports/student/<student_id>/
    Full academic report card for a student.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id):
        try:
            student = Student.objects.select_related("user", "department").get(
                pk=student_id
            )
        except Student.DoesNotExist:
            return Response(
                {"detail": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Marks grouped by subject
        marks_qs = (
            Marks.objects.filter(student=student)
            .select_related("subject", "exam")
            .order_by("subject__code", "exam__exam_type")
        )
        marks_data = {}
        for m in marks_qs:
            key = m.subject.code
            if key not in marks_data:
                marks_data[key] = {
                    "subject_code": m.subject.code,
                    "subject_name": m.subject.name,
                    "credits": m.subject.credits,
                    "exams": [],
                }
            marks_data[key]["exams"].append({
                "exam_name": m.exam.name,
                "exam_type": m.exam.exam_type,
                "marks_obtained": str(m.marks_obtained),
                "max_marks": m.exam.max_marks,
            })

        # Attendance summary
        attendance_qs = (
            Attendance.objects.filter(student=student)
            .values("subject__code", "subject__name")
            .annotate(
                total=Count("id"),
                present=Count("id", filter=Q(status="present")),
            )
        )
        attendance_data = []
        for row in attendance_qs:
            total = row["total"]
            present = row["present"]
            attendance_data.append({
                "subject_code": row["subject__code"],
                "subject_name": row["subject__name"],
                "total_classes": total,
                "present": present,
                "percentage": round((present / total) * 100, 2) if total else 0,
            })

        # Results
        results = list(
            Result.objects.filter(student=student)
            .order_by("semester")
            .values("semester", "sgpa", "cgpa", "total_credits", "credits_earned")
        )

        data = {
            "student": {
                "usn": student.usn,
                "name": student.user.get_full_name() or student.user.username,
                "department": student.department.code,
                "semester": student.semester,
                "section": student.section,
            },
            "marks": list(marks_data.values()),
            "attendance": attendance_data,
            "results": results,
        }
        return Response(data)


from .pdf_builder import ReportCardBuilder

def student_report_pdf_view(request, student_id):
    """
    Standard Django view to generate and return a professional PDF report card.
    GET /reports/student/<student_id>/pdf/?semester=<int>
    """
    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)

    # Default to student's current semester if not provided
    semester_param = request.GET.get("semester")
    
    try:
        student = Student.objects.get(pk=student_id)
        if not semester_param:
            semester = student.semester
        else:
            semester = int(semester_param)
    except (Student.DoesNotExist, ValueError):
        raise Http404("Invalid student ID or semester.")

    builder = ReportCardBuilder(student_id, semester)
    success = builder.fetch_data()

    if not success:
        return HttpResponse("No marks found for this student in the specified semester.", status=404)

    pdf_buffer = builder.build_pdf()
    
    filename = f"report_card_{student.usn}_{semester}.pdf"
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
