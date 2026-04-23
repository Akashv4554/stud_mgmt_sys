from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden, FileResponse

from accounts.models import User
from academics.models import Department, Subject
from students.models import Student, Enrollment
from faculty.models import Faculty
from attendance.models import Attendance
from exams.models import Marks, Result
from reports.pdf_builder import ReportCardBuilder
from reports.attendance_pdf import AttendanceReportBuilder

def index_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.is_superuser:
        return redirect('admin_dashboard')

    if hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')

    if hasattr(request.user, 'faculty_profile'):
        return redirect('faculty_dashboard')

    return redirect('login')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Role-based landing page (Case-insensitive)
            u_role = (user.role or "").lower()
            if u_role == User.Role.ADMIN or user.is_superuser:
                return redirect('admin_dashboard')
            elif u_role == User.Role.FACULTY:
                return redirect('faculty_dashboard')
            elif u_role == User.Role.STUDENT:
                return redirect('student_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, "registration/login.html")

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")

@login_required
def admin_dashboard(request):
    total_students = Student.objects.count()
    total_faculty = Faculty.objects.count()
    total_departments = Department.objects.count()
    
    # Department-wise student counts
    dept_student_data = Student.objects.values(
        'department__name'
    ).annotate(total=Count('id')).order_by('department__name')

    # Department-wise faculty counts
    dept_faculty_data = Faculty.objects.values(
        'department__name'
    ).annotate(total=Count('id')).order_by('department__name')

    context = {
        'role': 'Admin',
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_departments': total_departments,
        'dept_student_data': list(dept_student_data),
        'dept_faculty_data': list(dept_faculty_data),
    }
    return render(request, 'dashboard_admin.html', context)

@login_required
def faculty_dashboard(request):
    return render(request, 'dashboard_faculty.html', {"role": "Faculty"})

@login_required
def student_dashboard(request):
    return render(request, 'dashboard_student.html', {"role": "Student"})

@login_required
def students_view(request):
    search = request.GET.get('search')
    dept_id = request.GET.get('department')
    semester = request.GET.get('semester')
    
    print(f"DEBUG: Student Search: {search}")
    
    students = Student.objects.select_related("user", "department").filter(is_active=True)
    
    # RBAC: Faculty can only see students from their department
    user_role = (request.user.role or "").lower()
    if user_role == User.Role.FACULTY:
        faculty = Faculty.objects.filter(user=request.user).first()
        if faculty:
            students = students.filter(department=faculty.department)
        else:
            students = Student.objects.none()
    
    # Apply Filters
    if dept_id:
        students = students.filter(department_id=dept_id)
    if semester:
        students = students.filter(semester=semester)
    
    if search:
        name_parts = search.strip().split()
        if len(name_parts) >= 2:
            students = students.filter(
                Q(user__first_name__icontains=name_parts[0]) &
                Q(user__last_name__icontains=name_parts[1])
            )
        else:
            students = students.filter(
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(usn__icontains=search)
            )
    
    print(f"DEBUG: Filtered Student Count: {students.count()}")
    
    # Performance: Limit results
    students = students[:100]
        
    return render(request, 'students.html', {
        'students': students, 
        'selected_sem': semester,
        'selected_dept': dept_id,
        'search': search
    })

@login_required
def faculty_view(request):
    search = request.GET.get('search')
    dept_id = request.GET.get('department')
    
    print(f"DEBUG: Faculty Search: {search}")
    
    faculty = Faculty.objects.select_related("user", "department").filter(is_active=True)
    departments = Department.objects.all().order_by('name')
    
    if search:
        name_parts = search.strip().split()
        if len(name_parts) >= 2:
            faculty = faculty.filter(
                Q(user__first_name__icontains=name_parts[0]) &
                Q(user__last_name__icontains=name_parts[1])
            )
        else:
            faculty = faculty.filter(
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(employee_id__icontains=search)
            )

    if dept_id and str(dept_id).strip():
        faculty = faculty.filter(department_id=dept_id)
        
    print(f"DEBUG: Filtered Faculty Count: {faculty.count()}")
        
    return render(request, 'faculty.html', {
        'faculty': faculty, 
        'departments': departments,
        'search': search,
        'selected_dept': dept_id
    })

@login_required
def attendance_view(request):
    search = request.GET.get('search')
    semester = request.GET.get('semester')
    
    # Aggregated Stats for Admin/Faculty, Personal Logs for Student
    user_role = (request.user.role or "").lower()
    
    # Base Queryset - querying from Student model
    qs = Student.objects.select_related("user", "department").filter(is_active=True)

    # RBAC Privacy
    if request.user.is_superuser or user_role == User.Role.ADMIN:
        # Admins see everything
        pass
    elif user_role == User.Role.STUDENT:
        qs = qs.filter(user=request.user)
    elif user_role == User.Role.FACULTY:
        faculty = Faculty.objects.filter(user=request.user).first()
        if faculty:
            qs = qs.filter(department=faculty.department)
        else:
            qs = Student.objects.none()
    else:
        # Unauthorized roles or anonymous? Default to none for safety
        qs = Student.objects.none()

    # Filtering
    if search:
        print(f"DEBUG: Attendance Search: {search}")
        name_parts = search.strip().split()
        if len(name_parts) >= 2:
            qs = qs.filter(
                Q(user__first_name__icontains=name_parts[0]) &
                Q(user__last_name__icontains=name_parts[1])
            )
        else:
            qs = qs.filter(
                Q(usn__icontains=search) | 
                Q(user__username__icontains=search) | 
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
    if semester:
        qs = qs.filter(semester=semester)

    # Ensure distinct
    qs = qs.distinct().order_by('usn')

    print(f"DEBUG: Filtered Students for Attendance: {qs.count()}")

    return render(request, 'attendance.html', {
        'students': qs,
        'selected_sem': semester,
        'search': search,
    })

@login_required
def departments_view(request):
    """View to list departments with student/faculty counts and add new ones (Admin only)."""
    query = request.GET.get('q')
    
    # Base Queryset with annotations
    departments = Department.objects.annotate(
        student_count=Count('students', distinct=True),
        faculty_count=Count('faculty_members', distinct=True)
    ).order_by('code')
    
    if query:
        departments = departments.filter(Q(name__icontains=query) | Q(code__icontains=query))
        
    # Handle Add Department (Admin Only)
    user_role = (request.user.role or "").lower()
    is_admin = request.user.is_superuser or user_role == User.Role.ADMIN
    
    if request.method == "POST":
        if not is_admin:
            messages.error(request, "Only Administrators can add departments.")
        else:
            name = request.POST.get("name")
            code = request.POST.get("code").upper()
            description = request.POST.get("description", "")
            
            if name and code:
                try:
                    Department.objects.create(name=name, code=code, description=description)
                    messages.success(request, f"Department {code} added successfully.")
                    return redirect('departments')
                except Exception as e:
                    messages.error(request, f"Error adding department: {str(e)}")
            else:
                messages.error(request, "Name and Code are required.")

    return render(request, 'departments.html', {
        'departments': departments,
        'query': query,
        'is_admin': is_admin
    })



# Marks and Results views removed as per refactor.

@login_required
def student_report_pdf(request, student_id):
    # Determine the semester from query params or student's current semester
    semester_param = request.GET.get("semester")
    
    # Safe fetch target student
    student = Student.objects.filter(id=student_id).first()
    if not student:
        return HttpResponse("Student not found.", status=404)

    # RBAC Checks (Case-insensitive)
    is_authorized = False
    u_role = (request.user.role or "").lower()
    
    if u_role == User.Role.ADMIN or request.user.is_superuser:
        is_authorized = True
    elif u_role == User.Role.FACULTY:
        faculty = Faculty.objects.filter(user=request.user).first()
        if faculty and faculty.department == student.department:
            is_authorized = True
    elif u_role == User.Role.STUDENT:
        if hasattr(request.user, 'student_profile') and request.user.student_profile.id == student.id:
            is_authorized = True

    if not is_authorized:
        return HttpResponseForbidden("Unauthorized access")

    try:
        if not semester_param:
            semester = student.semester
        else:
            semester = int(semester_param)
    except (ValueError):
        return HttpResponse("Invalid semester.", status=400)

    builder = ReportCardBuilder(student.id, semester)
    success = builder.fetch_data()

    if not success:
        return HttpResponse("No marks found for this student in the specified semester.", status=404)

    pdf_buffer = builder.build_pdf()
    pdf_buffer.seek(0)
    
    filename = f"report_card_{student.usn}_{semester}.pdf"
    response = FileResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def department_detail(request, id):
    """Detailed analytics dashboard for a specific department."""
    dept = get_object_or_404(Department, id=id)
    
    # Basic Counts
    students = Student.objects.filter(department=dept, is_active=True)
    faculty = Faculty.objects.filter(department=dept, is_active=True)
    
    total_students = students.count()
    total_faculty = faculty.count()
    
    # Attendance Percentage (Overall for Dept)
    total_attendance = Attendance.objects.filter(student__in=students)
    present_count = total_attendance.filter(status='present').count()
    total_count = total_attendance.count()
    
    attendance_percentage = 0
    if total_count > 0:
        attendance_percentage = round((present_count / total_count) * 100, 1)
        
    # Academic Performance (Avg SGPA/CGPA)
    results = Result.objects.filter(student__department=dept)
    perf_stats = results.aggregate(avg_sgpa=Avg('sgpa'), avg_cgpa=Avg('cgpa'))
    
    avg_sgpa = round(perf_stats['avg_sgpa'] or 0, 2)
    avg_cgpa = round(perf_stats['avg_cgpa'] or 0, 2)
    
    context = {
        "dept": dept,
        "total_students": total_students,
        "total_faculty": total_faculty,
        "attendance_percentage": attendance_percentage,
        "avg_sgpa": avg_sgpa,
        "avg_cgpa": avg_cgpa,
        "students_list": students.select_related('user').order_by('usn')
    }
    
    return render(request, "department_detail.html", context)
@login_required
def attendance_pdf_report(request):
    """Generates a consolidated attendance PDF report for the current filter/view."""
    user_role = (request.user.role or "").lower()
    
    # Base Queryset (Reuse logic from attendance_view)
    qs = Attendance.objects.select_related("student__user", "subject")
    
    # RBAC Privacy
    if request.user.is_superuser or user_role == User.Role.ADMIN:
        pass
    elif user_role == User.Role.FACULTY:
        faculty = Faculty.objects.filter(user=request.user).first()
        if faculty:
            qs = qs.filter(student__department=faculty.department)
        else:
            qs = Attendance.objects.none()
    else:
        return HttpResponseForbidden("Unauthorized to generate consolidated reports")

    # Aggregated Stats
    attendance_stats = qs.values(
        'student__user__first_name', 
        'student__user__last_name', 
        'student__user__username',
        'student__usn', 
        'subject__name', 
        'subject__code',
    ).annotate(
        total_classes=Count('id'),
        present_count=Count('id', filter=Q(status='present'))
    ).order_by('student__usn', 'subject__code')

    # Format data for builder
    formatted_data = []
    for stat in attendance_stats:
        total = stat['total_classes']
        present = stat['present_count']
        percentage = round((present / total * 100), 1) if total > 0 else 0
        
        formatted_data.append({
            'name': f"{stat['student__user__first_name']} {stat['student__user__last_name']}",
            'usn': stat['student__usn'],
            'subject': stat['subject__name'],
            'total': total,
            'present': present,
            'percentage': percentage
        })

    builder = AttendanceReportBuilder(formatted_data)
    pdf_buffer = builder.build_pdf()
    
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'
    return response

import json

@login_required
def student_attendance_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    # Query all attendance records for this student
    qs = Attendance.objects.filter(student=student).select_related('subject')
    
    # Group by semester
    attendance_stats = qs.values(
        'subject__semester',
        'subject__code',
        'subject__name'
    ).annotate(
        total_classes=Count('id'),
        present_count=Count('id', filter=Q(status='present'))
    ).order_by('-subject__semester', 'subject__code')
    
    # Process for template and charts
    table_data = []
    
    # Chart Data
    bar_labels = []
    bar_data = []
    
    pie_present = 0
    pie_absent = 0
    
    # Line chart: semester-wise trend
    sem_data = {}
    
    for stat in attendance_stats:
        total = stat['total_classes']
        present = stat['present_count']
        absent = total - present
        percentage = round((present / total * 100), 2) if total > 0 else 0
        
        sem = stat['subject__semester']
        
        table_data.append({
            'semester': sem,
            'subject_code': stat['subject__code'],
            'subject_name': stat['subject__name'],
            'total_classes': total,
            'present': present,
            'percentage': percentage
        })
        
        bar_labels.append(stat['subject__code'])
        bar_data.append(percentage)
        
        pie_present += present
        pie_absent += absent
        
        if sem not in sem_data:
            sem_data[sem] = {'total': 0, 'present': 0}
        sem_data[sem]['total'] += total
        sem_data[sem]['present'] += present
        
    line_labels = sorted(list(sem_data.keys()))
    line_data = [
        round((sem_data[s]['present'] / sem_data[s]['total'] * 100), 2) if sem_data[s]['total'] > 0 else 0
        for s in line_labels
    ]
    
    context = {
        'student': student,
        'table_data': table_data,
        'chart_data': json.dumps({
            'bar_labels': bar_labels,
            'bar_data': bar_data,
            'pie_data': [pie_present, pie_absent],
            'line_labels': [f'Sem {s}' for s in line_labels],
            'line_data': line_data
        })
    }
    
    return render(request, 'student_detail.html', context)

