from django import forms
from django.forms import inlineformset_factory
from django.contrib.contenttypes.models import ContentType
from .models import Program, ProgramWeek, Activity
import random

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ["title", "description", "subject", "icon"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default test values
        random_number = random.randint(1000, 9999)
        
        self.fields["title"].initial = f"Test Program {random_number}"
        self.fields["description"].initial = "This is a sample program description for testing."
        self.fields["subject"].initial = "Science"
        self.fields["icon"].initial = "fa-solid fa-graduation-cap"


class ProgramWeekForm(forms.ModelForm):
    class Meta:
        model = ProgramWeek
        fields = ["week_number", "title", "notes", "tips"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make week_number optional for easier form handling
        self.fields["week_number"].required = False

        # Default test values
        self.fields["week_number"].initial = 1
        self.fields["title"].initial = "Week 1: Introduction"
        self.fields["notes"].initial = "These are example notes for testing."
        self.fields["tips"].initial = "Remember to review the material before the session."



class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["content_type"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit the selectable content types to specific models
        self.fields["content_type"].queryset = ContentType.objects.filter(
            model__in=[
                "basetest",
                "flashcardset",
                "practicetest",
                "writingtask",
            ]
        )
        # Add help text
        self.fields["content_type"].label = "Activity Type"


# Inline formsets
ProgramWeekFormSet = inlineformset_factory(
    Program,
    ProgramWeek,
    form=ProgramWeekForm,
    extra=1,
    can_delete=True,
)

ActivityFormSet = inlineformset_factory(
    ProgramWeek,
    Activity,
    form=ActivityForm,
    extra=1,
    can_delete=True,
)