from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from datetime import timedelta
import random

from .forms import StudentRegistrationForm, StudentProfileForm
from .models import (
ExamResult,
Question,
PasswordResetOTP,
StudentProfile,
)

def home(request):
    return render(request, 'students/home.html')

def register_student(request):
    if request.method == 'POST':
form = StudentRegistrationForm(request.POST)


    if form.is_valid():
        try:
            with transaction.atomic():
                form.save()

            return redirect('register_success')

        except IntegrityError:
            form.add_error(
                'username',
                'این نام کاربری قبلاً ثبت شده است. لطفاً نام کاربری دیگری انتخاب کنید.'
            )

    else:
    form = StudentRegistrationForm()

    return render(
    request,
    'students/register.html',
    {
        'form': form
    }
)


def register_success(request):
    return render(request, 'students/success.html')

def student_login(request):
    if request.method == 'POST':
username = request.POST.get(
'username',
''
).strip()


    password = request.POST.get(
        'password',
        ''
    )

    user = authenticate(
        request,
        username=username,
        password=password
    )

    if user is not None:
        login(request, user)
        return redirect('student_dashboard')

    return render(
        request,
        'students/login.html',
        {
            'error': 'نام کاربری یا رمز عبور اشتباه است.'
        }
    )

    return render(
    request,
    'students/login.html'
)


# ==========================================================

# بازیابی رمز عبور با شماره موبایل و OTP

# ==========================================================

def password_reset_request(request):
    if request.method == 'POST':
phone = request.POST.get(
'phone',
''
).strip()


    if not phone:
        return render(
            request,
            'students/password_reset_request.html',
            {
                'error': 'لطفاً شماره موبایل خود را وارد کنید.'
            }
        )

    try:
        student_profile = (
            StudentProfile.objects
            .filter(phone=phone)
            .select_related('user')
            .first()
        )

        if student_profile:
            user = student_profile.user

            PasswordResetOTP.objects.filter(
                user=user,
                is_used=False
            ).update(
                is_used=True
            )

            code = str(
                random.randint(
                    100000,
                    999999
                )
            )

            expires_at = (
                timezone.now()
                + timedelta(minutes=5)
            )

            PasswordResetOTP.objects.create(
                user=user,
                code=make_password(code),
                expires_at=expires_at
            )

            request.session[
                'password_reset_user_id'
            ] = user.id

            if settings.DEBUG:
                request.session[
                    'password_reset_debug_code'
                ] = code

            return redirect(
                'password_reset_verify'
            )

    except Exception:
        pass

    return render(
        request,
        'students/password_reset_request.html',
        {
            'success': (
                'اگر این شماره موبایل در AIZAVA ثبت شده باشد، '
                'کد تأیید برای آن ارسال خواهد شد.'
            )
        }
    )

    return render(
    request,
    'students/password_reset_request.html'
)


def password_reset_verify(request):
user_id = request.session.get(
'password_reset_user_id'
)


    if not user_id:
    return redirect(
        'password_reset_request'
    )

try:
    user = User.objects.get(
        id=user_id
    )

except User.DoesNotExist:
    request.session.pop(
        'password_reset_user_id',
        None
    )

    request.session.pop(
        'password_reset_verified',
        None
    )

    request.session.pop(
        'password_reset_debug_code',
        None
    )

    return redirect(
        'password_reset_request'
    )

otp = PasswordResetOTP.objects.filter(
    user=user,
    is_used=False
).order_by(
    '-created_at'
).first()

    if not otp:
    return redirect(
        'password_reset_request'
    )

debug_code = None

    if settings.DEBUG:
    debug_code = request.session.get(
        'password_reset_debug_code'
    )

# ------------------------------------------------------
# بررسی انقضای کد
# ------------------------------------------------------

    if timezone.now() > otp.expires_at:
    otp.is_used = True

    otp.save(
        update_fields=['is_used']
    )

    request.session.pop(
        'password_reset_user_id',
        None
    )

    request.session.pop(
        'password_reset_verified',
        None
    )

    request.session.pop(
        'password_reset_debug_code',
        None
    )

    context = {
        'error': (
            'کد تأیید منقضی شده است. '
            'لطفاً دوباره درخواست کد کنید.'
        )
    }

    if settings.DEBUG:
        context['debug_code'] = debug_code

    return render(
        request,
        'students/password_reset_verify.html',
        context
    )

# ------------------------------------------------------
# بررسی کد واردشده
# ------------------------------------------------------

    if request.method == 'POST':
    code = request.POST.get(
        'code',
        ''
    ).strip()

    if not code:
        context = {
            'error': 'لطفاً کد تأیید را وارد کنید.'
        }

        if settings.DEBUG:
            context['debug_code'] = debug_code

        return render(
            request,
            'students/password_reset_verify.html',
            context
        )

    # حداکثر ۵ تلاش
    if otp.attempts >= 5:
        otp.is_used = True

        otp.save(
            update_fields=['is_used']
        )

        request.session.pop(
            'password_reset_user_id',
            None
        )

        request.session.pop(
            'password_reset_verified',
            None
        )

        request.session.pop(
            'password_reset_debug_code',
            None
        )

        context = {
            'error': (
                'تعداد تلاش‌های مجاز به پایان رسیده است. '
                'لطفاً دوباره درخواست کد کنید.'
            )
        }

        if settings.DEBUG:
            context['debug_code'] = debug_code

        return render(
            request,
            'students/password_reset_verify.html',
            context
        )

    otp.attempts += 1

    otp.save(
        update_fields=['attempts']
    )

    if check_password(
        code,
        otp.code
    ):
        otp.is_used = True

        otp.save(
            update_fields=['is_used']
        )

        request.session[
            'password_reset_verified'
        ] = True

        return redirect(
            'password_reset_new_password'
        )

    context = {
        'error': 'کد تأیید اشتباه است.'
    }

    if settings.DEBUG:
        context['debug_code'] = debug_code

    return render(
        request,
        'students/password_reset_verify.html',
        context
    )

context = {}

    if settings.DEBUG:
    context['debug_code'] = debug_code

    return render(
    request,
    'students/password_reset_verify.html',
    context
)


def password_reset_new_password(request):
user_id = request.session.get(
'password_reset_user_id'
)


verified = request.session.get(
    'password_reset_verified'
)

    if not user_id or not verified:
    return redirect(
        'password_reset_request'
    )

try:
    user = User.objects.get(
        id=user_id
    )

except User.DoesNotExist:
    request.session.pop(
        'password_reset_user_id',
        None
    )

    request.session.pop(
        'password_reset_verified',
        None
    )

    request.session.pop(
        'password_reset_debug_code',
        None
    )

    return redirect(
        'password_reset_request'
    )

    if request.method == 'POST':
    password1 = request.POST.get(
        'password1',
        ''
    )

    password2 = request.POST.get(
        'password2',
        ''
    )

    if not password1 or not password2:
        return render(
            request,
            'students/password_reset_new_password.html',
            {
                'error': (
                    'لطفاً هر دو فیلد رمز عبور را وارد کنید.'
                )
            }
        )

    if password1 != password2:
        return render(
            request,
            'students/password_reset_new_password.html',
            {
                'error': (
                    'دو رمز عبور واردشده یکسان نیستند.'
                )
            }
        )

    if len(password1) < 8:
        return render(
            request,
            'students/password_reset_new_password.html',
            {
                'error': (
                    'رمز عبور باید حداقل ۸ کاراکتر باشد.'
                )
            }
        )

    user.set_password(password1)

    user.save(
        update_fields=['password']
    )

    user.refresh_from_db()

    if not user.check_password(
        password1
    ):
        return render(
            request,
            'students/password_reset_new_password.html',
            {
                'error': (
                    'ذخیره رمز عبور با مشکل مواجه شد. '
                    'لطفاً دوباره تلاش کنید.'
                )
            }
        )

    request.session.pop(
        'password_reset_user_id',
        None
    )

    request.session.pop(
        'password_reset_verified',
        None
    )

    request.session.pop(
        'password_reset_debug_code',
        None
    )

    return redirect(
        'student_login'
    )

    return render(
    request,
    'students/password_reset_new_password.html'
)


# ==========================================================

# داشبورد

# ==========================================================

@login_required(login_url='/students/login/')
def student_dashboard(request):
profile = request.user.studentprofile


    return render(
    request,
    'students/dashboard.html',
    {
        'profile': profile,
    }
)


# ==========================================================

# آزمون

# ==========================================================

@login_required(login_url='/students/login/')
def start_test(request):
questions = list(
Question.objects.filter(
active=True
).order_by('id')
)


    if request.method == 'POST':
    score = 0
    skill_results = {}

    learning_recommendations = {
        'اعداد': [
            'مرور مفهوم اعداد',
            'تمرین محاسبات عددی',
            'حل ۱۰ تمرین پایه'
        ],
        'کسرها': [
            'مرور مفهوم کسر',
            'تمرین جمع و تفریق کسرها',
            'حل ۱۰ تمرین کسر'
        ],
        'توان': [
            'مرور مفهوم توان',
            'تمرین توان‌های ساده',
            'حل ۱۰ تمرین توان'
        ],
        'هندسه': [
            'مرور مفاهیم هندسه',
            'تمرین محیط و اشکال هندسی',
            'حل ۱۰ تمرین هندسه'
        ],
        'جمع و تفریق': [
            'مرور جمع و تفریق',
            'تمرین محاسبات دقیق',
            'حل ۱۰ تمرین'
        ],
        'ضرب و تقسیم': [
            'مرور ضرب و تقسیم',
            'تمرین محاسبات',
            'حل ۱۰ تمرین'
        ],
    }

    for question in questions:
        student_answer = request.POST.get(
            f'q{question.id}'
        )

        topic = question.topic or 'سایر'

        if topic not in skill_results:
            skill_results[topic] = {
                'correct': 0,
                'total': 0,
            }

        skill_results[topic]['total'] += 1

        if student_answer == question.correct_answer:
            score += 1
            skill_results[topic]['correct'] += 1

    for topic, data in skill_results.items():
        total = data['total']
        correct = data['correct']

        if total > 0:
            percentage = round(
                (correct / total) * 100
            )
        else:
            percentage = 0

        if percentage >= 85:
            level = '🌟 عالی'
        elif percentage >= 70:
            level = '🟢 خوب'
        elif percentage >= 50:
            level = '🟡 متوسط'
        elif percentage >= 30:
            level = '🟠 نیاز به تمرین'
        else:
            level = '🔴 شروع از پایه'

        data['percentage'] = percentage
        data['level'] = level

    weak_skills = []

    for skill, data in skill_results.items():
        if data['percentage'] < 50:
            weak_skills.append(skill)

    weak_skills.sort(
        key=lambda skill:
        skill_results[skill]['percentage']
    )

    learning_plan_lines = [
        '🚀 مسیر یادگیری پیشنهادی AIZAVA',
        '',
        f'📊 نمره کل: {score} از {len(questions)}',
        ''
    ]

    if weak_skills:
        learning_plan_lines.append(
            '🎯 اولویت‌های یادگیری شما:'
        )

        learning_plan_lines.append('')

        priority_skills = weak_skills[:3]

        for index, skill in enumerate(
            priority_skills,
            start=1
        ):
            data = skill_results[skill]

            learning_plan_lines.append(
                f'🔴 اولویت {index}: {skill}'
            )

            learning_plan_lines.append(
                f'درصد عملکرد: {data["percentage"]}%'
            )

            learning_plan_lines.append(
                f'سطح فعلی: {data["level"]}'
            )

            learning_plan_lines.append(
                'برنامه پیشنهادی:'
            )

            recommendations = (
                learning_recommendations.get(
                    skill,
                    [
                        'مرور این مبحث',
                        'حل تمرین بیشتر',
                        'شرکت در آزمون مجدد'
                    ]
                )
            )

            for step_number, recommendation in enumerate(
                recommendations,
                start=1
            ):
                learning_plan_lines.append(
                    f'   {step_number}. {recommendation}'
                )

            learning_plan_lines.append('')

        learning_plan_lines.append(
            '💡 پیشنهاد AIZAVA: ابتدا روی ضعیف‌ترین مبحث '
            'تمرکز کنید و سپس به سراغ مباحث بعدی بروید.'
        )

    else:
        learning_plan_lines.extend([
            '🌟 عملکرد شما در همه مباحث آزمون مناسب است.',
            '',
            'برای پیشرفت بیشتر:',
            '1. تمرین‌های سطح متوسط و پیشرفته انجام دهید.',
            '2. سرعت و دقت خود را افزایش دهید.',
            '3. در آزمون‌های بعدی نیز شرکت کنید.'
        ])

    learning_plan = '\n'.join(
        learning_plan_lines
    )

    ExamResult.objects.create(
        user=request.user,
        score=score,
        total=len(questions),
        skill_results=skill_results,
        learning_plan=learning_plan,
    )

    return render(
        request,
        'students/result.html',
        {
            'score': score,
            'total': len(questions),
            'skill_results': skill_results,
            'learning_plan': learning_plan,
        }
    )

    return render(
    request,
    'students/test.html',
    {
        'questions': questions,
    }
)


# ==========================================================

# خروج

# ==========================================================

def student_logout(request):
logout(request)


    return redirect(
    'student_login'
)


# ==========================================================

# پروفایل

# ==========================================================

@login_required(login_url='/students/login/')
def student_profile(request):
profile = request.user.studentprofile


    return render(
    request,
    'students/profile.html',
    {
        'profile': profile,
    }
)


@login_required(login_url='/students/login/')
def edit_profile(request):
profile = request.user.studentprofile


    if request.method == 'POST':
    form = StudentProfileForm(
        request.POST,
        instance=profile
    )

    if form.is_valid():
        form.save()

        return redirect(
            'student_profile'
        )

    else:
    form = StudentProfileForm(
        instance=profile
    )

    return render(
    request,
    'students/edit_profile.html',
    {
        'form': form,
    }
)


@login_required(login_url='/students/login/')
def change_password(request):
    if request.method == 'POST':
form = PasswordChangeForm(
request.user,
request.POST
)


    if form.is_valid():
        user = form.save()

        update_session_auth_hash(
            request,
            user
        )

        return redirect(
            'student_profile'
        )

    else:
    form = PasswordChangeForm(
        request.user
    )

    return render(
    request,
    'students/change_password.html',
    {
        'form': form,
    }
)


# ==========================================================

# سابقه آزمون

# ==========================================================

@login_required(login_url='/students/login/')
def exam_history(request):
results = ExamResult.objects.filter(
user=request.user
).order_by(
'-created_at'
)


    return render(
    request,
    'students/exam_history.html',
    {
        'results': results,
    }
)


@login_required(login_url='/students/login/')
def exam_detail(request, id):
result = get_object_or_404(
ExamResult,
id=id,
user=request.user
)


    return render(
    request,
    'students/exam_detail.html',
    {
        'result': result,
    }
)

