from pathlib import Path

code = r'''
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User

from .forms import StudentRegistrationForm, StudentProfileForm
from .models import StudentProfile, ExamResult, Question, PasswordResetOTP


def home(request):
    return render(request, "students/home.html")


def register_student(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            student = form.save()
            login(request, student.user)
            return redirect("register_success")
    else:
        form = StudentRegistrationForm()

    return render(request, "students/register.html", {"form": form})


def register_success(request):
    return render(request, "students/success.html")


def student_login(request):
    if request.user.is_authenticated:
        return redirect("student_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("student_dashboard")

        messages.error(
            request,
            "نام کاربری یا رمز عبور صحیح نیست."
        )

    return render(request, "students/login.html")


@login_required
def student_logout(request):
    logout(request)
    return redirect("home")


def password_reset_request(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user is None:
            messages.error(
                request,
                "کاربری با این نام کاربری پیدا نشد."
            )
            return render(
                request,
                "students/password_reset_request.html"
            )

        request.session["reset_user_id"] = user.id

        return redirect("password_reset_verify")

    return render(
        request,
        "students/password_reset_request.html"
    )


def password_reset_verify(request):
    user_id = request.session.get("reset_user_id")

    if not user_id:
        return redirect("password_reset_request")

    if request.method == "POST":
        code = request.POST.get("code", "").strip()

        otp = (
            PasswordResetOTP.objects
            .filter(
                user_id=user_id,
                code=code,
                is_used=False
            )
            .order_by("-created_at")
            .first()
        )

        if otp and otp.expires_at >= timezone.now():
            request.session["reset_verified"] = True
            return redirect("password_reset_new_password")

        messages.error(
            request,
            "کد واردشده صحیح نیست یا منقضی شده است."
        )

    return render(
        request,
        "students/password_reset_verify.html"
    )


def password_reset_new_password(request):
    user_id = request.session.get("reset_user_id")
    verified = request.session.get("reset_verified", False)

    if not user_id or not verified:
        return redirect("password_reset_request")

    if request.method == "POST":
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if not password1:
            messages.error(
                request,
                "رمز عبور جدید را وارد کنید."
            )

        elif password1 != password2:
            messages.error(
                request,
                "رمزهای عبور یکسان نیستند."
            )

        else:
            user = get_object_or_404(
                User,
                id=user_id
            )

            user.set_password(password1)
            user.save()

            request.session.pop("reset_user_id", None)
            request.session.pop("reset_verified", None)

            messages.success(
                request,
                "رمز عبور با موفقیت تغییر کرد."
            )

            return redirect("student_login")

    return render(
        request,
        "students/password_reset_new_password.html"
    )


@login_required
def student_profile(request):
    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    return render(
        request,
        "students/profile.html",
        {
            "profile": profile,
            "student": profile,
        }
    )


@login_required
def edit_profile(request):
    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = StudentProfileForm(
            request.POST,
            instance=profile
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "اطلاعات پروفایل با موفقیت ذخیره شد."
            )

            return redirect("student_profile")

    else:
        form = StudentProfileForm(
            instance=profile
        )

    return render(
        request,
        "students/profile_edit.html",
        {
            "form": form,
            "profile": profile,
        }
    )


@login_required
def change_password(request):
    if request.method == "POST":
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

            messages.success(
                request,
                "رمز عبور با موفقیت تغییر کرد."
            )

            return redirect("student_profile")

    else:
        form = PasswordChangeForm(
            request.user
        )

    return render(
        request,
        "students/change_password.html",
        {
            "form": form
        }
    )


@login_required
def exam_history(request):
    results = (
        ExamResult.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    return render(
        request,
        "students/exam_history.html",
        {
            "results": results,
            "exam_results": results,
        }
    )


@login_required
def exam_detail(request, id):
    result = get_object_or_404(
        ExamResult,
        id=id,
        user=request.user
    )

    return render(
        request,
        "students/exam_detail.html",
        {
            "result": result,
            "exam": result,
        }
    )


@login_required
def student_dashboard(request):
    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    results = (
        ExamResult.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    latest_result = results.first()

    return render(
        request,
        "students/dashboard.html",
        {
            "profile": profile,
            "results": results,
            "latest_result": latest_result,
        }
    )


def _level_from_percentage(percentage):
    if percentage >= 85:
        return "عالی"
    elif percentage >= 70:
        return "خوب"
    elif percentage >= 50:
        return "متوسط"
    elif percentage >= 30:
        return "نیاز به تمرین"
    else:
        return "شروع از پایه"


def _build_learning_plan(skill_results):
    plans = []

    for skill, data in skill_results.items():
        percentage = data.get("percentage", 0)
        level = data.get("level", "")

        if percentage < 50:
            plans.append(
                f"{skill}: نیاز به تمرین بیشتر و مرور مفاهیم پایه."
            )

        elif percentage < 70:
            plans.append(
                f"{skill}: سطح متوسط؛ تمرین هدفمند پیشنهاد می‌شود."
            )

        elif percentage < 85:
            plans.append(
                f"{skill}: عملکرد خوب؛ با تمرین بیشتر تثبیت شود."
            )

        else:
            plans.append(
                f"{skill}: عملکرد عالی؛ آماده حرکت به مباحث دشوارتر."
            )

    return "\n".join(plans)


@login_required
def start_test(request):
    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "GET":

        questions = list(
            Question.objects
            .filter(
                active=True,
                grade=profile.grade
            )
            .filter(
                track=profile.track
            )
            .order_by("?")[:20]
        )

        if not questions:
            questions = list(
                Question.objects
                .filter(
                    active=True,
                    grade=profile.grade
                )
                .order_by("?")[:20]
            )

        if not questions:
            messages.warning(
                request,
                "هنوز سؤال مناسب برای پایه شما در بانک سؤال ثبت نشده است."
            )

            return render(
                request,
                "students/test.html",
                {
                    "questions": [],
                    "no_questions": True,
                }
            )

        request.session["test_question_ids"] = [
            question.id
            for question in questions
        ]

        return render(
            request,
            "students/test.html",
            {
                "questions": questions
            }
        )

    question_ids = request.session.get(
        "test_question_ids",
        []
    )

    if not question_ids:
        messages.error(
            request,
            "آزمون شما منقضی شده است. لطفاً دوباره شروع کنید."
        )

        return redirect("start_test")

    questions = list(
        Question.objects.filter(
            id__in=question_ids,
            active=True
        )
    )

    question_map = {
        question.id: question
        for question in questions
    }

    correct_count = 0
    topic_stats = {}

    for question_id in question_ids:

        question = question_map.get(question_id)

        if question is None:
            continue

        answer = request.POST.get(
            f"question_{question.id}",
            ""
        ).lower()

        topic = question.topic or "سایر"

        if topic not in topic_stats:
            topic_stats[topic] = {
                "correct": 0,
                "total": 0,
            }

        topic_stats[topic]["total"] += 1

        if answer == question.correct_answer:
            correct_count += 1
            topic_stats[topic]["correct"] += 1

    total_questions = len(question_ids)

    if total_questions == 0:
        total_questions = 20

    percentage = (
        correct_count / total_questions
    ) * 100

    skill_results = {}

    for topic, data in topic_stats.items():

        topic_percentage = (
            data["correct"] / data["total"]
        ) * 100

        skill_results[topic] = {
            "correct": data["correct"],
            "total": data["total"],
            "percentage": round(
                topic_percentage,
                1
            ),
            "level": _level_from_percentage(
                topic_percentage
            ),
        }

    learning_plan = _build_learning_plan(
        skill_results
    )

    result = ExamResult.objects.create(
        user=request.user,
        score=correct_count,
        total=total_questions,
        skill_results=skill_results,
        learning_plan=learning_plan,
    )

    request.session.pop(
        "test_question_ids",
        None
    )

    return render(
        request,
        "students/result.html",
        {
            "result": result,
            "score": correct_count,
            "total": total_questions,
            "percentage": round(
                percentage,
                1
            ),
            "skill_results": skill_results,
            "learning_plan": learning_plan,
        }
    )
'''

Path("students/views.py").write_text(
    code,
    encoding="utf-8"
)

print("students/views.py ساخته شد.")