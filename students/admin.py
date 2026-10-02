from django.contrib import admin
from .models import StudentProfile, Question


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'grade', 'track', 'city', 'created_at')
    search_fields = ('user__username', 'phone', 'city')
    list_filter = ('grade', 'track')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'grade',
        'track',
        'subject',
        'topic',
        'difficulty',
        'active',
        'created_at',
    )

    search_fields = (
        'question_text',
        'subject',
        'topic',
        'subtopic',
    )

    list_filter = (
        'grade',
        'track',
        'subject',
        'difficulty',
        'active',
    )

    ordering = ('grade', 'subject', 'topic', 'difficulty')