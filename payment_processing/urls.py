from django.urls import path
from . import views
from .views import painel_pagamentos, reprocessar_pedido, cancelar_pedido, reprocessar_todos_pendentes, notificacoes_recentes

app_name = 'payment_processing'

urlpatterns = [
    path('create/', views.create_payment, name='create_payment'),
    path('custom_create/', views.custom_create_preference, name='custom_create_preference'),
    path('success/', views.payment_success, name='payment_success'),
    path('failure/', views.payment_failure, name='payment_failure'),
    path('pending/', views.payment_pending, name='payment_pending'),
    path('webhook/', views.webhook, name='webhook'),
    path("admin/painel-pagamentos/", painel_pagamentos, name="painel_pagamentos"),
    path('admin/reprocessar-pedido/<int:pedido_id>/', reprocessar_pedido, name='reprocessar_pedido'),
    path('admin/cancelar-pedido/<int:pedido_id>/', cancelar_pedido, name='cancelar_pedido'),
    path('admin/reprocessar-todos-pendentes/', reprocessar_todos_pendentes, name='reprocessar_todos_pendentes'),
    path('admin/notificacoes-recentes/', notificacoes_recentes, name='notificacoes_recentes'),
]
