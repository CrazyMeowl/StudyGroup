from tinydb import TinyDB, Query

db = TinyDB("chat_history.json")
User = Query()

def get_user_history(username):
    result = db.get(User.username == username)
    return result["messages"] if result else []

def save_user_message(username, role, content):
    messages = get_user_history(username)
    messages.append({"role": role, "content": content})
    
    if db.contains(User.username == username):
        db.update({"messages": messages}, User.username == username)
    else:
        db.insert({"username": username, "messages": messages})

def clear_user_history(username):
    db.remove(User.username == username)
