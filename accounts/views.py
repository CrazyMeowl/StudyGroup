from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import requests
import json
from documents.models import Document 
from documents.utils import get_relevant_context

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "finetuned"

@csrf_exempt
@login_required
def clear_chat(request):
    if request.method == "POST":
        if 'chat_history' in request.session:
            del request.session['chat_history']
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
        user_message = data.get("message")

        if not user_message:
            return JsonResponse({"reply": "Please enter a message."}, status=400)

       # 1) Load & append to session history
        history = request.session.get("chat_history", [])
        history.append({"role": "user", "content": user_message})

        # 2) Retrieve RAG context (top 5 chunks)
        context = get_relevant_context(user_message, top_k=5)

        # 3) Build the messages payload
        messages_payload = []
        if context:
            messages_payload.append({
                "role": "system",
                "content": f"Here are some relevant excerpts from our document library:\n\n{context}, answer the user question in old english with shake spear vibe."
            })
        # Append previous turns
        messages_payload.extend(history)

        # 4) Call Ollama
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": messages_payload,
                    "stream": False
                }
            )
            resp.raise_for_status()
            assistant_reply = resp.json()["message"]["content"]
        except Exception as e:
            assistant_reply = "Sorry, I couldn't reach the AI assistant."
            print(f"[chat] Ollama error: {e}")

        # 5) Append AI reply to history & trim to last 20
        history.append({"role": "assistant", "content": assistant_reply})
        request.session["chat_history"] = history[-20:]
        request.session.modified = True

        return JsonResponse({"reply": assistant_reply})