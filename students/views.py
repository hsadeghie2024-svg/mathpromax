import ast

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User

from .forms import StudentRegistrationForm, StudentProfileForm
from .models import (
    StudentProfile,
    ExamResult,
    Question,
    PasswordResetOTP,
    LessonProgress,
    ExerciseResult,
    )


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

    # تبدیل مسیر یادگیری ذخیره‌شده در دیتابیس
    # از متن به لیست واقعی Python
    learning_plan = result.learning_plan

    if isinstance(learning_plan, str):
        try:
            learning_plan = ast.literal_eval(
                learning_plan
            )
        except (ValueError, SyntaxError):
            learning_plan = []

    # اطمینان از اینکه همیشه لیست داریم
    if not isinstance(learning_plan, list):
        learning_plan = []

    return render(
        request,
        "students/exam_detail.html",
        {
            "result": result,
            "exam": result,
            "learning_plan": learning_plan,
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
    """
    تعیین سطح عملکرد دانش‌آموز بر اساس درصد.
    """

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


def _lesson_info(skill):
    """
    اتصال نام مهارت آزمون به درس مربوطه.
    """

    lessons = {
        "ضرب و تقسیم": {
            "lesson_slug": "multiplication-division",
            "lesson_title": "آموزش ضرب و تقسیم",
        },

        "جمع و تفریق": {
            "lesson_slug": "addition-subtraction",
            "lesson_title": "آموزش جمع و تفریق",
        },

        "هندسه": {
            "lesson_slug": "geometry",
            "lesson_title": "آموزش هندسه",
        },

        "اعداد": {
            "lesson_slug": "numbers",
            "lesson_title": "آموزش اعداد",
        },

        "کسرها": {
            "lesson_slug": "fractions",
            "lesson_title": "آموزش کسرها",
        },

        "توان": {
            "lesson_slug": "powers",
            "lesson_title": "آموزش توان",
        },
    }

    return lessons.get(
        skill,
        {
            "lesson_slug": "",
            "lesson_title": f"آموزش {skill}",
        }
    )


def _build_learning_plan(skill_results):
    """
    ساخت مسیر یادگیری شخصی‌سازی‌شده AIZAVA
    بر اساس ضعیف‌ترین مهارت‌های دانش‌آموز.
    """

    if not skill_results:
        return []

    # مرتب‌سازی مهارت‌ها از ضعیف‌ترین به قوی‌ترین
    sorted_skills = sorted(
        skill_results.items(),
        key=lambda item: item[1].get("percentage", 0)
    )

    # حداکثر سه مهارت با اولویت بالاتر
    weak_skills = sorted_skills[:3]

    plans = []

    for priority, (skill, data) in enumerate(
        weak_skills,
        start=1
    ):

        percentage = data.get("percentage", 0)
        level = data.get(
            "level",
            _level_from_percentage(percentage)
        )

        # تعیین وضعیت آموزشی
        if percentage < 30:
            status = "نیازمند آموزش پایه"

            steps = [
                "مرور مفاهیم پایه",
                "آشنایی با مفهوم و مثال‌های ساده",
                "حل تمرین‌های ساده",
                "حل تمرین‌های سطح پایه",
                "آزمون کوتاه برای سنجش یادگیری",
            ]

        elif percentage < 50:
            status = "نیازمند تمرین بیشتر"

            steps = [
                "مرور مفاهیم اصلی",
                "حل تمرین‌های ساده و هدفمند",
                "بررسی و اصلاح اشتباه‌ها",
                "حل تمرین‌های سطح متوسط",
                "آزمون کوتاه تثبیت مهارت",
            ]

        elif percentage < 70:
            status = "در حال یادگیری"

            steps = [
                "مرور نکات مهم",
                "حل تمرین‌های متوسط",
                "حل مسائل چندمرحله‌ای",
                "تمرین ترکیبی",
                "آزمون تثبیت مهارت",
            ]

        elif percentage < 85:
            status = "نیازمند تقویت"

            steps = [
                "مرور نکات تکمیلی",
                "حل تمرین‌های چالشی",
                "حل مسائل ترکیبی",
                "تمرین سرعت و دقت",
                "آزمون پیشرفته",
            ]

        else:
            status = "تسلط خوب"

            steps = [
                "مرور سریع مطالب",
                "حل تمرین‌های پیشرفته",
                "حل مسائل چالشی",
                "تمرین‌های تیزهوشان",
                "آمادگی برای مباحث دشوارتر",
            ]

        lesson = _lesson_info(skill)

        plans.append({
            "priority": priority,
            "skill": skill,
            "percentage": percentage,
            "level": level,
            "status": status,
            "lesson_slug": lesson["lesson_slug"],
            "lesson_title": lesson["lesson_title"],
            "steps": steps,
        })

    return plans
@login_required
def start_test(request):
    profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    # -----------------------------
    # نمایش آزمون
    # -----------------------------
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

        # اگر برای رشته/گرایش سؤال پیدا نشد،
        # فقط بر اساس پایه جست‌وجو می‌کنیم.
        if not questions:
            questions = list(
                Question.objects
                .filter(
                    active=True,
                    grade=profile.grade
                )
                .order_by("?")[:20]
            )

        # اگر هیچ سؤالی وجود نداشت
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

        # ذخیره شناسه سؤال‌ها در Session
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

    # -----------------------------
    # دریافت پاسخ‌های آزمون
    # -----------------------------

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

    # آمار مهارت‌ها
    topic_stats = {}

    # -----------------------------
    # بررسی پاسخ‌ها
    # -----------------------------

    for question_id in question_ids:

        question = question_map.get(question_id)

        if question is None:
            continue

        # توجه:
        # نام فیلد دقیقاً مطابق test.html است:
        # question_{{ question.id }}
        answer = request.POST.get(
            f"question_{question.id}",
            ""
        ).strip().lower()

        topic = question.topic or "سایر"

        if topic not in topic_stats:
            topic_stats[topic] = {
                "correct": 0,
                "total": 0,
            }

        topic_stats[topic]["total"] += 1

        # پاسخ صحیح
        if answer == question.correct_answer:
            correct_count += 1
            topic_stats[topic]["correct"] += 1

    # -----------------------------
    # محاسبه نتیجه کلی
    # -----------------------------

    total_questions = len(question_ids)

    if total_questions == 0:
        total_questions = 1

    percentage = (
        correct_count / total_questions
    ) * 100

    percentage = round(
        percentage,
        1
    )

    overall_level = _level_from_percentage(
        percentage
    )

    # -----------------------------
    # تحلیل مهارت‌ها
    # -----------------------------

    skill_results = {}

    for topic, data in topic_stats.items():

        topic_percentage = (
            data["correct"] / data["total"]
        ) * 100

        topic_percentage = round(
            topic_percentage,
            1
        )

        skill_results[topic] = {
            "correct": data["correct"],
            "total": data["total"],
            "percentage": topic_percentage,
            "level": _level_from_percentage(
                topic_percentage
            ),
        }

    # -----------------------------
    # ساخت مسیر یادگیری
    # -----------------------------

    learning_plan = _build_learning_plan(
        skill_results
    )

    # -----------------------------
    # ذخیره نتیجه در دیتابیس
    # -----------------------------

    result = ExamResult.objects.create(
        user=request.user,
        score=correct_count,
        total=total_questions,
        skill_results=skill_results,
        learning_plan=learning_plan,
    )

    # پاک کردن آزمون فعلی از Session
    request.session.pop(
        "test_question_ids",
        None
    )

    # -----------------------------
    # نمایش صفحه نتیجه
    # -----------------------------

    return render(
        request,
        "students/result.html",
        {
            "result": result,
            "score": correct_count,
            "total": total_questions,
            "percentage": percentage,
            "overall_level": overall_level,
            "skill_results": skill_results,
            "learning_plan": learning_plan,
        }
    )

@login_required
def learning_topic(request, slug):

    topics = {
        "multiplication-division": {
            "title": "آموزش ضرب و تقسیم",
            "grade": "هفتم",
            "icon": "✖️➗",
            "description": "یادگیری ضرب و تقسیم به زبان ساده و مرحله‌به‌مرحله.",
        },

        "addition-subtraction": {
            "title": "آموزش جمع و تفریق",
            "grade": "هفتم",
            "icon": "➕➖",
            "description": "یادگیری جمع و تفریق با مثال‌ها و تمرین‌های هدفمند.",
        },

        "geometry": {
            "title": "آموزش هندسه",
            "grade": "هفتم",
            "icon": "📐",
            "description": "یادگیری مفاهیم پایه هندسه و حل مسائل هندسی.",
        },

        "numbers": {
            "title": "آموزش اعداد",
            "grade": "هفتم",
            "icon": "🔢",
            "description": "یادگیری مفاهیم اعداد و مهارت‌های عددی.",
        },

        "fractions": {
            "title": "آموزش کسرها",
            "grade": "هفتم",
            "icon": "🍕",
            "description": "یادگیری کسرها با مثال‌های ساده و کاربردی.",
        },

        "powers": {
            "title": "آموزش توان",
            "grade": "هفتم",
            "icon": "⚡",
            "description": "یادگیری مفهوم توان و قوانین توان‌ها.",
        },
    }

    topic = topics.get(slug)

    if topic is None:
        return redirect("student_dashboard")

    return render(
        request,
        "students/learning_topic.html",
        {
            "topic": topic,
            "slug": slug,
        }
    )
@login_required
def lesson_topic(request, slug):

    lessons = {

        # =====================================================
        # 1. ضرب و تقسیم
        # =====================================================
        "multiplication-division": {
            "title": "آموزش ضرب و تقسیم",
            "grade": "هفتم",
            "icon": "✖️",
            "intro": (
                "در این درس مفهوم ضرب و تقسیم را از پایه یاد می‌گیریم "
                "و سپس با مثال‌های ساده و کاربردی مهارت خود را تقویت می‌کنیم."
            ),
            "sections": [
                {
                    "title": "۱. مفهوم ضرب",
                    "text": (
                        "ضرب یعنی جمع کردن چندباره یک عدد. "
                        "برای مثال ۵ × ۶ یعنی عدد ۵ را شش بار با هم جمع کنیم."
                    ),
                    "example": "۵ + ۵ + ۵ + ۵ + ۵ + ۵ = ۳۰  ←  ۵ × ۶     = ۳۰",
                },
                {
                    "title": "۲. مفهوم تقسیم",
                    "text": (
                        "تقسیم یعنی تقسیم کردن یک مقدار به قسمت‌های مساوی."
                    ),
                    "example": "۳۰ ÷ ۵ = ۶",
                },
                {
                    "title": "۳. رابطه ضرب و تقسیم",
                    "text": (
                        "ضرب و تقسیم دو عمل مرتبط هستند و می‌توانیم "
                        "با استفاده از یکی، دیگری را بررسی کنیم."
                    ),
                    "example": (
                        "۵ × ۶ = ۳۰\n"
                        "۳۰ ÷ ۵ = ۶\n"
                        "۳۰ ÷ ۶ = ۵"
                    ),
                },
                {
                    "title": "۴. ضرب اعداد بزرگ‌تر",
                    "text": (
                        "برای ضرب اعداد بزرگ‌تر، ابتدا ارزش مکانی اعداد "
                        "را در نظر می‌گیریم و سپس مراحل ضرب را انجام می‌دهیم."
                    ),
                    "example": "۲۳ × ۴ = ۹۲",
                },
                {
                    "title": "۵. تقسیم اعداد بزرگ‌تر",
                    "text": (
                        "در تقسیم باید مشخص کنیم عدد مقسوم بر چه عددی "
                        "تقسیم می‌شود و حاصل را مرحله‌به‌مرحله به دست آوریم."
                    ),
                    "example": "۴۸ ÷ ۶ = ۸",
                },
            ],
            "exercises": [
                "۵ × ۶ = ؟",
                "۳۶ ÷ ۶ = ؟",
                "۷ × ۸ = ؟",
                "۶۴ ÷ ۸ = ؟",
                "۱۲ × ۵ = ؟",
            ],
        },

        # =====================================================
        # 2. جمع و تفریق
        # =====================================================
        "addition-subtraction": {
            "title": "آموزش جمع و تفریق",
            "grade": "هفتم",
            "icon": "➕",
            "intro": (
                "در این درس جمع و تفریق اعداد را از پایه مرور می‌کنیم "
                "و با مثال‌های ساده به سراغ محاسبات دقیق‌تر می‌رویم."
            ),
            "sections": [
                {
                    "title": "۱. مفهوم جمع",
                    "text": (
                        "جمع کردن یعنی کنار هم قرار دادن دو یا چند مقدار "
                        "برای به دست آوردن مقدار کل."
                    ),
                    "example": "۱۲ + ۸ = ۲۰",
                },
                {
                    "title": "۲. مفهوم تفریق",
                    "text": (
                        "تفریق یعنی کم کردن یک مقدار از مقدار دیگر."
                    ),
                    "example": "۲۰ - ۸ = ۱۲",
                },
                {
                    "title": "۳. جمع اعداد چندرقمی",
                    "text": (
                        "در جمع اعداد چندرقمی، از رقم یکان شروع می‌کنیم "
                        "و در صورت نیاز انتقال انجام می‌دهیم."
                    ),
                    "example": "۲۷ + ۳۵ = ۶۲",
                },
                {
                    "title": "۴. تفریق اعداد چندرقمی",
                    "text": (
                        "در تفریق نیز از رقم یکان شروع می‌کنیم و در صورت "
                        "نیاز از رقم سمت چپ قرض می‌گیریم."
                    ),
                    "example": "۷۲ - ۳۸ = ۳۴",
                },
            ],
            "exercises": [
                "۲۵ + ۳۷ = ؟",
                "۸۰ - ۲۶ = ؟",
                "۴۸ + ۲۹ = ؟",
                "۹۵ - ۴۷ = ؟",
                "۱۲۵ + ۷۵ = ؟",
            ],
        },

        # =====================================================
        # 3. اعداد
        # =====================================================
        "numbers": {
            "title": "آموزش اعداد",
            "grade": "هفتم",
            "icon": "🔢",
            "intro": (
                "در این درس با مفهوم اعداد، ارزش مکانی، مقایسه اعداد "
                "و محاسبات عددی آشنا می‌شویم."
            ),
            "sections": [
                {
                    "title": "۱. مفهوم عدد",
                    "text": (
                        "عدد برای نمایش مقدار یا تعداد استفاده می‌شود. "
                        "اعداد می‌توانند طبیعی، صحیح و در مباحث پیشرفته‌تر "
                        "از انواع دیگر باشند."
                    ),
                    "example": "۳ ، ۷ ، ۱۲ ، ۲۵ ، ۱۰۰",
                },
                {
                    "title": "۲. ارزش مکانی",
                    "text": (
                        "هر رقم با توجه به جایگاه خود دارای ارزش متفاوتی است."
                    ),
                    "example": (
                        "در عدد ۳۵۷:\n"
                        "۳ صدگان است.\n"
                        "۵ دهگان است.\n"
                        "۷ یکان است."
                    ),
                },
                {
                    "title": "۳. مقایسه اعداد",
                    "text": (
                        "برای مقایسه دو عدد ابتدا تعداد رقم‌ها و سپس "
                        "ارزش رقم‌ها را بررسی می‌کنیم."
                    ),
                    "example": "۷۵ > ۶۸",
                },
                {
                    "title": "۴. ترتیب اعداد",
                    "text": (
                        "اعداد را می‌توانیم از کوچک به بزرگ یا از بزرگ "
                        "به کوچک مرتب کنیم."
                    ),
                    "example": "۳ ، ۷ ، ۱۲ ، ۱۸ ، ۲۵",
                },
            ],
            "exercises": [
                "ارزش رقم ۵ در عدد ۵۲۳ چیست؟",
                "کدام بزرگ‌تر است؟ ۷۸ یا ۸۷",
                "اعداد ۵، ۲، ۹ را از کوچک به بزرگ مرتب کنید.",
                "عدد بعد از ۹۹ چیست؟",
                "عدد ۴۲ چند دهگان و چند یکان دارد؟",
            ],
        },

        # =====================================================
        # 4. کسرها
        # =====================================================
        "fractions": {
            "title": "آموزش کسرها",
            "grade": "هفتم",
            "icon": "🍕",
            "intro": (
                "در این درس مفهوم کسر، صورت و مخرج، کسرهای مساوی "
                "و مقایسه کسرها را یاد می‌گیریم."
            ),
            "sections": [
                {
                    "title": "۱. مفهوم کسر",
                    "text": (
                        "کسر برای نمایش بخشی از یک کل استفاده می‌شود. "
                        "عدد بالا صورت و عدد پایین مخرج نام دارد."
                    ),
                    "example": "۳/۵",
                },
                {
                    "title": "۲. صورت و مخرج",
                    "text": (
                        "در کسر ۳/۵، عدد ۳ صورت و عدد ۵ مخرج است."
                    ),
                    "example": "صورت = ۳ ، مخرج = ۵",
                },
                {
                    "title": "۳. کسرهای مساوی",
                    "text": (
                        "با ضرب صورت و مخرج در یک عدد یکسان، "
                        "کسرهای مساوی ایجاد می‌شوند."
                    ),
                    "example": "۱/۲ = ۲/۴ = ۳/۶",
                },
                {
                    "title": "۴. مقایسه کسرها",
                    "text": (
                        "برای مقایسه کسرها می‌توانیم از مخرج مشترک "
                        "یا روش‌های دیگر استفاده کنیم."
                    ),
                    "example": "۳/۴ > ۱/۲",
                },
            ],
            "exercises": [
                "صورت کسر ۳/۷ چیست؟",
                "مخرج کسر ۵/۹ چیست؟",
                "کدام بزرگ‌تر است؟ ۱/۲ یا ۳/۴",
                "کسر مساوی با ۱/۲ بنویسید.",
                "۳/۶ را ساده کنید.",
            ],
        },

        # =====================================================
        # 5. توان
        # =====================================================
        "powers": {
            "title": "آموزش توان",
            "grade": "هفتم",
            "icon": "⚡",
            "intro": (
                "در این درس مفهوم توان، پایه و نما و محاسبه توان‌های "
                "ساده را یاد می‌گیریم."
            ),
            "sections": [
                {
                    "title": "۱. مفهوم توان",
                    "text": (
                        "توان روشی کوتاه برای نمایش ضرب تکراری یک عدد است."
                    ),
                    "example": "۲³ = ۲ × ۲ × ۲ = ۸",
                },
                {
                    "title": "۲. پایه و نما",
                    "text": (
                        "در عبارت ۵²، عدد ۵ پایه و عدد ۲ نما یا توان است."
                    ),
                    "example": "۵² = ۵ × ۵ = ۲۵",
                },
                {
                    "title": "۳. توان دوم",
                    "text": (
                        "توان دوم یک عدد یعنی آن عدد را در خودش ضرب کنیم."
                    ),
                    "example": "۷² = ۷ × ۷ = ۴۹",
                },
                {
                    "title": "۴. توان سوم",
                    "text": (
                        "توان سوم یک عدد یعنی آن عدد را سه بار در خودش ضرب کنیم."
                    ),
                    "example": "۳³ = ۳ × ۳ × ۳ = ۲۷",
                },
            ],
            "exercises": [
                "۲³ چند است؟",
                "۵² چند است؟",
                "۳³ چند است؟",
                "۴² چند است؟",
                "۱۰² چند است؟",
            ],
        },

        # =====================================================
        # 6. هندسه
        # =====================================================
        "geometry": {
            "title": "آموزش هندسه",
            "grade": "هفتم",
            "icon": "📐",
            "intro": (
                "در این درس با مفاهیم پایه هندسه، انواع شکل‌ها، "
                "محیط و مساحت آشنا می‌شویم."
            ),
            "sections": [
                {
                    "title": "۱. نقطه و خط",
                    "text": (
                        "نقطه یکی از ساده‌ترین مفاهیم هندسی است و "
                        "خط از امتداد نقاط در یک مسیر تشکیل می‌شود."
                    ),
                    "example": "A •────────• B",
                },
                {
                    "title": "۲. زاویه",
                    "text": (
                        "زاویه از دو نیم‌خط با مبدأ مشترک تشکیل می‌شود."
                    ),
                    "example": "زاویه ۹۰ درجه = زاویه راست",
                },
                {
                    "title": "۳. محیط",
                    "text": (
                        "محیط یک شکل برابر مجموع طول ضلع‌های آن است."
                    ),
                    "example": "محیط مربع با ضلع ۵ = ۴ × ۵ = ۲۰",
                },
                {
                    "title": "۴. مساحت",
                    "text": (
                        "مساحت اندازه سطح داخلی یک شکل است."
                    ),
                    "example": "مساحت مستطیل = طول × عرض",
                },
            ],
            "exercises": [
                "محیط مربع با ضلع ۶ چند است؟",
                "مساحت مستطیل با طول ۸ و عرض ۳ چند است؟",
                "زاویه ۹۰ درجه چه نام دارد؟",
                "یک مثلث چند ضلع دارد؟",
                "یک مربع چند زاویه راست دارد؟",
            ],
        },
    }

    lesson = lessons.get(slug)

    if lesson is None:
        return redirect("student_dashboard")

    return render(
        request,
        "students/lesson_topic.html",
        {
            "lesson": lesson,
            "slug": slug,
        }
    )

@login_required
def lesson_exercise(request, slug):

    exercises = {

        # =========================
        # اعداد
        # =========================
        "numbers": [
            {
                "question": "عدد ۴۵ چند ده‌تایی و چند یکی دارد؟",
                "answer": "4 و 5",
            },
            {
                "question": "عدد ۷۰۳ را به صورت گسترده بنویسید.",
                "answer": "700 + 3",
            },
            {
                "question": "کدام عدد بزرگ‌تر است؟ ۵۸ یا ۸۵",
                "answer": "85",
            },
            {
                "question": "عدد بعد از ۹۹۹ چیست؟",
                "answer": "1000",
            },
            {
                "question": "عدد ۴۰۰ چند صدتایی دارد؟",
                "answer": "4",
            },
        ],

        # =========================
        # جمع و تفریق
        # =========================
        "addition-subtraction": [
            {
                "question": "۲۵ + ۳۷ چند می‌شود؟",
                "answer": "62",
            },
            {
                "question": "۸۵ - ۲۹ چند می‌شود؟",
                "answer": "56",
            },
            {
                "question": "۱۴۶ + ۲۳۴ چند می‌شود؟",
                "answer": "380",
            },
            {
                "question": "۵۰۰ - ۲۷۵ چند می‌شود؟",
                "answer": "225",
            },
            {
                "question": "۳۶ + ۴۸ چند می‌شود؟",
                "answer": "84",
            },
        ],

        # =========================
        # ضرب و تقسیم
        # =========================
        "multiplication-division": [
            {
                "question": "۵ × ۶ چند می‌شود؟",
                "answer": "30",
            },
            {
                "question": "۳۶ ÷ ۶ چند می‌شود؟",
                "answer": "6",
            },
            {
                "question": "۷ × ۸ چند می‌شود؟",
                "answer": "56",
            },
            {
                "question": "۶۴ ÷ ۸ چند می‌شود؟",
                "answer": "8",
            },
            {
                "question": "۱۲ × ۵ چند می‌شود؟",
                "answer": "60",
            },
        ],

        # =========================
        # هندسه
        # =========================
        "geometry": [
            {
                "question": "مربع چند ضلع دارد؟",
                "answer": "4",
            },
            {
                "question": "مثلث چند ضلع دارد؟",
                "answer": "3",
            },
            {
                "question": "مستطیلی با طول ۸ و عرض ۳، چند واحد محیط دارد؟",
                "answer": "22",
            },
            {
                "question": "مربعی با ضلع ۵، چند واحد محیط دارد؟",
                "answer": "20",
            },
            {
                "question": "مستطیلی با طول ۶ و عرض ۴، چند واحد مساحت دارد؟",
                "answer": "24",
            },
        ],

        # =========================
        # کسرها
        # =========================
        "fractions": [
            {
                "question": "صورت کسر ۳/۵ چیست؟",
                "answer": "3",
            },
            {
                "question": "مخرج کسر ۷/۹ چیست؟",
                "answer": "9",
            },
            {
                "question": "۱/۲ + ۱/۲ چند می‌شود؟",
                "answer": "1",
            },
            {
                "question": "۳/۴ از ۲۰ چند می‌شود؟",
                "answer": "15",
            },
            {
                "question": "کدام کسر بزرگ‌تر است؟ ۱/۲ یا ۳/۴",
                "answer": "3/4",
            },
        ],

        # =========================
        # توان
        # =========================
        "powers": [
            {
                "question": "۲ به توان ۲ چند می‌شود؟",
                "answer": "4",
            },
            {
                "question": "۳ به توان ۲ چند می‌شود؟",
                "answer": "9",
            },
            {
                "question": "۲ به توان ۳ چند می‌شود؟",
                "answer": "8",
            },
            {
                "question": "۵ به توان ۲ چند می‌شود؟",
                "answer": "25",
            },
            {
                "question": "۱۰ به توان ۲ چند می‌شود؟",
                "answer": "100",
            },
        ],
    }

    exercise_list = exercises.get(slug)

    if exercise_list is None:
        return redirect("student_dashboard")

    results = []
    score = None

    if request.method == "POST":

        correct = 0

        for index, exercise in enumerate(exercise_list):

            user_answer = request.POST.get(
                f"answer_{index}",
                ""
            ).strip()

            is_correct = (
                user_answer == exercise["answer"]
            )

            if is_correct:
                correct += 1

            results.append(
                {
                    "question": exercise["question"],
                    "user_answer": user_answer,
                    "correct_answer": exercise["answer"],
                    "is_correct": is_correct,
                }
            )

        total_questions = len(exercise_list)

        wrong = total_questions - correct

        score = round(
            (correct / total_questions) * 100
        )

        # ذخیره سابقه تمرین
        ExerciseResult.objects.create(
            user=request.user,
            topic=slug,
            total_questions=total_questions,
            correct_answers=correct,
            wrong_answers=wrong,
            score=score,
        )

        # دریافت یا ایجاد وضعیت پیشرفت مبحث
        progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            topic=slug,
        )

        progress.last_score = score
        progress.attempts += 1

        if score > progress.best_score:
            progress.best_score = score

        if score >= 80:
            progress.completed = True

        progress.save()

    return render(
        request,
        "students/lesson_exercise.html",
        {
            "slug": slug,
            "exercises": exercise_list,
            "results": results,
            "score": score,
        }
    )