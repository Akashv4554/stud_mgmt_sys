"""
exams/models.py
Exam, Marks and Result models.
Supports internal (CIA 1, CIA 2, CIA 3) and external (semester) exams.
Result stores computed SGPA and CGPA per student per semester.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Exam(models.Model):
    """
    Defines an examination event.
    Examples: "Internal 1 – Sem 5", "Semester Exam – Sem 5".
    """

    class ExamType(models.TextChoices):
        INTERNAL = "internal", "Internal"
        EXTERNAL = "external", "External"

    name = models.CharField(max_length=100)  # e.g. "Internal Assessment 1"
    exam_type = models.CharField(
        max_length=8,
        choices=ExamType.choices,
        default=ExamType.INTERNAL,
    )
    semester = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)],
    )
    academic_year = models.CharField(max_length=9, help_text="e.g. 2025-2026")
    max_marks = models.PositiveSmallIntegerField(default=40)
    date_conducted = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["semester", "exam_type", "name"]
        verbose_name = "Exam"
        verbose_name_plural = "Exams"

    def __str__(self):
        return f"{self.name} ({self.get_exam_type_display()}, Sem {self.semester})"


class Marks(models.Model):
    """
    Stores a single student's marks for a specific subject in a specific exam.
    - FK to Student, Subject, Exam
    """

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="marks",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="marks",
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="marks",
    )
    marks_obtained = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_absent = models.BooleanField(default=False)
    remarks = models.CharField(max_length=200, blank=True, default="")
    entered_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marks_entered",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "subject", "exam")
        ordering = ["student", "subject", "exam"]
        verbose_name = "Marks Entry"
        verbose_name_plural = "Marks Entries"
        indexes = [
            models.Index(fields=["student", "exam"]),
        ]

    def __str__(self):
        return (
            f"{self.student.usn} | {self.subject.code} | "
            f"{self.exam.name}: {self.marks_obtained}"
        )


class Result(models.Model):
    """
    Computed SGPA and CGPA for a student for a specific semester.
    Typically calculated after all marks are finalized.
    """

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="results",
    )
    semester = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(8)],
    )
    academic_year = models.CharField(max_length=9)
    sgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True,
        blank=True,
    )
    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True,
        blank=True,
    )
    total_credits = models.PositiveSmallIntegerField(default=0)
    credits_earned = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "semester", "academic_year")
        ordering = ["student", "semester"]
        verbose_name = "Result"
        verbose_name_plural = "Results"

    def __str__(self):
        return f"{self.student.usn} | Sem {self.semester} – SGPA: {self.sgpa}"
