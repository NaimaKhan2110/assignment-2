import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.contrib import messages

from .forms import SignUpForm, EventForm
from .models import Event

# Configure logging
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Helper Functions for Role-Based Access Control
# --------------------------------------------------

def is_admin(user):
    logger.debug("Checking admin privileges for user: %s", user)
    logger.debug("User.is_superuser: %s", user.is_superuser)
    logger.debug("User groups: %s", list(user.groups.values_list('name', flat=True)))
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Admin').exists())

def is_organizer(user):
    return user.is_authenticated and user.groups.filter(name='Organizer').exists()

def is_participant(user):
    return user.is_authenticated and user.groups.filter(name='Participant').exists()

# ------------------------------
# Authentication & Account Views
# ------------------------------

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until activation
            user.save()
            # Add user to Participant group by default
            participant_group, created = Group.objects.get_or_create(name='Participant')
            user.groups.add(participant_group)
            messages.success(request, "Account created! Please check your email to activate your account.")
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'events/signup.html', {'form': form})

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated! You can now log in.")
        return redirect('login')
    else:
        return HttpResponse("Activation link is invalid!")

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if is_admin(user):
                    return redirect('admin_dashboard')
                elif is_organizer(user):
                    return redirect('organizer_dashboard')
                else:
                    return redirect('participant_dashboard')
            else:
                messages.error(request, "Account inactive. Please activate your account via email.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'events/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# ------------------------------
# Dashboard Views
# ------------------------------

@login_required(login_url='/login/')
def admin_dashboard(request):
    # Debug prints to verify the logged-in user's details.
    print("DEBUG: Admin Dashboard accessed by user:", request.user)
    print("DEBUG: is_authenticated =", request.user.is_authenticated)
    print("DEBUG: is_superuser =", request.user.is_superuser)
    print("DEBUG: Groups =", list(request.user.groups.values_list('name', flat=True)))

    if not (request.user.is_superuser or request.user.groups.filter(name='Admin').exists()):
        messages.error(request, "You do not have admin privileges.")
        return redirect('login')
    events = Event.objects.all()
    users = User.objects.all()
    groups = Group.objects.all()  # Pass all groups for admin management
    context = {'events': events, 'users': users, 'groups': groups}
    return render(request, 'events/dashboard_admin.html', context)

@login_required(login_url='/login/')
def organizer_dashboard(request):
    if not is_organizer(request.user):
        messages.error(request, "You do not have organizer privileges.")
        return redirect('login')
    events = Event.objects.all()
    context = {'events': events}
    return render(request, 'events/dashboard_organizer.html', context)

@login_required(login_url='/login/')
def participant_dashboard(request):
    if not is_participant(request.user):
        messages.error(request, "You do not have participant privileges.")
        return redirect('login')
    events = request.user.rsvped_events.all()
    context = {'events': events}
    return render(request, 'events/dashboard_participant.html', context)

# ------------------------------
# Event Views
# ------------------------------

def event_list(request):
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events': events})

def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    # Get all users who RSVP'd to the event
    rsvp_users = event.rsvps.all()
    return render(request, 'events/event_detail.html', {
        'event': event,
        'rsvp_users': rsvp_users,
    })

@login_required(login_url='/login/')
def event_create(request):
    if not is_organizer(request.user):
        messages.error(request, "You do not have organizer privileges.")
        return redirect('login')
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            messages.success(request, "Event created successfully!")
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm()
    return render(request, 'events/event_form.html', {'form': form})

@login_required(login_url='/login/')
def event_edit(request, event_id):
    # Allow editing if the user is an organizer OR an admin.
    if not (is_organizer(request.user) or is_admin(request.user)):
        messages.error(request, "You do not have permission to edit events.")
        return redirect('login')
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, "Event updated successfully!")
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    return render(request, 'events/event_form.html', {'form': form, 'event': event})

@login_required(login_url='/login/')
def event_delete(request, event_id):
    # Allow deletion if the user is an admin or an organizer.
    if not (is_admin(request.user) or is_organizer(request.user)):
        messages.error(request, "You do not have permission to delete events.")
        return redirect('login')
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        event.delete()
        messages.success(request, "Event deleted successfully!")
        return redirect('event_list')
    return render(request, 'events/event_confirm_delete.html', {'event': event})

@login_required(login_url='/login/')
def rsvp_event(request, event_id):
    if not is_participant(request.user):
        messages.error(request, "You do not have participant privileges.")
        return redirect('login')
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        if request.user in event.rsvps.all():
            messages.info(request, "You have already RSVP'd to this event.")
        else:
            event.rsvps.add(request.user)
            messages.success(request, "RSVP successful! A confirmation email has been sent.")
    return redirect('event_detail', event_id=event.id)

# ------------------------------
# Admin-Only Operations
# ------------------------------

@login_required(login_url='/login/')
def change_user_role(request, user_id):
    if not is_admin(request.user):
        messages.error(request, "You do not have permission to change roles.")
        return redirect('admin_dashboard')
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        new_role = request.POST.get('role')  # Expected values: "Admin", "Organizer", "Participant"
        if new_role not in ['Admin', 'Organizer', 'Participant']:
            messages.error(request, "Invalid role specified.")
            return redirect('admin_dashboard')
        user.groups.clear()
        group, created = Group.objects.get_or_create(name=new_role)
        user.groups.add(group)
        messages.success(request, f"User {user.username}'s role updated to {new_role}!")
        return redirect('admin_dashboard')
    return render(request, 'events/change_user_role.html', {'user': user})

@login_required(login_url='/login/')
def create_group(request):
    if not is_admin(request.user):
        messages.error(request, "You do not have permission to create groups.")
        return redirect('admin_dashboard')
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        if not group_name:
            messages.error(request, "Group name cannot be empty.")
        else:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                messages.success(request, f"Group '{group_name}' created successfully!")
            else:
                messages.info(request, f"Group '{group_name}' already exists.")
            return redirect('admin_dashboard')
    return render(request, 'events/create_group.html')

@login_required(login_url='/login/')
def delete_group(request, group_id):
    if not is_admin(request.user):
        messages.error(request, "You do not have permission to delete groups.")
        return redirect('admin_dashboard')
    group = get_object_or_404(Group, pk=group_id)
    if request.method == 'POST':
        group.delete()
        messages.success(request, f"Group '{group.name}' deleted successfully!")
        return redirect('admin_dashboard')
    return render(request, 'events/confirm_delete_group.html', {'group': group})

@login_required(login_url='/login/')
def delete_participant(request, user_id):
    if not is_admin(request.user):
        messages.error(request, "You do not have permission to delete participants.")
        return redirect('admin_dashboard')
    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser or user.groups.filter(name__in=['Admin', 'Organizer']).exists():
        messages.error(request, "Cannot delete an admin or organizer account.")
        return redirect('admin_dashboard')
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"Participant {user.username} deleted successfully!")
        return redirect('admin_dashboard')
    return render(request, 'events/confirm_delete_participant.html', {'user': user})
