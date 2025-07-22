import json
import requests
from langdetect import detect
import langcodes
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from ..models import Collection
from ..chat_utils import get_relevant_context
from .utils import user_can_view

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "finetuned"


def detect_language_safe(text):
    try:
        lang = detect(text)
        if lang not in ["en", "vi", "fr", "de", "es", "zh", "ja", "ko"]:
            return "en"  # fallback to English for unexpected results
        return lang
    except Exception:
        return "en"  # fallback if detection fails


@csrf_exempt
@login_required
def collection_chat(request, collection_id):
    collection = get_object_or_404(Collection, pk=collection_id)

    if not user_can_view(request.user, collection):
        return JsonResponse({"error": "You do not have access to this collection."}, status=403)

    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message")

        if not user_message:
            return JsonResponse({"reply": "Please enter message."}, status=400)

        # # Detect language (for debugging/logging only)
        # user_lang = detect_language_safe(user_message)
        # print(f"[DEBUG] Detected Language: {user_lang}")

        # Load chat history
        history = request.session.get("chat_history", [])
        history.append({"role": "user", "content": user_message})

        # Retrieve RAG context
        context = get_relevant_context(
            user=request.user,
            query=user_message,
            collection_id=collection.id,
            top_k=5
        )
        print(f"Context : {context}")

        system_prompt = (
            "You are StudyGroup, an AI assistant that helps answer academic questions using the provided context only.\n\n"
            "Instructions:\n"
            "- Use ONLY the context given below to answer the question.\n"
            "- If the context contains a 'Correct Answers:' section, return all answers listed there.\n"
            "- Support MULTIPLE correct answers. List all correct choices clearly.\n"
            "- Do NOT guess or add any answers not explicitly listed.\n"
            "- If no 'Correct Answers:' section is present, respond with: 'The answer cannot be determined from the provided context.'\n"
            "- Maintain the original language of the question in your response.\n\n"
            f"Context:\n{context}"
        )

        print(system_prompt)

        messages_payload = [{"role": "system", "content": system_prompt}]
        messages_payload.extend(history)

        # Call Ollama and track response time for TPS
        import time
        start_time = time.time()

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
            assistant_reply = "Cannot connect to the chat server."
            print(f"[chat] Ollama error: {e}")
        finally:
            elapsed_time = time.time() - start_time
            token_count = sum(len(m.get("content", "").split()) for m in messages_payload)
            tps = token_count / elapsed_time if elapsed_time > 0 else 0
            print(f"[DEBUG] Tokens: {token_count}, Time: {elapsed_time:.2f}s, TPS: {tps:.2f}")

        # Save updated history
        history.append({"role": "assistant", "content": assistant_reply})
        request.session["chat_history"] = history[-20:]
        request.session.modified = True

        return JsonResponse({"reply": assistant_reply})

    elif request.method == "GET":
        return JsonResponse({
            "history": request.session.get("chat_history", [])
        })