from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .chat_db import get_user_history, save_user_message, clear_user_history  # Import TinyDB utils


@csrf_exempt
@login_required
def clear_chat(request):
    if request.method == "POST":
        clear_user_history(request.user.username)
        return JsonResponse({"status": "cleared"})
    return JsonResponse({"error": "Invalid request method"}, status=400)

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created!")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})

def custom_logout(request):
    logout(request)
    return redirect("landing")

def index(request):
    if request.user.is_authenticated:
        return redirect("home")
    return redirect("landing")

def landing(request):
    return render(request, "landing.html")


@login_required
def home(request):
    if request.user.is_superuser or request.user.is_staff:
        return render(request, "admin_home.html")
    else:
        return render(request, "student_home.html")

@staff_member_required
def admin_only_view(request):
    return render(request, "admin_page.html")


@csrf_exempt
@login_required
def chat(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user = request.user.username
        message = data.get("message")

        save_user_message(user, "user", message)

        # Send message + history to Ollama
        history = get_user_history(user)
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "finetuned",
                "messages": [
                    {"role": "user", "content": message}
                ],
                "stream": False
            }
        )

        # print(response.json())
        reply = response.json()["message"]["content"]
        save_user_message(user, "assistant", reply)

        return JsonResponse({"reply": reply})
    
