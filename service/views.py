from django.shortcuts import render, redirect
from .forms import BlogForm
from .models import Blog

def view_blogs(request):
    blogs = Blog.objects.all() # all users can view blogs
    return render(request, 'service/view_blogs.html', {'blogs': blogs})

def blog(request, blog_id):
    blog_obj = Blog.objects.get(id=blog_id) # prevent naming errors
    
    return render(request, 'service/blog.html', {'blog': blog_obj})

def create_blog(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.created_by = request.user  # Assuming the user is logged in
            blog.save()

            return redirect('service:view_blogs')
    else:
        form = BlogForm()
    
    return render(request, 'service/create_blog.html', {'form': form})


def support(request):
    faq_data = [
        {
            "category": "Account",
            "icon": "MessageCircle",
            "questions": [
                {"question": "How do I reset my password?", "answer": "Go to [settings](Settings) > reset password."},
                {"question": "How do I change my email?", "answer": "Navigate to account [settings](Settings) to update your email."},
                {"question": "Can I delete my account?", "answer": 'Go to account settings and select "Delete Account". Be careful, this action is permanent.'},
                {"question": "Can I switch my subscription plan?", "answer": "Yes, you can upgrade or downgrade your subscription from your account settings."},
                {"question": "Is my personal information safe?", "answer": "Yes, we store all personal data securely and follow privacy best practices."},
                {"question": "How do I recover my account if I forget my email?", "answer": "Contact our support team to recover your account. By email is the best way, contact summitstudygroup@gmail.com"}
            ]
        },
        {
            "category": "General",
            "icon": "Layers",
            "questions": [
                {"question": "What is Summit Study?", "answer": "Summit Study is an AI-powered study platform designed to help students prepare for exams and improve learning efficiency. It provides smart flashcards, personalized study plans, and practice tools to make studying easier and more effective."},
                {"question": "How does Summit Study work?", "answer": "Summit Study uses artificial intelligence to adapt to your learning needs. You can create or generate flashcards, track your progress, and follow tailored study plans. The platform identifies your strengths and weaknesses, helping you focus on the areas that matter most."},
                {"question": "How do I use Summit Study?", "answer": "Simply sign up for an account on [Summit Study](https://summitstudy.app). Once logged in, you can create flashcards, access AI-generated study materials, and set goals. You can also review past exams, monitor your progress, and stay motivated with interactive tools."},
                {"question": "Who is Summit Study for?", "answer": "Summit Study is designed for high school students, VCE students, selective school applicants, and anyone preparing for exams who wants a smarter, more structured way to study."},
                {"question": "Is Summit Study free to use?", "answer": "Summit Study offers a free version with core features. For access to advanced tools like AI-generated flashcards and progress tracking, you can upgrade to a premium plan."}
            ]
        },
        {
            "category": "AI Credits",
            "icon": "Zap",
            "questions": [
                {"question": "How many AI credits do I have?", "answer": "You can view your credit balance on the bottom left corner of the sidebar."},
                {"question": "Do AI credits expire?", "answer": "If you are subscribed to a plan (Free, Premium or Pro) AI credits will renew automatically at the end of every billing cycle. However, if you have bought an AI Credit package, this is kept forever until you use the credits."},
                {"question": "How are credits used?", "answer": "AI Credits allow you to use any AI services on Summit Study such as the chatbot, flashcard maker, practice test maker, etc."},
                {"question": "Can I buy extra AI credits?", "answer": "Yes, additional credits are included in our subscription plans. You can upgrade your plan on the [Subscriptions page](Subscriptions) to get more credits each month."},
                {"question": "Do premium subscriptions include AI credits?", "answer": "Yes, premium plans give 1,000 AI credits per month (renewed every month). To view more, visit the [subscriptions](Subscriptions) page."},
                {"question": "If I buy an annual subscription, do I get all of the AI Credits immediately?", "answer": "Yes, you will receive the yearly AI credits, this is the monthly amount multiplied by 12 (e.g., Premium annual plan will instantly give 12,000 credits while annual Pro will give 36,000 credits)."}
            ]
        },
        {
            "category": "Practice Tests",
            "icon": "BookOpen",
            "questions": [
                {"question": "How do I generate a practice test?", "answer": 'Go to the [Practice Tests](PracticeExams) section, select your subject, and click "Generate Test".'},
                {"question": "Can I upload my own test?", "answer": "Yes, you can upload PDF or text files to create custom AI-generated tests."},
                {"question": "How long does it take to generate a test?", "answer": "Most tests are generated in seconds, though large tests can take longer."},
                {"question": "Can I see my past generated tests?", "answer": "Yes, just click the See More tests button located at the bottom of the Practice Tests page."}
            ]
        },
        {
            "category": "AI Chatbot",
            "icon": "MessageCircle",
            "questions": [
                {"question": "How do I chat with the AI tutor?", "answer": "Click the chat button in the bottom right corner to start a conversation."},
                {"question": "Can the AI tutor answer any subject question?", "answer": "Yes, the AI tutor is trained to help across multiple subjects relevant to VCE and selective exams."},
                {"question": "Does chatting use AI credits?", "answer": "Yes, each message costs 5 AI Credits."},
                {"question": "Can I get detailed explanations from the AI?", "answer": "Yes, the AI provides step-by-step explanations for questions and tasks."}
            ]
        },
        {
            "category": "Subscriptions",
            "icon": "Trophy",
            "questions": [
                {"question": "What is the difference between Free, Pro, and Premium?", "answer": "You can see a detailed comparison on our [Subscriptions page](Subscriptions)."},
                {"question": "Can I upgrade or downgrade at any time?", "answer": "Yes, subscription changes can be made via your account settings."},
                {"question": "Do I get a trial period?", "answer": "Yes, as of September 2025, Summit Study offers 14 day free trials for subscriptions."},
                {"question": "How can I subscribe to Summit Study?", "answer": "Visit the [subscriptions](Subscriptions) page and subscribe to premium or pro plans handled securely by Stripe."}
            ]
        },
        {
            "category": "Writing Tasks",
            "icon": "PenTool",
            "questions": [
                {"question": "How do I submit a writing task?", "answer": "Go to the [Writing Tasks](WritingTasks) section and complete a writing task (You can create new writing tasks)."},
                {"question": "Can the AI give feedback on essays?", "answer": "Yes, the AI provides corrections, suggestions, and scoring guidance."},
                {"question": "Do writing tasks use AI credits?", "answer": "Yes, AI credits are consumed when submitting and reviewing tasks."}
            ]
        },
        {
            "category": "Courses",
            "icon": "Layers",
            "questions": [
                {"question": "How do I enroll in a course?", "answer": "Select the course you want from the Courses section and click 'Enroll'. This is only available for premium and pro users. Upgrade your subscription [here](Subscriptions)."},
                {"question": "Can I track my progress in a course?", "answer": "Yes, progress is tracked automatically and visible on both your dashboard and [progress reports page](Progress)."},
                {"question": "Can I leave a course and rejoin later?", "answer": "Yes, you can re-enroll at any time."}
            ]
        },
        {
            "category": "Progress Reports",
            "icon": "Trophy",
            "questions": [
                {"question": "How do I view my progress?", "answer": "Go to your dashboard and check the [Progress Reports](Progress) section."},
                {"question": "Can I see detailed analytics?", "answer": "Yes, you can view per-topic and per-task performance analytics in the [progress](Progress) page."},
                {"question": "Are progress reports updated in real time?", "answer": "Yes, progress updates automatically as you complete tasks and tests."}
            ]
        },
        {
            "category": "Privacy & Terms",
            "icon": "HelpCircle",
            "questions": [
                {"question": "Where can I find the Privacy Policy?", "answer": "You can read our full [Privacy Policy here](PrivacyPolicy)."},
                {"question": "Where can I find the Terms and Conditions?", "answer": "Our [Terms and Conditions are available here](TermsAndConditions)."},
                {"question": "Is my data shared with third parties?", "answer": "We do not sell your personal data. Please review our Privacy Policy for details on data sharing with service providers."},
                {"question": "Can I request deletion of my data?", "answer": "Yes, you can request data deletion by contacting our support team (summitstudygroup@gmail.com). Please refer to the Privacy Policy for the full procedure."}
            ]
        }
    ]

    return render(request, 'service/support.html', {'faq_data': faq_data})

def terms_and_conditions(request):
    return render(request, 'service/terms/terms_and_conditions.html')

def privacy_policy(request):
    return render(request, 'service/terms/privacy_policy.html')

def about_us(request):
    return render(request, 'service/about_us.html')