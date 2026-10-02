from django.urls import path
from . import views


urlpatterns = [

    # صفحه اصلی ثبت‌نام و ورود
    path(
        'register/',
        views.register_student,
        name='register_student'
    ),

    path(
        'success/',
        views.register_success,
        name='register_success'
    ),

    path(
        'login/',
        views.student_login,
        name='student_login'
    ),

    path(
        'logout/',
        views.student_logout,
        name='student_logout'
    ),


    # ==========================
    # بازیابی رمز عبور
    # ==========================

    path(
        'password-reset/',
        views.password_reset_request,
        name='password_reset_request'
    ),

    path(
        'password-reset/verify/',
        views.password_reset_verify,
        name='password_reset_verify'
    ),

    path(
        'password-reset/new-password/',
        views.password_reset_new_password,
        name='password_reset_new_password'
    ),


    # ==========================
    # پروفایل
    # ==========================

    path(
        'profile/',
        views.student_profile,
        name='student_profile'
    ),

    path(
        'profile/edit/',
        views.edit_profile,
        name='edit_profile'
    ),

    path(
        'profile/change-password/',
        views.change_password,
        name='change_password'
    ),


    # ==========================
    # آزمون
    # ==========================

    path(
        'exam-history/',
        views.exam_history,
        name='exam_history'
    ),

    path(
        'exam-detail/<int:id>/',
        views.exam_detail,
        name='exam_detail'
    ),

    path(
        'dashboard/',
        views.student_dashboard,
        name='student_dashboard'
    ),

    path(
    'lesson/<slug:slug>/',
    views.lesson_topic,
    name='lesson_topic'
    ), 

    path(
    'lesson/<slug:slug>/exercise/',
    views.lesson_exercise,
    name='lesson_exercise'
    ),

     path(
    'learning/<slug:slug>/',
    views.learning_topic,
    name='learning_topic'
    ),
    path(
        'test/',
        views.start_test,
        name='start_test'
    ),
]