"""
students/models.py
Student profile and Enrollment (Student ↔ Subject many-to-many through table).
"""

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Student(models.Model):
    """
    Profile for a user with role='student'.
    - Linked 1-to-1 with accounts.User
    - Belongs to one Department (FK)
    - Enrolled in many Subjects via Enrollment
    - Has many Attendance records
    - Has many Marks records
    - Has many Result records
    """

    SECTION_CHOICES = [(s, s) for s in "ABCDEF"]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    usn = models.CharField(
        max_length=20,
        unique=True,
        help_text="University Seat Number, e.g. 1RV21CS001",
    )
    department = models.ForeignKey(
        "academics.Department",
        on_delete=models.PROTECT,
        related_name="students",
    )
    semester = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        db_index=True,
    )
    section = models.CharField(max_length=1, choices=SECTION_CHOICES, default="A")
    date_of_birth = models.DateField(null=True, blank=True)
    admission_year = models.PositiveSmallIntegerField(null=True, blank=True)
    attendance_percentage = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["usn"]
        verbose_name = "Student"
        verbose_name_plural = "Students"
        indexes = [
            models.Index(fields=["department", "semester", "section"]),
        ]

    def __str__(self):
        return f"{self.usn} – {self.user.get_full_name() or self.user.username}"

    def update_attendance_percentage(self):
        """Calculates and saves the overall attendance percentage."""
        total = self.attendance_records.count()
        if total > 0:
            present = self.attendance_records.filter(status='present').count()
            self.attendance_percentage = round((present / total) * 100, 2)
        else:
            self.attendance_percentage = 0
        self.save(update_fields=['attendance_percentage'])


class Enrollment(models.Model):
    """
    Explicit many-to-many between Student and Subject.
    Tracks which student is enrolled in which subject for a given academic year.
    """

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    academic_year = models.CharField(
        max_length=9,
        help_text="e.g. 2025-2026",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "subject", "academic_year")
        ordering = ["student", "subject"]
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.student.usn} → {self.subject.code} ({self.academic_year})"
