from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # --- Core Site Pages ---
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),

    # --- Product Discovery ---
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # --- Cart Management ---
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/count/', views.cart_count, name='cart_count'),
    path('cart/calculate-shipping/', views.calculate_shipping_ajax, name='calculate_shipping_ajax'),

    # --- Checkout Process ---
    path('checkout/', views.checkout, name='checkout'),
    path('order/create/', views.create_order_and_redirect_to_payment, name='create_order_and_payment'),

    # --- User Account & Profile ---
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', views.user_login, name='login'),
    path('accounts/logout/', views.user_logout, name='logout'),

    # --- Wishlist ---
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.wishlist_add, name='wishlist_add'),
    path('wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),

    # --- Reviews ---
    path('product/<int:product_id>/add_review/', views.add_review, name='add_review'),
    path('review/<int:review_id>/helpful/', views.mark_review_helpful, name='mark_review_helpful'),
]
