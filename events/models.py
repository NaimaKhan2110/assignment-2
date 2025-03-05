from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth.models import AbstractUser
from django.urls import reverse

class CustomUser(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pics/', default='default_profile.jpg')
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.username

class Event(models.Model):
    CATEGORY_CHOICES = (
        ('music', 'Music'),
        ('sports', 'Sports'),
        ('tech', 'Technology'),
        ('art', 'Art'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()  # Event date
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='music'
    )
    image = models.ImageField(upload_to='event_images/', default='default_event.jpg')
    rsvps = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='rsvped_events',
        blank=True
    )
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='events_created',
        null=True,
        blank=True
    )
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # Redirect to the event detail page after creating/updating an event
        return reverse('event_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Event, self).save(*args, **kwargs)
