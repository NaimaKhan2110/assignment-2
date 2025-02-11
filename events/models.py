from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Event(models.Model):
    CATEGORY_CHOICES = (
        ('music', 'Music'),
        ('sports', 'Sports'),
        ('tech', 'Technology'),
        ('art', 'Art'),
    )

    # Event fields
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()  # Event date
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='music'  # Default value for the category
    )
    image = models.ImageField(upload_to='event_images/', default='default_event.jpg')
    rsvps = models.ManyToManyField(User, related_name='rsvped_events', blank=True)
    
    # Updated organizer field to be optional:
    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='events_created',
        null=True,      # Allow NULL in the database
        blank=True      # Allow the field to be blank in forms
    )
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.title

    # Override save method to auto-generate slug
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Event, self).save(*args, **kwargs)
