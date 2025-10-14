from django.db import models
import uuid
from accounts.models import CustomUser

class BaseTest(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=300, blank=True)
    subject = models.CharField(max_length=100, blank=True, null=True, default='General')
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    duration = models.IntegerField(help_text="Duration in minutes", default=30, blank=True, null=True)
    is_public = models.BooleanField(default=True)
    difficulty = models.CharField(max_length=50, blank=True, null=True)  # e.g., Easy, Medium, Hard

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return self.title
    
    class Meta:
        abstract = True


class PracticeTest(BaseTest): # add an auto add questions field
    pass

QUESTION_TYPES = (
    ('mcq', 'Multiple Choice'),
    ('text', 'Short Answer'), # make it so it handles spelling errors or up to 60-70% of answer
    ('tf', 'True/False'),
)

class Question(models.Model):
    practice_test = models.ForeignKey(PracticeTest, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='mcq')
    subject = models.CharField(max_length=100, blank=True, null=True, default='General')

    answer = models.CharField(max_length=200, blank=True, null=True)  # Correct answer for text types
    explanation = models.TextField(blank=True, null=True, max_length=5000)  # Optional explanation field

    def __str__(self):
        return self.text[:50]  # Display first 50 characters of the question text

class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

# -------------------------------Writing Tasks-----------------------------------------

class WritingTask(BaseTest):
    prompt = models.TextField(max_length=5000)
    grading_level = models.CharField(max_length=50, blank=True, null=True)  # e.g., Easy, strict, advanced

    min_word_count = models.IntegerField(default=250, blank=True, null=True)
    max_word_count = models.IntegerField(default=1000, blank=True, null=True)

    def __str__(self):
        return self.title

# -------------------------------Test Results-----------------------------------------

class TestResult(models.Model):
    owner = models.ForeignKey(
        CustomUser,
        related_name="%(class)s_results",
        on_delete=models.CASCADE,
        null=True, # DELETE LATER
        blank=True  # DELETE LATER
    )

    score = models.FloatField()
    taken_at = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


    def __str__(self):
        return f"{self.owner.email} - {self.score}"

    class Meta:
        abstract = True

class PracticeTestResult(TestResult):
    practice_test = models.ForeignKey(PracticeTest, on_delete=models.CASCADE)

class WritingTaskResult(TestResult):
    writing_task = models.ForeignKey(WritingTask, on_delete=models.CASCADE)
    content = models.TextField(max_length=10000, blank=True, null=True)  # User's written content
    feedback = models.TextField(max_length=5000, blank=True, null=True)  # Feedback from AI or human grader

# --------------------------------Flashcards------------------------------------------

class FlashcardSet(BaseTest):
    pass
    
class Flashcard(models.Model):
    flashcard_set = models.ForeignKey(FlashcardSet, related_name='flashcards', on_delete=models.CASCADE)
    front = models.TextField(max_length=1000)
    back = models.TextField(max_length=1000)

    def __str__(self):
        return self.front

class FlashcardSetProgress(models.Model): # track progress of flashcard sets (will delete data after completion)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE)
    current_index = models.IntegerField(default=0)  # index of the current flashcard
    known = models.IntegerField(default=0)  # number of flashcards marked as known
    not_known = models.IntegerField(default=0)  # number of flashcards marked as not known
    completed = models.BooleanField(default=False)
    last_reviewed = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"{self.owner.email} - {self.flashcard_set.title} - {self.current_index}"