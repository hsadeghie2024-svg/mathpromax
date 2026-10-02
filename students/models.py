from django.db import models
from django.contrib.auth.models import User


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    grade = models.CharField(
        max_length=30
    )

    track = models.CharField(
        max_length=50,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    # کد OTP به صورت هش‌شده ذخیره می‌شود
    # بنابراین طول آن باید بیشتر از ۶ کاراکتر باشد.
    code = models.CharField(
        max_length=128
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    expires_at = models.DateTimeField()

    is_used = models.BooleanField(
        default=False
    )

    attempts = models.PositiveIntegerField(
        default=0
    )

    def __str__(self):
        return f"OTP - {self.user.username}"


class ExamResult(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    score = models.PositiveIntegerField()

    total = models.PositiveIntegerField(
        default=20
    )

    skill_results = models.JSONField(
        default=dict
    )

    learning_plan = models.TextField(
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.score}/{self.total}"


class Question(models.Model):

    grade = models.CharField(
        max_length=30
    )

    track = models.CharField(
        max_length=50,
        blank=True
    )

    subject = models.CharField(
        max_length=100
    )

    topic = models.CharField(
        max_length=100
    )

    subtopic = models.CharField(
        max_length=100,
        blank=True
    )

    DIFFICULTY_CHOICES = [
        ('beginner', 'مبتدی'),
        ('medium', 'متوسط'),
        ('good', 'خوب'),
        ('advanced', 'پیشرفته'),
        ('professional', 'حرفه‌ای'),
        ('tizhooshan', 'تیزهوشان'),
    ]

    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner'
    )

    question_text = models.TextField()

    option_a = models.CharField(
        max_length=500
    )

    option_b = models.CharField(
        max_length=500
    )

    option_c = models.CharField(
        max_length=500
    )

    option_d = models.CharField(
        max_length=500
    )

    ANSWER_CHOICES = [
        ('a', 'گزینه الف'),
        ('b', 'گزینه ب'),
        ('c', 'گزینه ج'),
        ('d', 'گزینه د'),
    ]

    correct_answer = models.CharField(
        max_length=1,
        choices=ANSWER_CHOICES
    )

    explanation = models.TextField(
        blank=True
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.grade} - {self.subject} - {self.topic}"

class LessonProgress(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    topic = models.CharField(
        max_length=100
    )

    best_score = models.PositiveIntegerField(
        default=0
    )

    last_score = models.PositiveIntegerField(
        default=0
    )

    attempts = models.PositiveIntegerField(
        default=0
    )

    completed = models.BooleanField(
        default=False
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = ('user', 'topic')

    def __str__(self):
        return f"{self.user.username} - {self.topic} - {self.best_score}%"


class ExerciseResult(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    topic = models.CharField(
        max_length=100
    )

    total_questions = models.PositiveIntegerField(
        default=0
    )

    correct_answers = models.PositiveIntegerField(
        default=0
    )

    wrong_answers = models.PositiveIntegerField(
        default=0
    )

    score = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.topic} - "
            f"{self.score}%"
        )