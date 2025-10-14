# Enhanced login view with proper 400 error handling
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
import json

def enhanced_login_view(request):
    """
    Enhanced login view with proper error handling and 400 status codes
    """
    # Handle only GET and POST methods
    if request.method not in ['GET', 'POST']:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "Method not allowed"}, status=405)
        return render(request, "accounts/login_page.html", {
            "form": AuthenticationForm(),
            "error": "Invalid request method"
        })
    
    form = AuthenticationForm(request, data=request.POST or None)

    # If it's an AJAX (JS) request:
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            # Check if request contains valid form data
            if not request.POST:
                return JsonResponse({
                    "success": False, 
                    "error": "No data provided",
                    "message": "Please fill in all required fields"
                }, status=400)
            
            if form.is_valid():
                user = form.get_user()
                if user and user.is_active:
                    login(request, user)
                    return JsonResponse({"success": True, "redirect": "/dashboard/"})
                else:
                    return JsonResponse({
                        "success": False, 
                        "error": "Account inactive",
                        "message": "Your account has been deactivated"
                    }, status=400)
            else:
                # Form validation failed
                errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
                
                # You have two options here:
                
                # Option 1: Return 400 for validation errors (more REST-like)
                return JsonResponse({
                    "success": False, 
                    "errors": errors,
                    "message": "Please correct the errors below"
                }, status=400)
                
                # Option 2: Return 200 with error details (better for some frontend frameworks)
                # return JsonResponse({"success": False, "errors": errors}, status=200)
                
        except json.JSONDecodeError:
            return JsonResponse({
                "success": False, 
                "error": "Invalid JSON data",
                "message": "Malformed request data"
            }, status=400)
            
        except Exception as e:
            # Handle unexpected errors as 400 Bad Request
            error_detail = str(e) if settings.DEBUG else "Please check your input and try again."
            return JsonResponse({
                "success": False, 
                "error": "Invalid request data",
                "details": error_detail
            }, status=400)

    # If it's a regular form POST (HTML)
    elif request.method == "POST":
        try:
            if not request.POST:
                messages.error(request, "No data provided. Please fill in all fields.")
                return render(request, "accounts/login_page.html", {"form": form})
                
            if form.is_valid():
                user = form.get_user()
                if user and user.is_active:
                    login(request, user)
                    messages.success(request, "Welcome back! You've successfully logged in.")
                    return redirect("/dashboard/")
                else:
                    messages.error(request, "Your account has been deactivated. Please contact support.")
            else:
                # Form validation failed - show generic error message
                messages.error(request, "Incorrect email or password. Please try again.")
                
        except Exception as e:
            # Handle unexpected errors in form processing
            messages.error(request, "An error occurred while processing your request. Please try again.")
            if settings.DEBUG:
                messages.error(request, f"Debug: {str(e)}")

    # Render the page normally (GET request or failed POST)
    return render(request, "accounts/login_page.html", {"form": form})


def login_view_with_400_errors(request):
    """
    Alternative version that returns 400 errors for AJAX validation failures
    """
    if request.method not in ['GET', 'POST']:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    form = AuthenticationForm(request, data=request.POST or None)

    # AJAX Request Handling
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        if form.is_valid():
            login(request, form.get_user())
            return JsonResponse({"success": True, "redirect": "/dashboard/"})
        else:
            # Return 400 for validation errors in AJAX requests
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            return JsonResponse({
                "success": False, 
                "errors": errors,
                "message": "Login failed. Please check your credentials."
            }, status=400)  # This sends 400 Bad Request

    # HTML Form POST
    elif request.method == "POST":
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Welcome back! You've successfully logged in.")
            return redirect("/dashboard/")
        else:
            messages.error(request, "Incorrect email or password. Please try again.")

    return render(request, "accounts/login_page.html", {"form": form})