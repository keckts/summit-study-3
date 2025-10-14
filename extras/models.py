from django.db import models
from myapp.models import CustomUser as User
from myapp.models import BaseTest, FlashcardSet, PracticeTest, WritingTask
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Achievement(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100)
    required_level = models.IntegerField(default=1)

    def __str__(self):
        return self.title

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    date_earned = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "achievement")

class Program(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    subject = models.TextField(blank=True, default="General")
    icon = models.CharField(max_length=100, blank=True)

    def get_duration(self):
        return self.weeks.count()

    def __str__(self):
        return self.title


class ProgramWeek(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='weeks')
    week_number = models.PositiveIntegerField()
    title = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    tips = models.TextField(blank=True)

    class Meta:
        unique_together = ('program', 'week_number')    


class Activity(models.Model):
    week = models.ForeignKey(ProgramWeek, on_delete=models.CASCADE, related_name='activities')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()  # this replaces content_id
    content_object = GenericForeignKey('content_type', 'object_id')
