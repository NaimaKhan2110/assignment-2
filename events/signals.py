from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from .models import Event

# Signal to send an account activation email when a new user is created.
@receiver(post_save, sender=User)
def send_activation_email(sender, instance, created, **kwargs):
    if created and not instance.is_active:
        uid = urlsafe_base64_encode(force_bytes(instance.pk))
        token = default_token_generator.make_token(instance)
        activation_link = f"http://localhost:8000/activate/{uid}/{token}/"
        subject = "Activate Your Account"
        message = (
            f"Hi {instance.username},\n\n"
            f"Please activate your account by clicking the link below:\n{activation_link}\n\n"
            "Thank you!"
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [instance.email]
        send_mail(subject, message, from_email, recipient_list)

# Signal to send an RSVP confirmation email when a user is added to an event's rsvps.
@receiver(m2m_changed, sender=Event.rsvps.through)
def send_rsvp_confirmation_email(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            try:
                user = User.objects.get(pk=user_id)
                subject = f"RSVP Confirmation for {instance.title}"
                # Format the event's date to include the exact time.
                event_time = instance.date.strftime('%Y-%m-%d %H:%M:%S')
                message = (
                    f"Hi {user.username},\n\n"
                    f"Thank you for RSVPing to the event '{instance.title}'.\n"
                    f"The event is scheduled for {event_time}.\n\n"
                    "We look forward to your participation!"
                )
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [user.email]
                send_mail(subject, message, from_email, recipient_list)
            except User.DoesNotExist:
                continue
