from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    path('', views.progress_page, name='progress_page'),
    path('ai-insights/', views.get_ai_insights, name='get_ai_insights'),
]