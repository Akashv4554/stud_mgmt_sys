"""
academics/models.py
Department and Subject models.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Department(models.Model):
    """
    Represents an engineering department (e.g., CSE, ECE, MECH).
    - Has many Students (Student.department → Department)
    - Has many Faculty  (Faculty.department → Department)
    - Has many Subjects (Subject.department → Department)
    """

    name = models.CharField(max_length=100, unique=True)  # e.g. "Computer Science and Engineering"
    code = models.CharField(max_length=20, unique=True)    # e.g. "CSE"
    description = models.TextField(blank=True, default="")
    hod_name = models.CharField(max_length=100, blank=True, default="")  # Head of Department
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return f"{self.code} – {self.name}"


class Subject(models.Model):
    """
    Represents a course/subject for a specific semester within a department.
    - Belongs to one Department (FK)
    - Many-to-Many with Students through the Enrollment model (students app)
    - Referenced by Attendance and Marks records
    """

    class SubjectType(models.TextChoices):
        THEORY = "theory", "Theory"
        LAB = "lab", "Lab"

    code = models.CharField(max_length=30, unique=True)        # e.g. "21CS51"
    name = models.CharField(max_length=150)                     # e.g. "Operating Systems"
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="subjects",
    )
    semester = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        db_index=True,
    )
    credits = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(6)],
    )
    subject_type = models.CharField(
        max_length=6,
        choices=SubjectType.choices,
        default=SubjectType.THEORY,
    )
    max_internal_marks = models.PositiveSmallIntegerField(default=40)
    max_external_marks = models.PositiveSmallIntegerField(default=60)
    is_elective = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["department", "semester", "code"]
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        indexes = [
            models.Index(fields=["department", "semester"]),
        ]

    def __str__(self):
        return f"{self.code} – {self.name} (Sem {self.semester})"
