from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile


class StudentRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    phone = forms.CharField(max_length=20)
    grade = forms.CharField(max_length=30)
    track = forms.CharField(max_length=50, required=False)
    city = forms.CharField(max_length=100)

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )

        student = StudentProfile.objects.create(
            user=user,
            phone=self.cleaned_data['phone'],
            grade=self.cleaned_data['grade'],
            track=self.cleaned_data['track'],
            city=self.cleaned_data['city']
        )

        return student
