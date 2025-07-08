from django.urls import path
from . import views

app_name = 'payment_processing'

urlpatterns = [
    path('create/', views.create_payment, name='create_payment'),
    path('custom_create/', views.custom_create_preference, name='custom_create_preference'),
    path('success/', views.payment_success, name='payment_success'),
    path('failure/', views.payment_failure, name='payment_failure'),
    path('pending/', views.payment_pending, name='payment_pending'),
    path('webhook/', views.webhook, name='webhook'),
]
