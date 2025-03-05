from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    EventListView, EventDetailView, EventCreateView, EventUpdateView, EventDeleteView,
    SignUpView, login_view, logout_view, activate_account, ProfileView, EditProfileView,
    ChangePasswordView, AdminDashboardView, organizer_dashboard, participant_dashboard,
    create_group, GroupDeleteView, GroupDetailView, change_user_role, UserDeleteView, rsvp_event
)

urlpatterns = [
    # Event Management
    path('', EventListView.as_view(), name='event_list'),
    path('event/new/', EventCreateView.as_view(), name='event_create'),
    path('event/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('event/<int:pk>/edit/', EventUpdateView.as_view(), name='event_edit'),
    path('event/<int:pk>/delete/', EventDeleteView.as_view(), name='event_delete'),
    path('event/<int:pk>/rsvp/', rsvp_event, name='rsvp_event'),
    
    # Authentication & Account Activation
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('activate/<uidb64>/<token>/', activate_account, name='activate'),
    
    # Dashboard Views
    path('dashboard/admin/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('dashboard/admin/change_role/<int:user_id>/<str:role>/', change_user_role, name='change_user_role'),
    path('dashboard/admin/delete_user/<int:pk>/', UserDeleteView.as_view(), name='delete_user'),
    path('dashboard/organizer/', organizer_dashboard, name='organizer_dashboard'),
    path('dashboard/participant/', participant_dashboard, name='participant_dashboard'),
    
    # Group Management
    path('group/create/', create_group, name='create_group'),
    path('group/delete/<int:pk>/', GroupDeleteView.as_view(), name='delete_group'),
    path('group/<int:pk>/', GroupDetailView.as_view(), name='group_detail'),
    
    # Profile & Password Management
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', EditProfileView.as_view(), name='profile_edit'),
    path('profile/change_password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Password Reset Workflow
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]
