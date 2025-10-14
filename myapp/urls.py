from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Practice tests URLs
    path('practice-tests/', views.practice_tests, name='practice_tests'),
    path('practice-tests/<uuid:pk>/take/', views.take_practice_test, name='take_practice_test'),
    path("practice_tests/create/", views.practice_test_form, name="create_practice_test"),
    path("practice_tests/<uuid:pk>/edit/", views.practice_test_form, name="edit_practice_test"),
    path("practice_tests/<uuid:pk>/delete/", views.delete_practice_test, name="delete_practice_test"),

    path('create-ai-activity/<str:activity_type>/', views.create_ai_activity, name='create_ai_activity'),
    

    # Writing tasks URLs
    path('writing-tasks/', views.writing_tasks, name='writing_tasks'),
    path("writing-task/<uuid:pk>/take/", views.take_writing_task, name="take_writing_task"),
    path("writing-task/<uuid:pk>/results/", views.writing_task_result, name="writing_task_result"),
    path('writing-task/<uuid:pk>/loading/', views.writing_task_loading, name='writing_task_loading'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),

    path("writing-tasks/create/", views.writing_task_form, name="create_writing_task"),
    path("writing-tasks/<uuid:pk>/edit/", views.writing_task_form, name="edit_writing_task"),
    path("writing-tasks/<uuid:pk>/delete/", views.writing_task_form, name="delete_writing_task"),

    # Flashcards URLs
    path('flashcards/', views.flashcard_sets, name='flashcard_sets'),
    path('flashcards/create/', views.flashcard_set_form, name='create_flashcard_set'),
    path('flashcards/<uuid:set_id>/take/', views.take_flashcard_set, name='take_flashcard_set'),
    path('flashcards/<uuid:set_id>/summary/', views.flashcard_summary, name='flashcard_summary'),

    path('flashcards/<uuid:set_id>/edit/', views.flashcard_set_form, name='edit_flashcard_set'),
    path('flashcards/<uuid:set_id>/delete/', views.flashcard_set_form, name='delete_flashcard_set'),
    

    path('answer-flashcard/<uuid:set_id>/<str:action>/', views.answer_flashcard, name='answer_flashcard'),
    path('answer-flashcard-ajax/<uuid:set_id>/', views.answer_flashcard_ajax, name='answer_flashcard_ajax'),
    path('flashcard-nav-ajax/<uuid:set_id>/', views.flashcard_nav_ajax, name='flashcard_nav_ajax'),
    path('reset-flashcards-ajax/<uuid:set_id>/', views.reset_flashcards_ajax, name='reset_flashcards_ajax'),

]
