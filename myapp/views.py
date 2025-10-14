"""
Refactored views.py following DRY principles
- Extracted common patterns into reusable mixins/decorators
- Consolidated form processing logic
- Reduced code duplication
- Maintained all existing functionality
"""

import json
import logging
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.safestring import mark_safe
from accounts.subscriptions import get_subscription_features
from django.utils.timezone import now, timedelta
from django.utils import timezone
from collections import Counter

from myapp.models import PracticeTestResult, WritingTaskResult, FlashcardSetProgress

from .forms import (
    PracticeTestForm, QuestionFormSet, OptionFormSet,
    WritingTaskForm, WritingTaskSubmissionForm,
    FlashcardSetForm, FlashcardFormSet,
)
from .models import (
    PracticeTest, Question, Option, PracticeTestResult,
    WritingTask, WritingTaskResult,
    FlashcardSet, Flashcard, FlashcardSetProgress,
)
from .utils import (
    ai_chat_response, calculate_points, is_similar_answer,
    decode_uploaded_file, generate_activity, save_activity_from_json,
    deduct_credits,
)

logger = logging.getLogger(__name__)


# ======================== HELPER UTILITIES ========================

def get_owned_object_or_404(model, pk: int, user):
    """Get object by pk ensuring ownership, raise 404 otherwise."""
    try:
        return get_object_or_404(model, pk=pk, owner=user)
    except Http404:
        logger.warning(f"User {user} tried to access {model.__name__} {pk} they don't own")
        raise


def award_points(user, activity, score: int):
    """Award points to user based on activity and score."""
    points = calculate_points(activity, score)
    user.points = (getattr(user, "points", 0) or 0) + points
    user.save(update_fields=["points"])
    return points


def parse_json_body(request: HttpRequest) -> Dict:
    """Parse JSON from request body, return empty dict on error."""
    try:
        return json.loads(request.body)
    except Exception as e:
        logger.warning(f"Failed to parse JSON body: {e}")
        return {}



def get_dashboard_progress_data(user):
    """Return summarized progress data for the dashboard."""
    practice_results = PracticeTestResult.objects.filter(owner=user)
    writing_results = WritingTaskResult.objects.filter(owner=user)
    flashcard_progress = FlashcardSetProgress.objects.filter(owner=user)

    # --- Totals ---
    total_practice = practice_results.count()
    total_writing = writing_results.count()
    total_flashcards = flashcard_progress.count()

    # --- Recent activity (most recent 4) ---
    all_activities = []

    for r in practice_results.order_by('-taken_at')[:4]:
        all_activities.append({
            "type": "Practice Test",
            "name": getattr(r, "name", "Practice Test"),
            "date": r.taken_at,
            "score": r.score,
        })

    for r in writing_results.order_by('-taken_at')[:4]:
        all_activities.append({
            "type": "Writing Task",
            "name": getattr(r, "title", "Writing Task"),
            "date": r.taken_at,
            "score": getattr(r, "score", None),
        })

    for r in flashcard_progress.order_by('-last_reviewed')[:4]:
        all_activities.append({
            "type": "Flashcards",
            "name": getattr(r.flashcard_set, "title", "Flashcard Set"),
            "date": r.last_reviewed,
            "score": None,
        })

    # Sort combined activities by most recent
    all_activities = sorted(
        [a for a in all_activities if a["date"]],
        key=lambda x: x["date"],
        reverse=True
    )[:4]

    # --- Weekly activity ---
    one_week_ago = timezone.now() - timedelta(days=7)
    recent_activities = []

    for r in practice_results.filter(taken_at__gte=one_week_ago):
        recent_activities.append(r.taken_at.date())
    for r in writing_results.filter(taken_at__gte=one_week_ago):
        recent_activities.append(r.taken_at.date())
    for r in flashcard_progress.filter(last_reviewed__gte=one_week_ago):
        recent_activities.append(r.last_reviewed.date())

    daily_counts = Counter(recent_activities)
    weekly_progress = [
        {
            "date": (one_week_ago + timedelta(days=i)).date(),
            "count": daily_counts.get((one_week_ago + timedelta(days=i)).date(), 0),
        }
        for i in range(7)
    ]

    return {
        "total_practice": total_practice,
        "total_writing": total_writing,
        "total_flashcards": total_flashcards,
        "recent_activity": all_activities,
        "weekly_progress": weekly_progress,
    }

def create_formset_context(formset_class, prefix: str, instance=None, data=None):
    """Helper to create formset with common parameters."""
    return formset_class(data, prefix=prefix, instance=instance or formset_class.model())


# ======================== FORM PROCESSING HELPERS ========================

class FormProcessor:
    """Encapsulates common form processing patterns."""
    
    @staticmethod
    def process_with_formset(request, form_class, formset_class, 
                           form_instance=None, formset_instance=None,
                           owner_field='owner', prefix='items',
                           success_message='Saved successfully!',
                           redirect_url=None):
        """
        Generic form + formset processing.
        Returns (success: bool, context: dict)
        """
        if request.method == 'POST':
            form = form_class(request.POST, instance=form_instance)
            formset = formset_class(request.POST, prefix=prefix, instance=formset_instance)
            
            if form.is_valid() and formset.is_valid():
                with transaction.atomic():
                    obj = form.save(commit=False)
                    if owner_field:
                        setattr(obj, owner_field, request.user)
                    obj.save()
                    
                    formset.instance = obj
                    formset.save()
                
                if success_message:
                    messages.success(request, success_message)
                if redirect_url:
                    return True, {'redirect': redirect(redirect_url)}
                return True, {'instance': obj}
            else:
                messages.error(request, "Please correct the errors below.")
                return False, {'form': form, 'formset': formset}
        else:
            form = form_class(instance=form_instance)
            formset = formset_class(prefix=prefix, instance=formset_instance)
            return False, {'form': form, 'formset': formset}


# ======================== PRACTICE TEST VIEWS ========================

@login_required
def practice_tests(request: HttpRequest) -> HttpResponse:
    """List all practice tests for current user."""
    tests = PracticeTest.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "myapp/main/tests/practice_tests.html", {"tests": tests})


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction

import json
from django.utils.safestring import mark_safe
from .models import PracticeTest, Question
from .forms import PracticeTestForm, QuestionFormSet, OptionFormSet

@login_required
def practice_test_form(request, pk=None):
    """Create or edit a practice test with questions and options."""
    editing = bool(pk)
    practice_test = None
    html_questions = []

    if editing:
        practice_test = get_object_or_404(PracticeTest, pk=pk, owner=request.user)
        questions = practice_test.questions.all()
        print(f"[DEBUG] Editing PracticeTest {practice_test.id} with {questions.count()} questions")
        for question in questions:
            print(f"[DEBUG] Question {question.id} belongs to PracticeTest {question.practice_test.id}")
    else:
        questions = Question.objects.none()
        print("[DEBUG] Creating new PracticeTest")

    if request.method == "POST":
        test_form = PracticeTestForm(request.POST, instance=practice_test)
        question_formset = QuestionFormSet(
            request.POST,
            prefix="questions",
            queryset=questions
        )

        print(f"[DEBUG] Test form valid: {test_form.is_valid()}, Question formset valid: {question_formset.is_valid()}")

        if test_form.is_valid() and question_formset.is_valid():
            with transaction.atomic():
                practice_test = test_form.save(commit=False)
                practice_test.owner = request.user
                practice_test.save()
                print(f"[DEBUG] Saved PracticeTest ID: {practice_test.id}")

                for q_idx, q_form in enumerate(question_formset):
                    question = q_form.save(commit=False)
                    question.practice_test = practice_test
                    if q_form.cleaned_data.get("DELETE") and question.pk:
                        print(f"[DEBUG] Deleting Question ID: {question.id}")
                        question.delete()
                        continue
                    question.save()
                    print(f"[DEBUG] Saved Question ID: {question.id}, Type: {question.question_type}")

                    if question.question_type in ["mcq", "tf"]:
                        option_formset = OptionFormSet(
                            request.POST,
                            prefix=f"options-{q_idx}",
                            instance=question
                        )
                        if option_formset.is_valid():
                            for opt in option_formset.save(commit=False):
                                opt.question = question
                                opt.save()
                                print(f"[DEBUG] Saved Option ID: {opt.id}, Text: {opt.text}")
                            for opt in option_formset.deleted_objects:
                                print(f"[DEBUG] Deleted Option ID: {opt.id}")
                                opt.delete()
                        else:
                            print(f"[ERROR] Invalid options for Question {q_idx + 1}")
                            print(option_formset.errors)

            messages.success(request, f"Practice test {'updated' if editing else 'created'} successfully!")
            return redirect("practice_tests")
        else:
            print("[DEBUG] Validation errors found")
            print("Form errors:", test_form.errors)
            print("Formset errors:", question_formset.errors)
            for q_idx, q_form in enumerate(question_formset.forms):
                q_form.option_formset = OptionFormSet(
                    request.POST,
                    prefix=f"options-{q_idx}",
                    instance=q_form.instance if q_form.instance.pk else Question()
                )
            messages.error(request, "Please fix the errors below.")

    else:
        test_form = PracticeTestForm(instance=practice_test)
        question_formset = QuestionFormSet(prefix="questions", queryset=questions)
        for q_idx, q_form in enumerate(question_formset.forms):
            q_form.option_formset = OptionFormSet(prefix=f"options-{q_idx}", instance=q_form.instance)

    # Build html_questions for the template
    for question in questions:
        question_data = {
            "id": question.id,
            "text": question.text,
            "question_type": question.question_type,
        }
        if question.question_type in ["mcq", "tf"]:
            question_data["options"] = list(question.options.all().values("id", "text", "is_correct"))
        html_questions.append(question_data)

    # Empty option form for JS dynamic adding
    option_empty = OptionFormSet(prefix="options-__prefix__", instance=Question())

    return render(request, "myapp/main/tests/create_practice_test.html", {
        "form": test_form,
        "formset": question_formset,
        "option_empty": option_empty,
        "editing": editing,
        "practice_test": practice_test,
        "questions": questions,
        "html_questions": mark_safe(json.dumps(html_questions)),
    })


def delete_practice_test(request, pk):
    """Delete a practice test."""
    practice_test = get_object_or_404(PracticeTest, pk=pk, owner=request.user)

    if request.method == "POST":
        practice_test.delete()
        return redirect("practice_tests")

    return render(request, "myapp/main/tests/practice_tests.html")

class QuestionGrader:
    """Handles grading logic for different question types."""
    
    @staticmethod
    def grade_question(question: Question, user_answer: str) -> Tuple[bool, Optional[Dict]]:
        """
        Grade a question and return (is_correct, typo_warning).
        typo_warning is dict with similarity info if applicable.
        """
        qtype = (question.question_type or "").lower()
        user_answer = user_answer.strip()
        
        if qtype in ("mcq", "multiple choice"):
            return QuestionGrader._grade_mcq(question, user_answer)
        elif qtype in ("tf", "true/false"):
            return QuestionGrader._grade_tf(question, user_answer)
        elif qtype == "text":
            return QuestionGrader._grade_text(question, user_answer)
        
        return False, None
    
    @staticmethod
    def _grade_mcq(question: Question, user_answer: str) -> Tuple[bool, None]:
        correct_option = question.options.filter(is_correct=True).first()
        is_correct = correct_option and user_answer == str(correct_option.id)
        return is_correct, None
    
    @staticmethod
    def _grade_tf(question: Question, user_answer: str) -> Tuple[bool, None]:
        is_correct = user_answer.lower() == (question.answer or "").lower()
        return is_correct, None
    
    @staticmethod
    def _grade_text(question: Question, user_answer: str) -> Tuple[bool, Optional[Dict]]:
        if not question.answer:
            return False, None
            
        matched, similarity = is_similar_answer(question.answer, user_answer)
        typo_warning = None
        
        if matched and similarity < 100:
            typo_warning = {
                "question": question.text,
                "user_answer": user_answer,
                "correct_answer": question.answer,
                "similarity": similarity,
            }
        
        return matched, typo_warning


@login_required
def take_practice_test(request: HttpRequest, pk: int) -> HttpResponse:
    """Take and grade a practice test."""
    test = get_owned_object_or_404(PracticeTest, pk, request.user)
    questions = test.questions.prefetch_related("options").all()

    if request.method == "POST":
        total_questions = questions.count()
        correct_answers = 0
        user_answers_list = []
        potential_typos = []

        for question in questions:
            user_answer = request.POST.get(f"question_{question.id}")

            if not user_answer:
                # No answer provided — mark as incorrect
                is_correct = False
                typo_warning = None
            else:
                is_correct, typo_warning = QuestionGrader.grade_question(question, user_answer)
            
            if is_correct:
                correct_answers += 1

            if typo_warning:
                potential_typos.append(typo_warning)

            user_answers_list.append({
                "question": question,
                "user_answer": user_answer or "(no answer)",
                "is_correct": is_correct,
                "typo_warning": typo_warning,
            })

        score = round((correct_answers / total_questions) * 100) if total_questions else 0
        points = award_points(request.user, test, score)
        
        PracticeTestResult.objects.create(owner=request.user, score=score, practice_test=test)

        return render(request, "myapp/main/tests/practice_test_result.html", {
            "test": test,
            "score": score,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "user_answers_list": user_answers_list,
            "points": points,
            "potential_typos": potential_typos,
        })

    return render(request, "myapp/main/tests/take_practice_test.html", {
        "test": test,
        "questions": questions
    })


# ======================== WRITING TASK VIEWS ========================

@login_required
def writing_tasks(request: HttpRequest) -> HttpResponse:
    """List all writing tasks for current user."""
    tasks = WritingTask.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "myapp/main/writing_tasks/writing_tasks.html", {"tasks": tasks})


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import WritingTask
from .forms import WritingTaskForm


@login_required
def writing_task_form(request, pk=None):
    """
    Create, edit, or delete a writing task.
    If pk is provided → edit/delete existing task.
    Otherwise → create a new task.
    """
    if pk:
        task = get_object_or_404(WritingTask, pk=pk, owner=request.user)
    else:
        task = None

    # Handle DELETE
    if request.method == "POST" and "delete" in request.POST:
        if task:
            task.delete()
            messages.success(request, "Writing task deleted.")
        return redirect("writing_tasks")

    # Handle CREATE or EDIT
    if request.method == "POST":
        form = WritingTaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            if pk:
                messages.success(request, "Writing task updated successfully.")
            else:
                messages.success(request, "Writing task created successfully.")
            return redirect("writing_tasks")
    else:
        form = WritingTaskForm(instance=task)

    return render(
        request,
        "myapp/main/writing_tasks/create_writing_task.html",
        {"form": form, "task": task},
    )



@login_required
def take_writing_task(request: HttpRequest, pk: int) -> HttpResponse:
    """Submit an essay for a writing task."""
    task = get_owned_object_or_404(WritingTask, pk, request.user)

    if request.method == "POST":
        form = WritingTaskSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.writing_task = task
            submission.owner = request.user
            submission.score = 0
            submission.save()

            request.session["user_response"] = request.POST.get("user_response", "")
            request.session["grading_task_id"] = str(submission.pk)

            return redirect("writing_task_loading", pk=submission.pk)
    else:
        form = WritingTaskSubmissionForm()

    return render(request, "myapp/main/writing_tasks/take_writing_task.html", {
        "task": task,
        "form": form
    })


class EssayGrader:
    """Handles AI-based essay grading."""
    
    @staticmethod
    def grade_essay(task: WritingTask, content: str, user) -> Tuple[int, str]:
        """Grade essay and return (score, feedback)."""
        grading_prompt = (
            f"You are grading a student essay.\n"
            f"The essay prompt was: \"{task.prompt}\".\n"
            f"Grading strictness level: {task.grading_level}.\n\n"
            f"Essay content:\n{content}\n\n"
            "Provide JSON with: - 'score' (0–100) and - 'feedback' (detailed constructive feedback)."
        )

        response = ai_chat_response(
            grading_prompt,
            system_content="You are an essay marker.",
            user=user,
            model="gpt-4o",
            response_format="json_object",
        )

        return EssayGrader._parse_grading_response(response)
    
    @staticmethod
    def _parse_grading_response(response) -> Tuple[int, str]:
        """Parse AI response and extract score/feedback."""
        score = 0
        feedback = "AI failed to provide feedback."
        
        try:
            ai_result = response if isinstance(response, dict) else json.loads(response)
            score = int(ai_result.get("score", 0))
            feedback = str(ai_result.get("feedback", ""))
        except Exception as exc:
            logger.exception(f"Failed to parse AI grading response: {exc}")
        
        return score, feedback


@login_required
def writing_task_loading(request: HttpRequest, pk: int) -> HttpResponse:
    """Grade submitted essay using AI."""
    submission = get_owned_object_or_404(WritingTaskResult, pk, request.user)
    task = submission.writing_task
    content = request.session.pop("user_response", submission.content or "")

    score, feedback = EssayGrader.grade_essay(task, content, request.user)

    with transaction.atomic():
        submission.content = content
        submission.score = score
        submission.feedback = feedback
        submission.save()
        
        award_points(request.user, task, score)

    return redirect("writing_task_result", pk=submission.pk)


@login_required
def writing_task_result(request: HttpRequest, pk: int) -> HttpResponse:
    """Display graded essay results."""
    submission = get_owned_object_or_404(WritingTaskResult, pk, request.user)
    task = submission.writing_task

    return render(request, "myapp/main/writing_tasks/writing_task_result.html", {
        "task": task,
        "submission": submission,
        "content": submission.content,
        "score": submission.score,
        "feedback": submission.feedback,
        "points": calculate_points(task, submission.score or 0),
    })


# ======================== FLASHCARD VIEWS ========================

@login_required
def flashcard_sets(request: HttpRequest) -> HttpResponse:
    """List all flashcard sets for current user."""
    sets = FlashcardSet.objects.filter(owner=request.user)
    return render(request, "myapp/main/flashcards/flashcard_sets.html", {"sets": sets})


@login_required
def flashcard_set_form(request: HttpRequest, pk: Optional[int] = None) -> HttpResponse:
    """Create, edit, or delete a flashcard set."""
    flashcard_set = get_owned_object_or_404(FlashcardSet, pk, request.user) if pk else None

    # Handle delete
    if request.method == "POST" and "delete" in request.POST:
        if flashcard_set:
            flashcard_set.delete()
            messages.success(request, "Flashcard set deleted successfully.")
        return redirect("flashcard_sets")

    # Handle create/edit
    success, context = FormProcessor.process_with_formset(
        request,
        form_class=FlashcardSetForm,
        formset_class=FlashcardFormSet,
        form_instance=flashcard_set,
        formset_instance=flashcard_set,
        success_message="Flashcard set saved successfully!",
        redirect_url="flashcard_sets",
    )

    # Redirect if successful
    if success and "redirect" in context:
        return context["redirect"]

    return render(request, "myapp/main/flashcards/flashcard_set_form.html", {
        "set_form": context.get("form"),
        "formset": context.get("formset"),
        "flashcard_set": flashcard_set,
    })



@login_required
def take_flashcard_set(request, set_id):
    """Display flashcard set for studying."""
    flashcard_set = get_owned_object_or_404(FlashcardSet, set_id, request.user)
    flashcards = list(flashcard_set.flashcards.all().values("front", "back"))

    return render(request, "myapp/main/flashcards/take_flashcard_set.html", {
        "flashcard_set": flashcard_set,
        "flashcards_json": mark_safe(json.dumps(flashcards))
    })


class FlashcardManager:
    """Manages flashcard session state and progress."""
    
    @staticmethod
    def save_session_summary(request, known: int, not_known: int, total: int):
        """Save flashcard summary to session."""
        request.session["flashcard_summary"] = {
            "known": known,
            "not_known": not_known,
            "total": total
        }
    
    @staticmethod
    def get_session_summary(request) -> Optional[Dict]:
        """Retrieve flashcard summary from session."""
        return request.session.pop("flashcard_summary", None)
    
    @staticmethod
    def reset_progress(request, flashcard_set, mode: str):
        """Reset flashcard progress for a set."""
        FlashcardSetProgress.objects.filter(
            user=request.user,
            flashcard_set=flashcard_set
        ).delete()
        
        if "flashcard_summary" in request.session:
            del request.session["flashcard_summary"]
        
        if mode == "study":
            FlashcardSetProgress.objects.create(
                user=request.user,
                flashcard_set=flashcard_set,
                current_index=0,
                known=0,
                not_known=0,
            )


@login_required
@require_http_methods(["POST"])
def answer_flashcard_ajax(request: HttpRequest, set_id: int) -> JsonResponse:
    """Handle flashcard answer submission via AJAX."""
    flashcard_set = get_owned_object_or_404(FlashcardSet, set_id, request.user)
    data = parse_json_body(request)
    
    if not data:
        return JsonResponse({"error": "Invalid request"}, status=400)
    
    try:
        known = int(data.get("known", 0))
        not_known = int(data.get("not_known", 0))
        total = int(data.get("total", 0))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid data format"}, status=400)
    
    FlashcardManager.save_session_summary(request, known, not_known, total)
    return JsonResponse({"completed": True, "known": known, "not_known": not_known, "total": total})


@login_required
@require_http_methods(["POST"])
def flashcard_nav_ajax(request: HttpRequest, set_id: int) -> JsonResponse:
    """Handle flashcard navigation via AJAX."""
    flashcard_set = get_owned_object_or_404(FlashcardSet, set_id, request.user)
    flashcards = list(flashcard_set.flashcards.all())
    data = parse_json_body(request)
    
    if not data:
        return JsonResponse({"error": "Invalid request body"}, status=400)
    
    try:
        direction = data.get("direction")
        current_index = int(data.get("current_index", 0))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid data format"}, status=400)
    
    if direction == "next":
        current_index = min(current_index + 1, len(flashcards) - 1)
    elif direction == "prev":
        current_index = max(current_index - 1, 0)
    
    card = flashcards[current_index]
    
    return JsonResponse({
        "current_index": current_index,
        "card": {"front": card.front, "back": card.back},
        "total": len(flashcards),
    })


@login_required
@require_http_methods(["POST"])
def reset_flashcards_ajax(request: HttpRequest, set_id: int) -> JsonResponse:
    """Reset flashcard progress via AJAX."""
    flashcard_set = get_owned_object_or_404(FlashcardSet, set_id, request.user)
    data = parse_json_body(request)
    
    if not data:
        return JsonResponse({"error": "Invalid request body"}, status=400)
    
    mode = data.get("mode", "regular")
    FlashcardManager.reset_progress(request, flashcard_set, mode)
    
    return JsonResponse({"ok": True, "mode": mode})


@login_required
def answer_flashcard(request: HttpRequest, set_id: int, action: str) -> HttpResponse:
    """Non-AJAX fallback for answering flashcards."""
    flashcard_set = get_owned_object_or_404(FlashcardSet, set_id, request.user)
    progress = get_object_or_404(FlashcardSetProgress, user=request.user, flashcard_set=flashcard_set)

    if action == "known":
        progress.known += 1
    elif action == "not_known":
        progress.not_known += 1

    progress.current_index += 1
    flashcards = list(flashcard_set.flashcards.all())

    if progress.current_index >= len(flashcards):
        FlashcardManager.save_session_summary(
            request,
            progress.known,
            progress.not_known,
            len(flashcards)
        )
        progress.delete()
        return redirect("flashcard_summary", set_id=set_id)

    progress.save()
    return redirect("take_flashcard_set", set_id=set_id)


@login_required
def flashcard_summary(request: HttpRequest, set_id: int) -> HttpResponse:
    """Display flashcard session summary."""
    flashcard_set = get_owned_object_or_404(FlashcardSet, set_id, request.user)
    summary = FlashcardManager.get_session_summary(request)

    if not summary:
        try:
            progress = FlashcardSetProgress.objects.get(
                user=request.user,
                flashcard_set=flashcard_set
            )
            total = progress.known + progress.not_known
            summary = {"known": progress.known, "not_known": progress.not_known, "total": total}
        except FlashcardSetProgress.DoesNotExist:
            summary = {"known": 0, "not_known": 0, "total": 0}

    # Calculate percentages
    if summary["total"]:
        summary["known_percent"] = (summary["known"] / summary["total"]) * 100
        summary["not_known_percent"] = (summary["not_known"] / summary["total"]) * 100
    else:
        summary["known_percent"] = 0
        summary["not_known_percent"] = 0

    return render(request, "myapp/main/flashcards/flashcard_summary.html", {
        "flashcard_set": flashcard_set,
        "summary": summary
    })


# ======================== AI & MISC VIEWS ========================

def index(request: HttpRequest) -> HttpResponse:
    """Landing page."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    return render(request, "myapp/index.html",
                  {"subscription_features": mark_safe(get_subscription_features())}
            )

@login_required
def dashboard(request):
    user = request.user

    # Weekly progress: count activities per day for last 7 days
    today = now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    weekly_progress = []
    for day in last_7_days:
        practice_count = PracticeTestResult.objects.filter(owner=user, taken_at__date=day).count()
        writing_count = WritingTaskResult.objects.filter(owner=user, taken_at__date=day).count()
        flashcard_count = FlashcardSetProgress.objects.filter(owner=user, last_reviewed__date=day).count()
        total_count = practice_count + writing_count + flashcard_count
        weekly_progress.append({'date': day.isoformat(), 'count': total_count})

    # ✅ Create progress summary
    total_practice = PracticeTestResult.objects.filter(owner=user).count()
    total_writing = WritingTaskResult.objects.filter(owner=user).count()
    total_flashcards = FlashcardSetProgress.objects.filter(owner=user).count()

    # ✅ Example: recent activity list (last 5)
    recent_activity = []
    for result in PracticeTestResult.objects.filter(owner=user).order_by('-taken_at')[:5]:
        recent_activity.append({
            'type': 'Practice Test',
            'name': result.practice_test.title,
            'date': result.taken_at,
        })
    for result in WritingTaskResult.objects.filter(owner=user).order_by('-taken_at')[:5]:
        recent_activity.append({
            'type': 'Writing Task',
            'name': result.writing_task.title,
            'date': result.taken_at,
        })
    for progress in FlashcardSetProgress.objects.filter(owner=user).order_by('-last_reviewed')[:5]:
        recent_activity.append({
            'type': 'Flashcards',
            'name': progress.flashcard_set.title,
            'date': progress.last_reviewed,
        })

    # Sort all activities by date (most recent first)
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    recent_activity = recent_activity[:5]  # top 5 overall

    # ✅ Bundle all in progress_data
    progress_data = {
        'total_practice': total_practice,
        'total_writing': total_writing,
        'total_flashcards': total_flashcards,
        'recent_activity': recent_activity,
    }

    context = {
        'user': user,
        'weekly_progress': weekly_progress,
        'progress_data': progress_data,  # ✅ Now your HTML will see this
    }

    return render(request, "myapp/main/dashboard.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def ai_chat(request: HttpRequest) -> JsonResponse:
    """AI chat endpoint for essay assistance."""
    data = parse_json_body(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    message = data.get("message", "")
    submission_id = data.get("submission_id")

    essay_text = ""
    if submission_id:
        try:
            submission = WritingTaskResult.objects.get(pk=submission_id)
            essay_text = submission.writing_task.prompt
        except WritingTaskResult.DoesNotExist:
            logger.info(f"ai_chat: submission id {submission_id} not found")

    prompt = f"Student asked: {message}\nEssay prompt: {essay_text}" if essay_text else f"Student asked: {message}"
    response = ai_chat_response(prompt, system="You are an AI tutor.", user=getattr(request, "user", None))

    if isinstance(response, dict):
        reply = response.get("reply") or response.get("content") or json.dumps(response)
    else:
        reply = str(response)

    return JsonResponse({"reply": reply})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def create_ai_activity(request: HttpRequest, activity_type: str) -> JsonResponse:
    """Create AI-generated content (practice tests or flashcards)."""
    if request.method == "GET":
        sets = FlashcardSet.objects.filter(owner=getattr(request, "user", None))
        return render(request, "myapp/main/flashcards.html", {"sets": sets})

    # POST
    prompt = request.POST.get("prompt")
    try:
        amount = int(request.POST.get("amount", 5))
        duration = int(request.POST.get("duration", 30))
    except (ValueError, TypeError):
        amount = 5
        duration = 30

    difficulty = request.POST.get("difficulty", "Medium")
    file = request.FILES.get("file")
    file_data = decode_uploaded_file(file) if file else None

    try:
        activity_json, usage = generate_activity(
            prompt=prompt,
            amount=amount,
            difficulty=difficulty,
            activity_type=activity_type,
            extra_file_data=file_data,
        )

        save_activity_from_json(activity_json, request.user, activity_type, duration)
        deduct_credits(usage, request.user)

        redirect_map = {
            "practice_test": "/practice-tests/",
            "flashcards": "/flashcards/"
        }
        return JsonResponse({
            "success": True,
            "redirect_url": redirect_map.get(activity_type, "/")
        })

    except json.JSONDecodeError as e:
        logger.exception(f"AI returned invalid JSON: {e}")
        return JsonResponse({"success": False, "error": f"AI returned invalid JSON: {e}"})
    except Exception as e:
        logger.exception(f"Failed to create AI activity: {e}")
        return JsonResponse({"success": False, "error": str(e)})