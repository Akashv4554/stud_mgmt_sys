import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from accounts.models import User
from academics.models import Department, Subject
from students.models import Student, Enrollment
from faculty.models import Faculty
from attendance.models import Attendance
from exams.models import Exam, Marks, Result

class Command(BaseCommand):
    help = "Clear all existing data and insert clean, realistic demo data."

    def handle(self, *args, **options):
        self.stdout.write("Starting data reset and seeding...")

        with transaction.atomic():
            # 1. Clear Data
            self.stdout.write("Deleting existing data...")
            Marks.objects.all().delete()
            Result.objects.all().delete()
            Exam.objects.all().delete()
            Attendance.objects.all().delete()
            Enrollment.objects.all().delete()
            Student.objects.all().delete()
            Faculty.objects.all().delete()
            Subject.objects.all().delete()
            Department.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

            # 2. Seed Departments
            self.stdout.write("Seeding Departments...")
            cse = Department.objects.create(name="Computer Science and Engineering", code="CSE", description="Department of CSE")
            ece = Department.objects.create(name="Electronics and Communication Engineering", code="ECE", description="Department of ECE")
            depts = [cse, ece]

            # 3. Seed Faculty
            self.stdout.write("Seeding Faculty...")
            faculty_data = [
                ("dr_smith", "Dr. Jane Smith", "jane.smith@college.edu", cse, "Professor"),
                ("prof_kumar", "Prof. Naveen Kumar", "naveen.kumar@college.edu", ece, "Associate Professor"),
                ("mr_verma", "Mr. Amit Verma", "amit.verma@college.edu", cse, "Assistant Professor"),
            ]
            faculty_objs = []
            for username, name, email, dept, desig in faculty_data:
                user = User.objects.create_user(username=username, email=email, password="password123", role=User.Role.FACULTY)
                user.first_name = name.split()[0]
                user.last_name = " ".join(name.split()[1:])
                user.save()
                f = Faculty.objects.create(user=user, employee_id=f"EMP{random.randint(100, 999)}", department=dept, designation=desig)
                faculty_objs.append(f)

            # 4. Seed Subjects (Sem 3 and 5)
            self.stdout.write("Seeding Subjects...")
            subjects_list = [
                (cse, 3, "21CS31", "Data Structures", 4),
                (cse, 3, "21CS32", "Object Oriented Programming", 3),
                (cse, 3, "21CS33", "Digital Design", 3),
                (cse, 3, "21CS34", "Computer Organization", 4),
                (cse, 5, "21CS51", "Operating Systems", 4),
                (cse, 5, "21CS52", "Computer Networks", 4),
                (cse, 5, "21CS53", "Database Management", 4),
                (cse, 5, "21CS54", "Theory of Computation", 3),
                (ece, 3, "21EC31", "Network Analysis", 4),
                (ece, 3, "21EC32", "Analog Electronics", 3),
                (ece, 5, "21EC51", "Digital Signal Processing", 4),
                (ece, 5, "21EC52", "Microcontrollers", 4),
            ]
            sub_objs = []
            for dept, sem, code, name, credits in subjects_list:
                s = Subject.objects.create(department=dept, semester=sem, code=code, name=name, credits=credits)
                sub_objs.append(s)

            # 5. Seed Students
            self.stdout.write("Seeding Students...")
            student_data = [
                ("1RV23CS001", "Akash Sharma", "akash@gmail.com", cse, 3, "A"),
                ("1RV23CS045", "Bhavana Reddy", "bhavana@gmail.com", cse, 3, "A"),
                ("1RV21CS005", "Chetan Kumar", "chetan@gmail.com", cse, 5, "B"),
                ("1RV23EC012", "Deepika Padukone", "deepika@gmail.com", ece, 3, "A"),
                ("1RV21EC088", "Eshwar Prasad", "eshwar@gmail.com", ece, 5, "A"),
            ]
            student_objs = []
            for usn, name, email, dept, sem, sec in student_data:
                uname = usn.lower()
                user = User.objects.create_user(username=uname, email=email, password="password123", role=User.Role.STUDENT)
                user.first_name = name.split()[0]
                user.last_name = " ".join(name.split()[1:])
                user.save()
                s = Student.objects.create(user=user, usn=usn, department=dept, semester=sem, section=sec, admission_year=2021 if sem==5 else 2023)
                student_objs.append(s)

            # 6. Enrollments, Attendance & Exams
            self.stdout.write("Seeding Enrollments and Attendance...")
            academic_year = "2025-2026"
            
            # Create Exams
            ia1 = Exam.objects.create(name="Internal Assessment 1", exam_type=Exam.ExamType.INTERNAL, semester=3, academic_year=academic_year, max_marks=40)
            ia1_sem5 = Exam.objects.create(name="Internal Assessment 1", exam_type=Exam.ExamType.INTERNAL, semester=5, academic_year=academic_year, max_marks=40)
            external = Exam.objects.create(name="Semester End Exam", exam_type=Exam.ExamType.EXTERNAL, semester=3, academic_year=academic_year, max_marks=60)
            external_sem5 = Exam.objects.create(name="Semester End Exam", exam_type=Exam.ExamType.EXTERNAL, semester=5, academic_year=academic_year, max_marks=60)

            for s in student_objs:
                relevant_subs = [sub for sub in sub_objs if sub.department == s.department and sub.semester == s.semester]
                
                total_weighted_points = 0
                total_credits = 0

                for sub in relevant_subs:
                    Enrollment.objects.create(student=s, subject=sub, academic_year=academic_year)
                    
                    # Attendance
                    for i in range(10):
                        Attendance.objects.create(
                            student=s, 
                            subject=sub, 
                            date=date.today() - timedelta(days=i), 
                            period=random.randint(1, 4),
                            status=random.choice([Attendance.Status.PRESENT]*8 + [Attendance.Status.ABSENT])
                        )
                    
                    # Marks
                    exam_int = ia1 if s.semester == 3 else ia1_sem5
                    exam_ext = external if s.semester == 3 else external_sem5
                    
                    m_int = random.randint(25, 38)
                    m_ext = random.randint(35, 55)
                    
                    Marks.objects.create(student=s, subject=sub, exam=exam_int, marks_obtained=m_int)
                    Marks.objects.create(student=s, subject=sub, exam=exam_ext, marks_obtained=m_ext)
                    
                    # SGPA Calculation logic (simplified)
                    # Grade points: 90+=10, 80+=9, 70+=8, 60+=7, 50+=6, 40+=5
                    total = m_int+m_ext # out of 100
                    gp = 10 if total >= 90 else 9 if total >= 80 else 8 if total >= 70 else 7 if total >= 60 else 6 if total >= 50 else 5 if total >= 40 else 0
                    
                    total_weighted_points += (gp * sub.credits)
                    total_credits += sub.credits

                # Result
                sgpa = round(total_weighted_points / total_credits, 2) if total_credits > 0 else 0
                Result.objects.create(
                    student=s, 
                    semester=s.semester, 
                    academic_year=academic_year, 
                    sgpa=sgpa, 
                    total_credits=total_credits, 
                    credits_earned=total_credits,
                    is_published=True
                )

        self.stdout.write(self.style.SUCCESS("Successfully reset and seeded demo data!"))
