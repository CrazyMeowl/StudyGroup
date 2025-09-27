# StudyGroup
> A Django-based collaborative study platform that allows users to create and share flashcards, multiple-choice questions, and multipart questions, enhanced with ChromaDB and an AI-powered RAG system for context-aware Q&A over uploaded documents.

### Prerequisite:
- Windows 10 or higher
- NVIDIA GPU with 8 GB of VRAM or higher, the higher the CUDA core count, the better
- Python 3.10.6
- Ollama 
- An Email account with An App Password

# Installation Guide & Basic Commands
### Python Installation Guide
1. Download the installer from [Python 3.10.6](https://www.python.org/downloads/release/python-3106/)
2. Run the installer -> Remember to choose the “Add To PATH” option



### Ollama Installation Guide
1. Download the installer from [Ollama](https://ollama.com/download)
2. Run the installer

### Email Setup
#### Pre-requisites:
- 2-Step Verification (2FA) Must Be Enabled: This is crucial. App passwords are only available if you have 2-Step Verification turned on for your Google account. If you don't have it enabled, you'll need to set it up first.


#### Steps to Generate a Gmail App Password:
1. Go to myaccount.google.com/apppasswords
2. Sign In (if prompted).
3. Enter the app name, could be “StudyGroup”.
4. Generate the Password.
5. Click the "Generate" button.
6. Copy Your 16-Character App Password.

### Setup Guide
1. Setup local variable
```
setx SENDER_EMAIL_PASSWORD "<put in your app password>"
setx SENDER_EMAIL_USERNAME "<put in your app password>"
setx SUPER_SECRET "<any string you like>"
```
2. Download the source code and extract the zip package
3. Open VS Code at that profile root folder ( optional )
4. Open Terminal
5. Run all the commands below ( This will take a long time )
```
ollama pull llama3
ollama create llama3-zero --file llama3-zero.modelfile
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```
All the steps below will need to be run in the virtual environment terminal or the same terminal above; do not close it.

6. Use the command below and follow its instructions to create the Admin Account
```
python manage.py createsuperuser
```

7. Use the command below to run the server.
```
python manage.py runserver
```

That’s it. The server should be up and running at http://127.0.0.1:8000/

