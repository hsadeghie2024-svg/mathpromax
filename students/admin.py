from django.contrib import admin
from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'grade', 'track', 'city', 'created_at')
    search_fields = ('user__username', 'phone', 'city')
    list_filter = ('grade', 'track')
