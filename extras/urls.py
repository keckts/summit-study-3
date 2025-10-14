from django.urls import path
from . import views

app_name = 'extras'

urlpatterns = [
    path('achievements/', views.achievements, name='achievements'),
    path('programs/', views.programs, name='programs'),

    path("program/new/", views.program_form_view, name="create_program"),
    path("program/<int:pk>/edit/", views.program_form_view, name="edit_program"),

    path('chatbot/', views.chatbot, name='chatbot'),
]