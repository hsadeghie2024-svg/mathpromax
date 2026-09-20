from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import StudentRegistrationForm


def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('register_success')

    else:
        form = StudentRegistrationForm()

    return render(request, 'students/register.html', {'form': form})


def register_success(request):
    return render(request, 'students/success.html')


def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('student_dashboard')

        return render(request, 'students/login.html', {
            'error': 'نام کاربری یا رمز عبور اشتباه است.'
        })

    return render(request, 'students/login.html')


def student_dashboard(request):
    return render(request, 'students/dashboard.html')


def start_test(request):

    if request.method == 'POST':

        answers = {
            'q1': 'b',
            'q2': 'b',
            'q3': 'b',
            'q4': 'a',
            'q5': 'a',
            'q6': 'c',
            'q7': 'c',
            'q8': 'b',
            'q9': 'b',
            'q10': 'c',
            'q11': 'c',
            'q12': 'a',
            'q13': 'c',
            'q14': 'c',
            'q15': 'b',
            'q16': 'c',
            'q17': 'c',
            'q18': 'b',
            'q19': 'b',
            'q20': 'b',
        }

        skills = {
            'اعداد و ارزش مکانی': ['q1', 'q2', 'q5'],
            'جمع و تفریق': ['q3', 'q4'],
            'ضرب و تقسیم': ['q6', 'q7', 'q8', 'q9'],
            'مسائل کلامی': ['q10', 'q11', 'q12'],
            'هندسه': ['q13', 'q14', 'q15'],
            'اندازه‌گیری و زمان': ['q16', 'q17', 'q18'],
            'الگو و استدلال': ['q19', 'q20'],
        }

        score = 0
        skill_results = {}

        for question, correct_answer in answers.items():

            student_answer = request.POST.get(question)

            if student_answer == correct_answer:
                score += 1

        for skill_name, questions in skills.items():

            correct = 0

            for question in questions:

                if request.POST.get(question) == answers[question]:
                    correct += 1

            total = len(questions)
            percentage = round((correct / total) * 100)

            if percentage >= 80:
                level = 'بسیار خوب'
            elif percentage >= 60:
                level = 'خوب'
            elif percentage >= 40:
                level = 'متوسط'
            else:
                level = 'نیاز به تقویت'

            skill_results[skill_name] = {
                'correct': correct,
                'total': total,
                'percentage': percentage,
                'level': level,
            }

        return render(request, 'students/result.html', {
            'score': score,
            'total': 20,
            'skill_results': skill_results,
        })

    return render(request, 'students/test.html')


