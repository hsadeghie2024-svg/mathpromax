from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile


class StudentRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='نام کاربری'
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        label='رمز عبور'
    )

    phone = forms.CharField(
        max_length=20,
        label='شماره موبایل'
    )

    grade = forms.CharField(
        max_length=30,
        label='پایه تحصیلی'
    )

    track = forms.CharField(
        max_length=50,
        required=False,
        label='رشته'
    )

    city = forms.CharField(
        max_length=100,
        label='شهر'
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'این نام کاربری قبلاً ثبت شده است. لطفاً نام کاربری دیگری انتخاب کنید.'
            )

        return username

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


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'phone',
            'grade',
            'track',
            'city'
        ]