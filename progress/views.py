from django.shortcuts import render
from django.db.models import Avg, Max, Min, Count, F
from django.db.models.functions import Length
from myapp.models import PracticeTestResult, WritingTaskResult, FlashcardSetProgress
import json
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from myapp.utils import ai_chat_response


def get_user_results(user):
    practice_results = PracticeTestResult.objects.filter(owner=user)
    writing_results = WritingTaskResult.objects.filter(owner=user)
    flashcard_progress = FlashcardSetProgress.objects.filter(owner=user)

    return {
        "practice_results": practice_results,
        "writing_results": writing_results,
        "flashcard_progress": flashcard_progress,
    }

def progress_page(request):
    """Main progress page with all data consolidated"""
    results = get_user_results(request.user)
    
    practice_results = results["practice_results"]
    writing_results = results["writing_results"]
    flashcard_progress = results["flashcard_progress"]

    # ------------------------ Helper functions ------------------------
    
    def practice_summary():
        total = practice_results.count()
        agg = practice_results.aggregate(
            average_score=Avg('score'),
            highest_score=Max('score'),
            lowest_score=Min('score')
        )
        average_score = agg['average_score'] or 0
        highest_score = agg['highest_score'] or 0
        lowest_score = agg['lowest_score'] or 0

        bins = [0]*10
        for r in practice_results:
            index = min(int(r.score // 10), 9)
            bins[index] += 1

        return {
            'total': total,
            'average': round(average_score, 2),
            'highest': highest_score,
            'lowest': lowest_score,
            'distribution': bins,
        }

    def writing_summary():
        total = writing_results.count()
        agg = writing_results.aggregate(
            average_length=Avg(Length('content')),
            max_length=Max(Length('content')),
            min_length=Min(Length('content'))
        )
        average_length = agg['average_length'] or 0
        max_length = agg['max_length'] or 0
        min_length = agg['min_length'] or 0

        return {
            'total': total,
            'average_length': int(average_length),
            'max_length': max_length,
            'min_length': min_length,
        }

    def flashcard_summary():
        total_sets = flashcard_progress.count()
        completed = flashcard_progress.filter(completed=True).count()
        in_progress = total_sets - completed

        sets_progress = []
        for fp in flashcard_progress:
            total_cards = fp.flashcard_set.flashcards.count()
            known_percent = (fp.known / total_cards * 100) if total_cards else 0
            sets_progress.append({
                'title': fp.flashcard_set.title,
                'known_percent': round(known_percent, 2),
                'completed': fp.completed
            })

        return {
            'total_sets': total_sets,
            'completed': completed,
            'in_progress': in_progress,
            'sets_progress': sets_progress
        }

    # Recent activity data
    recent_practice = practice_results.order_by('-taken_at')[:10]
    recent_writing = writing_results.order_by('-taken_at')[:10]

    # Performance over time data
    practice_data = [
        {
            "score": r.score,
            "taken_at": r.taken_at.isoformat(),
            "test_name": getattr(r, "name", "Practice Test"),
        }
        for r in practice_results.order_by('-taken_at')
    ]
    writing_data = [
        {
            "score": r.score,
            "taken_at": r.taken_at.isoformat(),
            "test_name": getattr(r, "title", "Writing Task"),
        }
        for r in writing_results.order_by('-taken_at')
    ]

    # Quick insights for AI section
    avg_practice_score = (
        practice_results.aggregate(avg_score=Avg('score'))['avg_score'] or 0
    )

    if writing_results.exists():
        lengths = [len(r.content) for r in writing_results]
        avg_writing_length = sum(lengths) / len(lengths)
    else:
        avg_writing_length = 0

    recent_practice_item = practice_results.order_by('-taken_at').first()
    recent_writing_item = writing_results.order_by('-taken_at').first()

    recent_activity_date = None
    if recent_practice_item and recent_writing_item:
        recent_activity_date = max(recent_practice_item.taken_at, recent_writing_item.taken_at)
    elif recent_practice_item:
        recent_activity_date = recent_practice_item.taken_at
    elif recent_writing_item:
        recent_activity_date = recent_writing_item.taken_at

    quick_insights = {
        'avg_practice_score': round(avg_practice_score, 2),
        'avg_writing_length': round(avg_writing_length, 2),
        'recent_activity': recent_activity_date,
    }

    # ------------------------ Gather all data ------------------------
    context = {
        'practice_summary': practice_summary(),
        'writing_summary': writing_summary(),
        'flashcard_summary': flashcard_summary(),
        'recent_practice': recent_practice,
        'recent_writing': recent_writing,
        'practice_data_json': json.dumps(practice_data, cls=DjangoJSONEncoder),
        'writing_data_json': json.dumps(writing_data, cls=DjangoJSONEncoder),
        'quick_insights': quick_insights,
        'practice_distribution_json': json.dumps(practice_summary()['distribution']),
        'flashcard_sets_json': json.dumps([s['title'] for s in flashcard_summary()['sets_progress']]),
        'flashcard_known_json': json.dumps([s['known_percent'] for s in flashcard_summary()['sets_progress']]),
    }

    return render(request, 'progress/progress_page.html', context)

def get_ai_insights(request):
    """AJAX endpoint for AI insights"""
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        results = get_user_results(request.user)
        practice_results = results["practice_results"]
        writing_results = results["writing_results"]

        recent_practice_data = practice_results.order_by('-taken_at')[:20]
        recent_writing_data = writing_results.order_by('-taken_at')[:20]

        practice_data = [
            {'score': r.score, 'date': r.taken_at.strftime('%Y-%m-%d')}
            for r in recent_practice_data
        ]
        writing_data = [
            {'score': r.score, 'length': len(r.content), 'date': r.taken_at.strftime('%Y-%m-%d')}
            for r in recent_writing_data
        ]

        prompt = f"""
        Analyze the following practice test results and writing task results. Provide insights on strengths, weaknesses, and suggestions for improvement. Focus on recent activities.

        Practice Test Results:
        {practice_data}

        Writing Task Results:
        {writing_data}

        Provide a concise summary with actionable advice.
        """

        # Get AI response
        response = ai_chat_response(
            prompt,
            "You are a helpful assistant that provides insights based on user performance data.",
            request.user,
            "gpt-4o-mini",
            "text"
        )

        # Ensure it's a string and return JSON
        return JsonResponse({'ai_insight': str(response)})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
