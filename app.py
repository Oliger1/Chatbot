import tkinter as tk
import webbrowser
import wikipedia
import openai
import sqlite3
import hashlib
import datetime

# Lidhja me bazën e të dhënave
conn = sqlite3.connect('chatbot.db')
c = conn.cursor()

# Tabelat për të ruajtur përdoruesit dhe historikun
c.execute('''CREATE TABLE IF NOT EXISTS users
             (username TEXT, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS history
             (username TEXT, query TEXT, response TEXT, timestamp TEXT)''')
conn.commit()

def login():
    username = username_entry.get()
    password = password_entry.get()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()  # Fjalëkalimi i hashuar

    # Kontrolli në bazën e të dhënave për përdoruesin
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
    result = c.fetchone()

    if result:
        current_user.set(username)  # Set the current user
        show_frame(options_frame)
    else:
        print("Invalid username or password")

openai.api_key = ""

def register():
    new_username = new_username_entry.get()
    new_password = new_password_entry.get()
    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()  # Fjalëkalimi i hashuar

    # Kontrolli në bazën e të dhënave nëse ekziston tashmë emri i përdoruesit
    c.execute("SELECT * FROM users WHERE username=?", (new_username,))
    existing_user = c.fetchone()
    if existing_user:
        print("Username already exists. Please choose another username.")
    else:
        # Shton përdoruesin në bazën e të dhënave nëse nuk ekziston
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_username, hashed_password))
        conn.commit()
        show_frame(login_frame)

def start_as_guest():
    current_user.set("Guest")  # Set the current user as Guest
    show_frame(options_frame)

def handle_message(query):
    query_lower = query.lower()
    if "google" in query_lower:
        open_google()
    elif "wikipedia" in query_lower:
        open_wikipedia()
    elif "recipes" in query_lower or "cooking" in query_lower:
        open_cooking_recipes()
    elif "hospital assistant" in query_lower or "symptoms" in query_lower:
        open_hospital_assistant()
    elif "show options" in query_lower:
        show_frame(options_frame)
    else:
        response = get_openai_response(query)
        save_history(current_user.get(), query, response)
        chat_history.config(state=tk.NORMAL)
        chat_history.insert(tk.END, f"{current_user.get()}: {query}\nBot: {response}\n")
        chat_history.config(state=tk.DISABLED)

def send_message(event=None):
    if not send_message.sending:
        send_message.sending = True
        query = entry.get()
        chat_history.config(state=tk.NORMAL)
        chat_history.insert(tk.END, f"{current_user.get()}: {query}\n")
        chat_history.config(state=tk.DISABLED)
        entry.delete(0, tk.END)

        handle_message(query)
        show_frame(chat_frame)
        send_message.sending = False

send_message.sending = False

def open_google():
    show_frame(google_frame)

def search_google(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")

def open_wikipedia():
    show_frame(wikipedia_frame)

def search_wikipedia(query, read_summary):
    try:
        result = wikipedia.summary(query, sentences=2)
        if not read_summary:
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, result)
            result_text.config(state=tk.DISABLED)
            show_frame(wikipedia_result_frame)
    except wikipedia.exceptions.DisambiguationError:
        print("Multiple results found. Please be more specific.")
    except wikipedia.exceptions.PageError:
        print("No page found for that query. Please try again.")

def open_cooking_recipes():
    show_frame(cooking_recipes_frame)

def get_openai_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You: " + prompt}],
            max_tokens=150
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return str(e)

def open_hospital_assistant():
    show_frame(hospital_assistant_frame)

def search_recipes(ingredients):
    prompt = f"I have the following ingredients: {ingredients}. What can I cook with them?"
    response = get_openai_response(prompt)
    recipe_result_text.config(state=tk.NORMAL)
    recipe_result_text.delete(1.0, tk.END)
    recipe_result_text.insert(tk.END, response)
    recipe_result_text.config(state=tk.DISABLED)
    show_frame(recipe_result_frame)

def get_diagnoses(symptoms):
    prompt = f"I have the following symptoms: {symptoms}. What are the most common diagnoses?"
    response = get_openai_response(prompt)
    diagnosis_result_text.config(state=tk.NORMAL)
    diagnosis_result_text.delete(1.0, tk.END)
    diagnosis_result_text.insert(tk.END, response)
    diagnosis_result_text.config(state=tk.DISABLED)
    show_frame(diagnosis_result_frame)

def save_history(username, query, response):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO history (username, query, response, timestamp) VALUES (?, ?, ?, ?)",
              (username, query, response, timestamp))
    conn.commit()

def show_history():
    username = current_user.get()
    c.execute("SELECT query, response, timestamp FROM history WHERE username=? ORDER BY timestamp DESC", (username,))
    rows = c.fetchall()
    history_text.config(state=tk.NORMAL)
    history_text.delete(1.0, tk.END)
    for row in rows:
        history_text.insert(tk.END, f"{row[2]} - You: {row[0]}\nBot: {row[1]}\n\n")
    history_text.config(state=tk.DISABLED)
    show_frame(history_frame)

def logout():
    current_user.set("Guest")
    show_frame(login_frame)

root = tk.Tk()
root.title("Chatbot")
root.geometry("400x450")
root.configure(bg="#f0f0f0")  # Ngjyra e sfondit

current_user = tk.StringVar(root)  # Variable to store the current logged-in user
current_user.set("Guest")

container = tk.Frame(root)
container.pack(fill="both", expand=True)

frames = {}
for i, F in enumerate(["login_frame", "register_frame", "chat_frame", "options_frame", "google_frame", "wikipedia_frame", "wikipedia_result_frame", "cooking_recipes_frame", "recipe_result_frame", "hospital_assistant_frame", "diagnosis_result_frame", "history_frame"]):
    frame = tk.Frame(container)
    frames[F] = frame
    frame.grid(row=0, column=0, sticky="nsew")

# Login Frame
login_frame = frames["login_frame"]
tk.Label(login_frame, text="Login").pack()
tk.Label(login_frame, text="Username").pack()
username_entry = tk.Entry(login_frame)
username_entry.pack()
tk.Label(login_frame, text="Password").pack()
password_entry = tk.Entry(login_frame, show="*")
password_entry.pack()
tk.Button(login_frame, text="Login", command=login).pack()
tk.Button(login_frame, text="Register", command=lambda: show_frame(register_frame)).pack()
tk.Button(login_frame, text="Start as Guest", command=start_as_guest).pack()

# Register Frame
register_frame = frames["register_frame"]
tk.Label(register_frame, text="Register").pack()
tk.Label(register_frame, text="Username").pack()
new_username_entry = tk.Entry(register_frame)
new_username_entry.pack()
tk.Label(register_frame, text="Password").pack()
new_password_entry = tk.Entry(register_frame, show="*")
new_password_entry.pack()
tk.Button(register_frame, text="Register", command=register).pack()
tk.Button(register_frame, text="Back to Login", command=lambda: show_frame(login_frame)).pack()

# Chat Frame
chat_frame = frames["chat_frame"]
chat_history = tk.Text(chat_frame, height=20, width=50)
chat_history.config(state=tk.DISABLED)
chat_history.pack()

label = tk.Label(chat_frame, text="Enter your command to Artificial Intelligence:")
label.pack()

entry = tk.Entry(chat_frame, width=50)
entry.pack()
entry.bind("<Return>", send_message)

send_button = tk.Button(chat_frame, text="Send", command=send_message)
send_button.pack()

show_options_button = tk.Button(chat_frame, text="Show Options", command=lambda: show_frame(options_frame))
show_options_button.pack()

# Options Frame
options_frame = frames["options_frame"]
tk.Label(options_frame, text="Choose an option:").pack()
tk.Button(options_frame, text="Search on Google", command=open_google).pack()
tk.Button(options_frame, text="Search on Wikipedia", command=open_wikipedia).pack()
tk.Button(options_frame, text="Cooking Recipes", command=open_cooking_recipes).pack()
tk.Button(options_frame, text="Hospital Assistant", command=open_hospital_assistant).pack()
tk.Button(options_frame, text="View Search History", command=show_history).pack()
tk.Button(options_frame, text="Back to Chat", command=lambda: show_frame(chat_frame)).pack()  # Button to go back to chat
tk.Button(options_frame, text="Log Out", command=logout).pack()  # Log Out button

# Google Frame
google_frame = frames["google_frame"]
tk.Label(google_frame, text="Enter your search query:").pack()
google_entry = tk.Entry(google_frame, width=50)
google_entry.pack()
tk.Button(google_frame, text="Search", command=lambda: search_google(google_entry.get())).pack()
tk.Button(google_frame, text="Back to Chat", command=lambda: show_frame(chat_frame)).pack()  # Button to go back to chat

# Wikipedia Frame
wikipedia_frame = frames["wikipedia_frame"]
tk.Label(wikipedia_frame, text="Enter your search query:").pack()
wikipedia_entry = tk.Entry(wikipedia_frame, width=50)
wikipedia_entry.pack()
tk.Button(wikipedia_frame, text="Search", command=lambda: search_wikipedia(wikipedia_entry.get(), False)).pack()
tk.Button(wikipedia_frame, text="Back to Chat", command=lambda: show_frame(chat_frame)).pack()  # Button to go back to chat

# Wikipedia Result Frame
wikipedia_result_frame = frames["wikipedia_result_frame"]
result_text = tk.Text(wikipedia_result_frame, height=20, width=50)
result_text.config(state=tk.DISABLED)
result_text.pack()
tk.Button(wikipedia_result_frame, text="Back to Chat", command=lambda: show_frame(chat_frame)).pack()  # Button to go back to chat

# Cooking Recipes Frame
cooking_recipes_frame = frames["cooking_recipes_frame"]
tk.Label(cooking_recipes_frame, text="Enter the ingredients you have:").pack()
ingredients_entry = tk.Entry(cooking_recipes_frame, width=50)
ingredients_entry.pack()
tk.Button(cooking_recipes_frame, text="Search Recipes", command=lambda: search_recipes(ingredients_entry.get())).pack()
tk.Button(cooking_recipes_frame, text="Back to Chat", command=lambda: show_frame(chat_frame)).pack()  # Button to go back to chat

# Recipe Result Frame
recipe_result_frame = frames["recipe_result_frame"]
recipe_result_text = tk.Text(recipe_result_frame, height=20, width=50)
recipe_result_text.config(state=tk.DISABLED)
recipe_result_text.pack()
tk.Button(recipe_result_frame, text="Back to Chat", command=lambda: show_frame(chat_frame)).pack()  # Button to go back to chat

# Hospital Assistant Frame
hospital_assistant_frame = frames["hospital_assistant_frame"]
tk.Label(hospital_assistant_frame, text="Enter your symptoms:").pack()
symptoms_entry = tk.Entry(hospital_assistant_frame, width=50)
symptoms_entry.pack()
tk.Button(hospital_assistant_frame, text="Get Diagnoses", command=lambda: get_diagnoses(symptoms_entry.get())).pack()
tk.Button(hospital_assistant_frame, text="Back to Chat", command=lambda: show_frame(chat_frame)).pack()  # Button to go back to chat

# Diagnosis Result Frame
diagnosis_result_frame = frames["diagnosis_result_frame"]
diagnosis_result_text = tk.Text(diagnosis_result_frame, height=20, width=50)
diagnosis_result_text.config(state=tk.DISABLED)
diagnosis_result_text.pack()
tk.Button(diagnosis_result_frame, text="Back to Chat", command=lambda: show_frame(chat_frame)).pack()  # Button to go back to chat

# History Frame
history_frame = frames["history_frame"]
history_text = tk.Text(history_frame, height=20, width=50)
history_text.config(state=tk.DISABLED)
history_text.pack()
tk.Button(history_frame, text="Back to Chat", command=lambda: show_frame(chat_frame)).pack()  # Button to go back to chat

def show_frame(frame):
    frame.tkraise()

show_frame(login_frame)
root.mainloop()
