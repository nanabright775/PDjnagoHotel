from accountss.views import *
from django.urls import path, include


urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='signup'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/<int:pk>/update/', ProfileUpdateView.as_view(), name='profile_update'),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
    path('profile/change-password/', CustomPasswordChangeView.as_view(), name='change_password'),
]