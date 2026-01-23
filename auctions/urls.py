from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('auction/<int:pk>/', views.auction_detail, name='auction_detail'),
    path('auction/<int:pk>/edit/', views.edit_auction, name='edit_auction'),
    path('auction/<int:pk>/delete/', views.delete_auction, name='delete_auction'),
    path('create/', views.create_auction, name='create_auction'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('auction/<int:pk>/checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('auction/<int:pk>/success/', views.payment_success, name='payment_success'),
]
