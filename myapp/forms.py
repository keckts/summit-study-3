from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms import inlineformset_factory
from .models import Flashcard, FlashcardSet, PracticeTest, Question, Option, WritingTask, WritingTaskResult, PracticeTestResult, FlashcardSetProgress
from accounts.models import CustomUser



# ------------------------ Test Forms ----------------------------

BASE_TEST_FIELDS = ['title', 'description', 'subject', 'duration', 'difficulty', 'is_public']

class BaseTestForm(forms.ModelForm):

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('ultra-hard', 'Ultra Hard'),
    ] 

    SUBJECT_CHOICES = [ # add more later
        ('Math', 'Math'),
        ('Science', 'Science'),
        ('History', 'History'),
        ('Language', 'Language'),
        ('General', 'General'),
    ]

    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    subject = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Math, Science'})
    )
     
    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    duration = forms.IntegerField(
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1})
    )

    is_public = forms.BooleanField(
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


    class Meta:
        abstract = True



from django import forms
from django.forms import inlineformset_factory
from .models import PracticeTest, Question, Option

class PracticeTestForm(BaseTestForm):
    class Meta:
        model = PracticeTest
        fields = BASE_TEST_FIELDS


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "question_type", "answer", "explanation"]

    # Use the model choices if available
    try:
        QUESTION_TYPE_CHOICES = Question._meta.get_field('question_type').choices
    except Exception:
        QUESTION_TYPE_CHOICES = [
            ('SA', 'Short answer'),
            ('MCQ', 'Multiple choice'),
            ('TF', 'True / False'),
        ]

    # Make short answer the default (value 'SA' must match your model choice key)
    question_type = forms.ChoiceField(
        choices=QUESTION_TYPE_CHOICES,
        initial=QUESTION_TYPE_CHOICES[0][0],
        widget=forms.Select(attrs={'class': 'form-select question-type'})
    )

    text = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 1}))
    explanation = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 1}))


    
class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ["text", "is_correct"]

    text = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option text'}))

# formsets
QuestionFormSet = inlineformset_factory(
    PracticeTest, Question, form=QuestionForm,
    fields=["text", "question_type", "answer", "explanation"],
    extra=0, can_delete=True
)

# provide 4 default option rows for MCQ questions
OptionFormSet = inlineformset_factory(
    Question, Option, form=OptionForm,
    fields=["text", "is_correct"], extra=4, can_delete=True
)

# ------------------------Writing Task forms ----------------------------

class WritingTaskForm(BaseTestForm):
    class Meta:
        model = WritingTask
        fields = BASE_TEST_FIELDS + ["prompt", "grading_level", "min_word_count", "max_word_count"]

    GRADING_LEVEL_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
        ('Strict', 'Strict'),
        ('Expert', 'Expert'),
    ]

    grading_level = forms.ChoiceField(
        choices=GRADING_LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    min_word_count = forms.IntegerField(
        initial=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'value': 100, 'min': 1 })
    )

    max_word_count = forms.IntegerField(
        initial=1000,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'value': 1000, 'min': 100 })
    )

class WritingTaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = WritingTaskResult
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Write your essay here...'
            })
        }



# ------------------------------------------------ Flashcards ----------------------------
# Note: do not confuse flashcard set with flashcard

class FlashcardSetForm(forms.ModelForm):
    class Meta:
        model = FlashcardSet
        fields = ['title', 'description', 'subject'] 

class FlashcardForm(forms.ModelForm):
    class Meta:
        model = Flashcard
        fields = ["front", "back"]

    front = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    back = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

FlashcardFormSet = inlineformset_factory(
    FlashcardSet, Flashcard, form=FlashcardForm,
    fields=["front", "back"], extra=1, can_delete=True
)
    

class FlashcardSetProgressForm(forms.ModelForm):
    class Meta:
        model = FlashcardSetProgress
        fields = ['current_index']
        widgets = {
            'current_index': forms.HiddenInput()
        }