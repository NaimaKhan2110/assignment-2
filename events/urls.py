from django.urls import path
from . import views

urlpatterns = [
    # Public and authentication routes
    path('', views.event_list, name='event_list'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),
    
    # Dashboard Views
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/organizer/', views.organizer_dashboard, name='organizer_dashboard'),
    path('dashboard/participant/', views.participant_dashboard, name='participant_dashboard'),
    
    # Event Views
    path('event/new/', views.event_create, name='event_create'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),  # Path for event details by ID
    path('event/<slug:slug>/', views.event_detail, name='event_detail_slug'),  # Path for event details by slug
    path('event/<int:event_id>/edit/', views.event_edit, name='event_edit'),
    path('event/<int:event_id>/delete/', views.event_delete, name='event_delete'),
    path('event/<int:event_id>/rsvp/', views.rsvp_event, name='rsvp_event'),
    
    # Admin-Only Operations (all under dashboard/admin/)
    path('dashboard/admin/change_role/<int:user_id>/', views.change_user_role, name='change_user_role'),
    path('dashboard/admin/create_group/', views.create_group, name='create_group'),
    path('dashboard/admin/delete_group/<int:group_id>/', views.delete_group, name='delete_group'),
    path('dashboard/admin/delete_participant/<int:user_id>/', views.delete_participant, name='delete_participant'),
]
