from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('auction/<int:pk>/', views.auction_detail, name='auction_detail'),
    path('create/', views.create_auction, name='create_auction'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('auction/<int:pk>/checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('auction/<int:pk>/success/', views.payment_success, name='payment_success'),
]
