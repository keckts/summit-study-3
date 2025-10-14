from django.urls import path
from . import views

app_name = "service"

urlpatterns = [
    path('support/', views.support, name='support'),
    path('view_blogs/', views.view_blogs, name='view_blogs'),
    path('blog/<int:blog_id>/', views.blog, name='blog'),
    path('create_blog/', views.create_blog, name='create_blog'),

    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('about-us/', views.about_us, name='about_us'),
]