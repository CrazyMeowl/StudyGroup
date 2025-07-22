from django.shortcuts import render, redirect
from .forms import RegisterForm, ForgotPasswordForm
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
# from documents.models import Document 
from studycollections.chat_utils import get_relevant_public_context

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives, send_mail
from django.urls import reverse
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.auth.forms import SetPasswordForm
import threading

from langdetect import detect

OLLAMA_URL = "http://localhost:11434/api/chat"
# MODEL_NAME = "deepseek-r1"
MODEL_NAME = "llama3-zero"
@csrf_exempt
@login_required
def clear_chat(request):
    if request.method == "POST":
        if 'chat_history' in request.session:
            del request.session['chat_history']
        return JsonResponse({"status": "cleared"})
    return JsonResponse({"error": "Invalid request method"}, status=400)


# class EmailThread(threading.Thread):
#     def __init__(self, subject, message, from_email, recipient_list):
#         self.subject = subject
#         self.message = message
#         self.from_email = from_email
#         self.recipient_list = recipient_list
#         threading.Thread.__init__(self)

#     def run(self):
#         send_mail(
#             subject=self.subject,
#             message=self.message,
#             from_email=self.from_email,
#             recipient_list=self.recipient_list,
#             fail_silently=False,
#         )


class EmailThread(threading.Thread):
    """
    A thread to send emails in the background, preventing UI lag.
    Supports sending both plain text and HTML emails.
    """
    def __init__(self, subject, message, from_email, recipient_list, html_message=None, fail_silently=False):
        """
        Initializes the EmailThread.

        Args:
            subject (str): The subject line of the email.
            message (str): The plain text body of the email (used as fallback for HTML).
            from_email (str): The sender's email address.
            recipient_list (list): A list of recipient email addresses.
            html_message (str, optional): The HTML body of the email. Defaults to None.
            fail_silently (bool, optional): If True, exceptions during sending are suppressed. Defaults to False.
        """
        self.subject = subject
        self.message = message
        self.from_email = from_email
        self.recipient_list = recipient_list
        self.html_message = html_message
        self.fail_silently = fail_silently
        super().__init__() # Correct way to call parent constructor in Python 3

    def run(self):
        """
        Executes the email sending logic in the new thread.
        Uses EmailMultiAlternatives if html_message is provided, otherwise falls back to send_mail.
        """
        try:
            if self.html_message:

                msg = EmailMultiAlternatives(
                    self.subject,
                    self.message, # Plain text version
                    self.from_email,
                    self.recipient_list
                )
                msg.attach_alternative(self.html_message, "text/html")
                msg.send(fail_silently=self.fail_silently)
            else:
                send_mail(
                    subject=self.subject,
                    message=self.message,
                    from_email=self.from_email,
                    recipient_list=self.recipient_list,
                    fail_silently=self.fail_silently,
                )
            print(f"Email sent successfully to: {self.recipient_list}") 
        except Exception as e:
            print(f"Error sending email to {self.recipient_list}: {e}")
            if not self.fail_silently:
                raise

def register(request):
    """
    Handles user registration, account deactivation, and sends an activation email.
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until confirmed
            user.save()

            # Generate activation link
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = get_current_site(request).domain
            # Ensure 'activate' URL name is correctly defined in your urls.py
            activation_link = f"http://{domain}{reverse('activate', args=[uid, token])}"

            # Prepare context for the email template
            email_context = {
                'user': user,
                'activation_link': activation_link,
                'from_email': settings.EMAIL_HOST_USER, # Pass for footer in HTML email
                'site_name': get_current_site(request).name, # Optional: Pass site name
                # Add any other variables your email template needs
            }

            # Render the HTML email content from template
            # Ensure 'accounts/email/account_activation_email.html' exists at the specified path
            html_message = render_to_string(
                'email/account_activation_email.html',
                email_context
            )

            # Create a plain text version for email clients that don't render HTML
            # Replace 'YourAppName' with your actual application's name
            plain_message = (
                f"Hi {user.username},\n\n"
                f"Please activate your account by clicking the link below:\n\n"
                f"{activation_link}\n\n"
                f"If you did not create an account with us, you can safely ignore this email.\n\n"
                f"Best regards,\n"
                f"The YourAppName Team"
            )

            subject = "Activate Your Account"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]

            # Start the email sending in a new thread
            # Pass both plain_message and html_message to the EmailThread
            EmailThread(subject, plain_message, from_email, recipient_list, html_message=html_message).start()

            messages.success(request, "Account created! Please check your email to activate your account. (Especially in spam/trash mail category)")
            return redirect("login")
        else:
            # If form is not valid, re-render the form with errors
            pass # Errors will be displayed by the template automatically

    else: # GET request
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated! You can now log in.")
        return redirect("login")
    else:
        messages.error(request, "The activation link is invalid or has expired.")
        return redirect("register")

def custom_logout(request):
    logout(request)
    return redirect("landing")

def index(request):
    if request.user.is_authenticated:
        return redirect("home")
    return redirect("landing")

def landing(request):
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "landing.html")


@login_required
def home(request):
    if request.user.is_superuser or request.user.is_staff:
        
        # return render(request, "admin/admin_home.html")
        return redirect('admin_dashboard')
    else:
        return render(request, "student_home.html")

@staff_member_required
def admin_only_view(request):
    return render(request, "admin_page.html")
import re, time, json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import requests  # Make sure this is enabled

def detect_language(text):
    # Simple heuristic-based detection
    if re.search(r"[à-ỹ]", text, re.IGNORECASE):
        return "vi"
    if re.search(r"[一-龯]", text):
        return "zh"
    if re.search(r"[ぁ-んァ-ン]", text):
        return "ja"
    if re.search(r"[가-힣]", text):
        return "ko"
    return "en"

def get_fallback_message(lang_code):
    messages = {
        "vi": "StudyGroup hiện không có thông tin cần thiết để trả lời câu hỏi của bạn.",
        "en": "StudyGroup currently does not have the required information to answer your question.",
        "es": "StudyGroup actualmente no tiene la información necesaria para responder a su pregunta.",
        "fr": "StudyGroup n’a actuellement pas les informations nécessaires pour répondre à votre question.",
        "de": "StudyGroup hat derzeit nicht die erforderlichen Informationen, um Ihre Frage zu beantworten.",
        "zh": "StudyGroup 目前没有回答您问题所需的信息。",
        "ja": "StudyGroup は現在、ご質問にお答えするために必要な情報を持っていません。",
        "ko": "StudyGroup는 현재 귀하의 질문에 답변하는 데 필요한 정보를 보유하고 있지 않습니다。"
    }
#     return messages.get(lang_code, messages["en"])
# ### deepseek-r1
# @csrf_exempt
# @login_required
# def chat(request):
#     import re
#     if request.method == "POST":
#         data = json.loads(request.body)
#         user_message = data.get("message")
#         if not user_message:
#             return JsonResponse({"reply": "Please enter a message."}, status=400)

#         fallback_reply = "StudyGroup currently does not have the required information to answer your question."

#         # Load chat history
#         history = request.session.get("chat_history", [])
#         history.append({"role": "user", "content": user_message})

#         # Step 1: Retrieve candidate chunks
#         chunks, _ = get_relevant_public_context(query=user_message, top_k=10, min_score=0.0)
#         chunk_list = [chunk.strip() for chunk in chunks.split("\n\n") if chunk.strip()]
#         short_chunks = [chunk for chunk in chunk_list]

#         if not short_chunks:
#             print("[DEBUG] No usable chunks — skipping to fallback.")
#             assistant_reply = fallback_reply
#             history.append({"role": "assistant", "content": assistant_reply})
#             request.session["chat_history"] = history[-20:]
#             request.session.modified = True
#             return JsonResponse({"reply": assistant_reply})
#         for chunk in short_chunks:
#             print(f"[DEBUG] chunk: {chunk}")
#         # Step 2: Ask DeepSeek to filter relevant passages (text-based)
#         relevance_prompt = [
#             {
#                 "role": "system",
#                 "content": (
#                     "You are an assistant that selects useful passages to help answer a user's question.\n"
#                     "Given a question and a set of passages, return only the passages that clearly help answer the question.\n"
#                     "If none are helpful, reply with: NONE.\n"
#                     "Do not explain or add commentary. Do not include <think> tags."
#                 )
#             },
#             {
#                 "role": "user",
#                 "content": f"Question: {user_message}\n\nPassages:\n" + "\n\n".join(short_chunks)
#             }
#         ]

#         try:
#             relevance_response = requests.post(
#                 OLLAMA_URL,
#                 json={
#                     "model": MODEL_NAME,
#                     "messages": relevance_prompt,
#                     "stream": False,
#                     "temperature": 0.0
#                 }
#             )
#             raw_relevance = relevance_response.json()["message"]["content"]
#             relevance_answer = re.sub(r"<think>.*?</think>", "", raw_relevance, flags=re.DOTALL).strip()
#             print(f"[DEBUG] raw_relevance: {raw_relevance}")

#             if "none" in relevance_answer.lower():
#                 print("[DEBUG] No relevant context — using fallback.")
#                 assistant_reply = fallback_reply
#                 history.append({"role": "assistant", "content": assistant_reply})
#                 request.session["chat_history"] = history[-20:]
#                 request.session.modified = True
#                 return JsonResponse({"reply": assistant_reply})
#             else:
#                 system_prompt = (
#                     "You are StudyGroup, an academic assistant. Answer the user's question using ONLY the provided information below. "
#                     f"If the information does not contain the answer, respond: '{fallback_reply}'.\n\n"
#                     "Do not use external knowledge. Do not guess. Do not include <think> tags.\n\n"
#                     f"Information:\n{relevance_answer}"
#                 )

#         except Exception as e:
#             print(f"[DEBUG] Relevance check failed: {e}")
#             assistant_reply = fallback_reply
#             history.append({"role": "assistant", "content": assistant_reply})
#             request.session["chat_history"] = history[-20:]
#             request.session.modified = True
#             return JsonResponse({"reply": assistant_reply})

#         # Step 3: Ask final question using filtered context
#         messages_payload = [{"role": "system", "content": system_prompt}]
#         messages_payload.extend(history)

#         try:
#             start_time = time.time()
#             response = requests.post(
#                 OLLAMA_URL,
#                 json={
#                     "model": MODEL_NAME,
#                     "messages": messages_payload,
#                     "stream": False,
#                     "temperature": 0.0
#                 }
#             )
#             raw_reply = response.json()["message"]["content"]
#             assistant_reply = re.sub(r"<think>.*?</think>", "", raw_reply, flags=re.DOTALL).strip()

#         except Exception as e:
#             assistant_reply = "Cannot connect to the chat server."
#             print(f"[chat] Ollama error: {e}")
#         finally:
#             elapsed = time.time() - start_time
#             token_count = sum(len(m["content"].split()) for m in messages_payload)
#             print(f"[DEBUG] Tokens: {token_count}, Time: {elapsed:.2f}s, TPS: {token_count / elapsed:.2f}")

#         # Step 4: Save updated history
#         history.append({"role": "assistant", "content": assistant_reply})
#         request.session["chat_history"] = history[-20:]
#         request.session.modified = True

#         return JsonResponse({"reply": assistant_reply})

#     elif request.method == "GET":
#         return JsonResponse({
#             "history": request.session.get("chat_history", [])
#         })


## llama3
@csrf_exempt
@login_required
def chat(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message")
        if not user_message:
            return JsonResponse({"reply": "Please enter message."}, status=400)


        
        fallback_reply = "StudyGroup currently does not have the required information to answer your question."

        # Load chat history
        history = request.session.get("chat_history", [])
        history.append({"role": "user", "content": user_message})


                # Step 0: Handle simple greetings or assistant-related questions
        greetings = {"hi", "hello", "hey", "greetings"}
        assistant_questions = [
            "who are you",
            "what is studygroup",
            "tell me about studygroup",
            "what can you do",
            "what is this",
        ]

        lower_msg = user_message.strip().lower()

        cleaned_lower_msg = lower_msg.replace("!", "").replace(".", "").replace("?", "").strip()
        if cleaned_lower_msg in greetings:
            reply = "Hello! How can I help you today?"
            history.append({"role": "assistant", "content": reply})
            request.session["chat_history"] = history
            return JsonResponse({"reply": reply})

        # Assistant info response
        if any(q in lower_msg for q in assistant_questions):
            reply = (
                "I'm StudyGroup's AI assistant. I can help you understand study materials, "
                "answer questions based on public documents and shared collections, and assist with your learning."
            )
            history.append({"role": "assistant", "content": reply})
            request.session["chat_history"] = history
            return JsonResponse({"reply": reply})

        # Step 1: Retrieve raw context (multiple chunks)
        chunks, _ = get_relevant_public_context(query=user_message, top_k=5, min_score=0.0)
        relevant_chunks = []
        print("[DEBUG] Checking each chunk for relevance...")

        # Step 2: Relevance check per chunk
        for i, chunk in enumerate(chunks.split("\n\n")):  # assuming chunks are separated by double newline
            chunk = chunk.strip()
            if not chunk:
                continue

            relevance_check_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an assistant that determines whether the following passage contains a clear, direct answer "
                        "to the user's question. Only reply YES if the answer is explicitly stated, not inferred or implied."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Question: {user_message}\n\n"
                        f"Passage:\n{chunk}\n\n"
                        "Does the passage contain instructions, steps, or explanations that answer the user's question directly or closely enough to be helpful? Answer YES or NO. No explanations."

                    )
                }
            ]

            try:
                resp = requests.post(
                    OLLAMA_URL,
                    json={
                        "model": MODEL_NAME,
                        "messages": relevance_check_messages,
                        "stream": False,
                        "temperature": 0.0
                    }
                )
                answer = resp.json()["message"]["content"].strip().lower()
                print(f"[CONTEXT] {chunk} \n [RELEVANT] {answer}")
                if answer.startswith("yes"):
                    relevant_chunks.append(chunk)
            except Exception as e:
                print(f"[DEBUG] Relevance check failed on chunk {i}: {e}")

        # Step 3: Build system prompt
        if relevant_chunks:
            merged_context = "\n\n".join(relevant_chunks)
            system_prompt = (
                "You are StudyGroup, an academic assistant. Answer the user's question using ONLY the provided information below. "
                "Never guess, never use external knowledge. Do not mention 'context' or 'passage'. "
                "Always respond in the same language as the user.\n\n"
                f"Information:\n{merged_context}\n\n"
            )
        else:
            print("[DEBUG] No relevant chunks. Using fallback message.")
            system_prompt = (
                "You are StudyGroup, an academic assistant. You do not have enough information to answer this question. "
                f"Respond with the following message, in the same language as the user's question: '{fallback_reply}'"
            )

        # Step 4: Send message to model
        messages_payload = [{"role": "system", "content": system_prompt}]
        messages_payload.extend(history)

        try:
            start_time = time.time()
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": messages_payload,
                    "stream": False,
                    "temperature": 0.0
                }
            )
            assistant_reply = resp.json()["message"]["content"]
        except Exception as e:
            assistant_reply = "Cannot connect to the chat server."
            print(f"[chat] Ollama error: {e}")
        finally:
            elapsed = time.time() - start_time
            token_count = sum(len(m["content"].split()) for m in messages_payload)
            print(f"[DEBUG] Tokens: {token_count}, Time: {elapsed:.2f}s, TPS: {token_count/elapsed:.2f}")

        # Save updated history
        history.append({"role": "assistant", "content": assistant_reply})
        request.session["chat_history"] = history[-20:]
        request.session.modified = True

        return JsonResponse({"reply": assistant_reply})

    elif request.method == "GET":
        return JsonResponse({
            "history": request.session.get("chat_history", [])
        })



def forgot_password(request):
    """
    Handles the forgot password request, sends a password reset link via email.
    """
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST) # Use the form to handle input
        if form.is_valid():
            email = form.cleaned_data.get("email")
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                messages.success(request, "Password reset link has been sent to your email.")
                return redirect("forgot_password")

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            domain = get_current_site(request).domain
            # Ensure 'reset_password' URL name is correctly defined in your urls.py
            reset_link = f"http://{domain}{reverse('reset_password', args=[uid, token])}"

            # Prepare context for the email template
            email_context = {
                'user': user,
                'reset_link': reset_link,
                'from_email': settings.EMAIL_HOST_USER, # Pass for footer in HTML email
                'site_name': get_current_site(request).name, # Optional: Pass site name
                # Add any other variables your email template needs
            }

            # Render the HTML email content from template
            # Ensure 'accounts/email/password_reset_email.html' exists at the specified path
            html_message = render_to_string(
                'email/forgot_password.html',
                email_context
            )

            # Create a plain text version for email clients that don't render HTML
            # Replace 'StudyGroup' with your actual application's name
            plain_message = (
                f"Hi {user.username},\n\n"
                f"You requested a password reset. Click the link below to set a new password:\n\n"
                f"{reset_link}\n\n"
                f"If you did not request this, you can safely ignore this email."
                f"Your current password will remain unchanged.\n\n"
                f"Best regards,\n"
                f"The StudyGroup Team"
            )

            subject = "Reset Your Password"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]

            EmailThread(subject, plain_message, from_email, recipient_list, html_message=html_message).start()

            messages.success(request, "Password reset link has been sent to your email.")
            return redirect("login")
        else:
            # If form is not valid (e.g., empty email, invalid format), re-render with errors
            pass # Errors will be displayed by the template automatically

    else: # GET request
        form = ForgotPasswordForm() # Instantiate an empty form for GET request

    return render(request, "accounts/forgot_password.html", {'form': form})

def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been reset. You can now log in.")
                return redirect("login")
        else:
            form = SetPasswordForm(user)
        return render(request, "accounts/reset_password.html", {"form": form})
    else:
        messages.error(request, "The password reset link is invalid or has expired.")
        return redirect("forgot_password")

