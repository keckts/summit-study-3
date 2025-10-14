from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from .models import Question, PracticeTest
from django.forms.models import model_to_dict

app_models = apps.get_app_config('myapp').get_models()

# Only register models that are NOT Question or PracticeTest
for model in app_models:
    if model in [Question, PracticeTest]:
        continue
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass

class PracticeTestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner')

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'practice_test_id')  # show practice_test id

    def practice_test_id(self, obj):
        return obj.practice_test.id
    practice_test_id.short_description = 'Practice Test ID'

admin.site.register(Question, QuestionAdmin)
admin.site.register(PracticeTest, PracticeTestAdmin)