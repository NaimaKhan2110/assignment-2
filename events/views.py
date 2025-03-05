import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth import (
    login,
    authenticate,
    logout,
    get_user_model
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.views.generic import (
    CreateView, ListView, DetailView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.models import Group

from .forms import SignUpForm, EventForm, EditProfileForm
from .models import Event

# Get the custom user model
CustomUser = get_user_model()

# Configure logging
logger = logging.getLogger(__name__)

# --------------------------------------------------
# 🔹 Helper Functions
# --------------------------------------------------

def is_admin(user):
    """
    Returns True if the user is a superuser or belongs to the 'Admin' group.
    """
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Admin').exists())

def is_organizer(user):
    """
    Returns True if the user belongs to the 'Organizer' group.
    """
    return user.is_authenticated and user.groups.filter(name='Organizer').exists()

def is_participant(user):
    """
    Returns True if the user belongs to the 'Participant' group.
    """
    return user.is_authenticated and user.groups.filter(name='Participant').exists()

# --------------------------------------------------
# 🔹 Authentication & Account Views
# --------------------------------------------------

class SignUpView(CreateView):
    """
    Class-based view for user signup with email activation.
    """
    form_class = SignUpForm
    template_name = 'events/signup.html'
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False  # Inactive until activation
        user.save()
        
        # Send activation email
        current_site = get_current_site(self.request)
        subject = 'Activate Your Account'
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_link = self.request.build_absolute_uri(
            reverse('activate', kwargs={'uidb64': uid, 'token': token})
        )
        message = render_to_string('events/activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'activation_link': activation_link,
        })
        user.email_user(subject, message)
        
        messages.success(self.request, "Account created! Check your email to activate your account.")
        return redirect('login')

def activate_account(request, uidb64, token):
    """
    Activates the user account if the provided token is valid.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated! You can now log in.")
        return redirect('login')
    else:
        return render(request, 'events/activation_invalid.html')

def login_view(request):
    """
    Logs a user in if their credentials are valid and the account is active.
    - If user is superuser, they are placed in the Admin group (only).
    - If user is not superuser and has no role, they are assigned to Participant.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and user.is_active:
            if user.is_superuser:
                # Clear all groups and add user to Admin group
                user.groups.clear()
                admin_group, _ = Group.objects.get_or_create(name='Admin')
                user.groups.add(admin_group)
                login(request, user)
                return redirect('admin_dashboard')
            else:
                # If user not admin, check if they have no group
                if not (is_organizer(user) or is_participant(user)):
                    participant_group, _ = Group.objects.get_or_create(name='Participant')
                    user.groups.add(participant_group)
                login(request, user)
                if is_admin(user):
                    return redirect('admin_dashboard')
                elif is_organizer(user):
                    return redirect('organizer_dashboard')
                else:
                    return redirect('participant_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'events/login.html')

def logout_view(request):
    """
    Logs the user out and redirects to the login page.
    """
    logout(request)
    return redirect('login')

# --------------------------------------------------
# 🔹 Dashboard Views
# --------------------------------------------------

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Displays all users, events, and groups for admin users.
    """
    model = CustomUser
    template_name = 'events/dashboard_admin.html'
    context_object_name = 'users'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, "You do not have admin privileges.")
        return redirect('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events'] = Event.objects.all()
        context['groups'] = Group.objects.all()
        return context

@login_required
def organizer_dashboard(request):
    """
    Displays the organizer dashboard.
    Organizer now sees ALL events (like admin).
    """
    if not is_organizer(request.user):
        messages.error(request, "You do not have organizer privileges.")
        return redirect('login')
    
    events = Event.objects.all()  # Show all events
    return render(request, 'events/dashboard_organizer.html', {'events': events})

@login_required
def participant_dashboard(request):
    """
    Displays the participant dashboard for users in the 'Participant' group,
    showing the events they've RSVP'd to.
    """
    if not is_participant(request.user):
        messages.error(request, "You do not have participant privileges.")
        return redirect('login')
    
    rsvped_events = request.user.rsvped_events.all()
    return render(request, 'events/dashboard_participant.html', {
        'rsvped_events': rsvped_events,
    })

# --------------------------------------------------
# 🔹 Event Management Views
# --------------------------------------------------

class EventListView(ListView):
    """
    Lists all events on the home page.
    """
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'

class EventDetailView(DetailView):
    """
    Shows details for a specific event, including who has RSVP'd.
    """
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rsvp_users'] = self.object.rsvps.all()
        return context

class EventCreateView(LoginRequiredMixin, CreateView):
    """
    Creates a new event. Uses get_absolute_url from the Event model for redirection.
    """
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'

class EventUpdateView(LoginRequiredMixin, UpdateView):
    """
    Updates an existing event.
    """
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'

class EventDeleteView(LoginRequiredMixin, DeleteView):
    """
    Deletes an existing event and redirects to the event list.
    """
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('event_list')

# --------------------------------------------------
# 🔹 RSVP View
# --------------------------------------------------

@login_required
def rsvp_event(request, pk):
    """
    Allows a logged-in user to RSVP for an event.
    """
    event = get_object_or_404(Event, pk=pk)
    user = CustomUser.objects.get(pk=request.user.pk)
    event.rsvps.add(user)
    messages.success(request, "You have successfully RSVPed to the event!")
    return redirect('event_detail', pk=event.pk)

# --------------------------------------------------
# 🔹 Profile Management
# --------------------------------------------------

class ProfileView(LoginRequiredMixin, DetailView):
    """
    Displays the currently logged-in user's profile.
    """
    model = CustomUser
    template_name = 'events/profile.html'
    context_object_name = 'user_obj'
    
    def get_object(self, queryset=None):
        return self.request.user

class EditProfileView(LoginRequiredMixin, UpdateView):
    """
    Allows a user to edit their profile.
    """
    model = CustomUser
    form_class = EditProfileForm
    template_name = 'events/edit_profile.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)

class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    """
    Allows a user to change their password.
    """
    template_name = 'events/change_password.html'
    success_url = reverse_lazy('profile')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Password changed successfully!")
        return response

# --------------------------------------------------
# 🔹 Group Management
# --------------------------------------------------

def create_group(request):
    """
    Creates a new group (Admin only).
    """
    if not is_admin(request.user):
        messages.error(request, "You do not have permission to create a group.")
        return redirect('admin_dashboard')
    
    if request.method == "POST":
        group_name = request.POST.get('group_name')
        if group_name:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                messages.success(request, f"Group '{group_name}' created successfully!")
            else:
                messages.info(request, f"Group '{group_name}' already exists.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Group name is required.")
    
    return render(request, 'events/create_group.html')

class GroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Deletes a group (Admin only).
    """
    model = Group
    template_name = 'events/group_confirm_delete.html'
    success_url = reverse_lazy('admin_dashboard')
    
    def test_func(self):
        return is_admin(self.request.user)

class GroupDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Displays group details, including members (Admin only).
    """
    model = Group
    template_name = 'events/group_detail.html'
    context_object_name = 'group'
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['members'] = self.object.user_set.all()
        return context

# --------------------------------------------------
# 🔹 User Role & Management
# --------------------------------------------------

def change_user_role(request, user_id, role):
    """
    Changes the role of a user (to 'organizer' or 'participant'), Admin only.
    """
    if not is_admin(request.user):
        messages.error(request, "You do not have permission to change user roles.")
        return redirect('admin_dashboard')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    valid_roles = ['organizer', 'participant']
    if role.lower() not in valid_roles:
        messages.error(request, "Invalid role specified.")
        return redirect('admin_dashboard')
    
    # Prevent user from changing their own role
    if user.id == request.user.id:
        messages.error(request, "You cannot change your own role.")
        return redirect('admin_dashboard')
    
    user.groups.clear()
    group_name = role.capitalize()
    group, created = Group.objects.get_or_create(name=group_name)
    if created:
        messages.info(request, f"Group '{group_name}' was automatically created.")
    
    user.groups.add(group)
    messages.success(request, f"User {user.username}'s role changed to {group_name}.")
    return redirect('admin_dashboard')

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Deletes a user account (Admin only).
    """
    model = CustomUser
    template_name = 'events/delete_user_confirm.html'
    success_url = reverse_lazy('admin_dashboard')
    
    def test_func(self):
        obj = self.get_object()
        return is_admin(self.request.user) and obj.id != self.request.user.id
