from django.shortcuts import render, redirect
from .models import Achievement, UserAchievement
import math
from .models import Program
from django.contrib.auth.decorators import login_required
from myapp.utils import ai_chat_response
from extras.models import Achievement, UserAchievement
from django.views.decorators.csrf import csrf_exempt

def achievements(request):
    user = request.user
    user_level = math.floor(user.points / 1000) or 0

    # Get all achievements
    achievements = Achievement.objects.all()

    # Optional: if you track which achievements the user has unlocked
    user_achievements = set(UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True))

    print(f'user: {user}, level: {user_level}, achievements: {user_achievements}')

    # Annotate each achievement with unlocked boolean
    for ach in achievements:
        # Unlocked if user has enough points OR already has it in UserAchievement
        ach.unlocked = user_level >= ach.required_level or ach.id in user_achievements

    # Calculate level and progress toward next level
    progress = (user.points % 1000) / 1000 * 100  # percentage

    context = {
        'achievements': achievements,
        'points': user.points,
        'level': user_level,
        'progress': progress,
    }

    return render(request, 'extras/achievements.html', context)

def programs(request):
    program_objects = Program.objects.all()
    return render(request, 'extras/programs/programs.html', {
        'programs': program_objects,
    })



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Program, ProgramWeek, Activity
from .forms import ProgramForm, ProgramWeekFormSet, ActivityFormSet


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Program, ProgramWeek, Activity
from .forms import ProgramForm, ProgramWeekFormSet, ActivityFormSet

@login_required
def program_form_view(request, pk=None):
    """Create or edit a Program with nested Weeks and Activities."""
    editing = bool(pk)
    program = get_object_or_404(Program, pk=pk) if editing else None

    if request.method == "POST":
        # Main formsets
        program_form = ProgramForm(request.POST, request.FILES, instance=program)
        week_formset = ProgramWeekFormSet(request.POST, request.FILES, instance=program)

        # Prepare nested activity formsets
        activity_formsets = []
        for i, wform in enumerate(week_formset.forms):
            week_instance = wform.instance if wform.instance.pk else None
            prefix = f"activities-{i}"
            a_formset = ActivityFormSet(request.POST, request.FILES, instance=week_instance, prefix=prefix)
            activity_formsets.append(a_formset)

        # Validate everything before saving
        all_valid = (
            program_form.is_valid()
            and week_formset.is_valid()
            and all(a.is_valid() for a in activity_formsets)
        )

        if all_valid:
            # Save main program
            program = program_form.save()
            week_formset.instance = program
            weeks = week_formset.save(commit=False)

            # Save each week and its activities
            for i, wform in enumerate(week_formset.forms):
                if not wform.cleaned_data or wform.cleaned_data.get("DELETE", False):
                    continue

                week = wform.save(commit=False)
                week.program = program
                week.save()

                a_formset = activity_formsets[i]
                a_formset.instance = week
                activities = a_formset.save(commit=False)
                for activity in activities:
                    activity.week = week
                    activity.save()

                # Handle deleted activities
                for obj in a_formset.deleted_objects:
                    obj.delete()

            # Handle deleted weeks
            for obj in week_formset.deleted_objects:
                obj.delete()

            messages.success(request, "✅ Program saved successfully!")
            return redirect("extras:programs")

        else:
            messages.error(request, "⚠️ Please correct the errors below.")
            # Reattach activity formsets for re-rendering
            for i, wform in enumerate(week_formset.forms):
                wform.activity_formset = activity_formsets[i]

    else:
        # GET request – prefill forms for editing or empty for new
        program_form = ProgramForm(instance=program)
        week_formset = ProgramWeekFormSet(instance=program)

        # Attach nested activity formsets to each week form
        for i, wform in enumerate(week_formset.forms):
            week_instance = wform.instance if wform.instance.pk else None
            prefix = f"activities-{i}"
            wform.activity_formset = ActivityFormSet(instance=week_instance, prefix=prefix)

    return render(
        request,
        "extras/programs/program_form.html",
        {
            "program_form": program_form,
            "week_formset": week_formset,
            "editing": editing,
        },
    )


@login_required
@csrf_exempt
def chatbot(request):
    user = request.user
    ai_response = None
    error = None

    if user.ai_credits < 1000:  # threshold check
        error = "You need at least 1000 AI credits to use the chatbot."
        return render(request, "extras/chatbot.html", {"error": error})

    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()
        if prompt:
           ai_response = ai_chat_response(prompt, "You are a helpful assistant who generates text responses to prompts.", user, "gpt-4o", "text") 

        

    return render(request, "extras/chatbot.html", {
        "ai_response": ai_response,
        "error": error,
    })
