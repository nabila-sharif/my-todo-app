import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import pandas as pd
from fpdf import FPDF
import base64
import re

# Database and Business Logic (OOP Style)
class ToDoApp:
    def __init__(self):
        self.conn = sqlite3.connect('todo.db', check_same_thread=False)
        self.c = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, email TEXT, pushover_key TEXT)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS todo(username TEXT, task TEXT, status TEXT, date TEXT, favorite INTEGER, category TEXT, priority TEXT, recurring TEXT)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS login_history(username TEXT, login_time TEXT)''')
        self.conn.commit()

    def add_user(self, username, password, email, pushover_key):
        self.c.execute('INSERT INTO users(username, password, email, pushover_key) VALUES (?, ?, ?, ?)', (username, password, email, pushover_key))
        self.conn.commit()

    def login_user(self, username, password):
        self.c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        return self.c.fetchall()

    def log_login(self, username):
        self.c.execute("INSERT INTO login_history(username, login_time) VALUES (?, ?)", (username, str(datetime.now())))
        self.conn.commit()

    def get_user_email_key(self, username):
        self.c.execute("SELECT email, pushover_key FROM users WHERE username=?", (username,))
        return self.c.fetchone()

    def add_task(self, username, task, status, date, favorite, category, priority, recurring):
        self.c.execute('''INSERT INTO todo(username, task, status, date, favorite, category, priority, recurring) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (username, task, status, date, favorite, category, priority, recurring))
        self.conn.commit()

    def get_tasks(self, username):
        self.c.execute('SELECT rowid, * FROM todo WHERE username=?', (username,))
        return self.c.fetchall()

    def update_task(self, task_id, task, status, date, favorite, category, priority, recurring):
        self.c.execute('''UPDATE todo SET task=?, status=?, date=?, favorite=?, category=?, priority=?, recurring=? WHERE rowid=?''', 
                      (task, status, date, favorite, category, priority, recurring, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        self.c.execute('DELETE FROM todo WHERE rowid=?', (task_id,))
        self.conn.commit()

    def search_tasks(self, username, query):
        self.c.execute('''SELECT rowid, * FROM todo WHERE username=? AND (task LIKE ? OR date LIKE ? OR status LIKE ?)''',
                      (username, f'%{query}%', f'%{query}%', f'%{query}%'))
        return self.c.fetchall()

    def update_task_status(self, task_id, new_status):
        self.c.execute('UPDATE todo SET status=? WHERE rowid=?', (new_status, task_id))
        self.conn.commit()

        if new_status and new_status.lower() == "done":
            self.c.execute("SELECT recurring, date FROM todo WHERE rowid=?", (task_id,))
            rec, current_date = self.c.fetchone()
            if rec and rec != "None":
                next_date = self.compute_next_date(rec, current_date)
                self.c.execute("UPDATE todo SET date=?, status='ToDo' WHERE rowid=?", (next_date, task_id))
                self.conn.commit()

    def compute_next_date(self, recurring, date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if recurring == "Daily": return (dt + timedelta(days=1)).strftime("%Y-%m-%d")
        elif recurring == "Weekly": return (dt + timedelta(weeks=1)).strftime("%Y-%m-%d")
        elif recurring == "Monthly": return (dt + timedelta(days=30)).strftime("%Y-%m-%d")
        return date_str

    def get_due_tasks(self):
        today = datetime.now().strftime('%Y-%m-%d')
        self.c.execute("SELECT rowid, * FROM todo WHERE date=?", (today,))
        return self.c.fetchall()

    def send_email_reminder(self, to_email, task):
        from_email = "your_email@example.com"
        password = "your_email_password"
        subject = "To-Do Task Reminder"
        body = f"Reminder: You have a task due today: {task}"

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Email failed: {e}")

    def send_push_notification(self, message, user_key):
        if not user_key:
            return
        data = {"token": "your_pushover_app_token", "user": user_key, "message": message}
        try:
            requests.post("https://api.pushover.net/1/messages.json", data=data)
        except Exception as e:
            print(f"Push failed: {e}")

    def export_pdf(self, data):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for row in data:
            pdf.cell(200, 10, txt=" | ".join([str(i) for i in row]), ln=True)
        return pdf.output(dest='S').encode('latin1')

# App
app = ToDoApp()
st.title("Multi-User To-Do App")
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''

menu = ["Login", "SignUp"]
choice = st.sidebar.selectbox("Menu", menu)

if not st.session_state['logged_in']:
    if choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        new_email = st.text_input("Email")
        pushover_key = st.text_input("Pushover User Key (Optional)")
        if st.button("Signup"):
            if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                st.error("Invalid email format")
            else:
                app.add_user(new_user, new_password, new_email, pushover_key)
                st.success("Account created successfully")

    elif choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            if app.login_user(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                app.log_login(username)
                st.rerun()
            else:
                st.error("Invalid credentials")

else:
    username = st.session_state['username']
    st.success(f"Logged in as {username}")
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.rerun()

    st.subheader("Add Task")
    task = st.text_input("Task")
    status = st.selectbox("Status", ["ToDo", "In Progress", "Done"])
    date = st.date_input("Due Date")
    favorite = st.checkbox("Favorite")
    category = st.text_input("Category")
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    recurring = st.selectbox("Recurring", ["None", "Daily", "Weekly", "Monthly"])
    if st.button("Add Task", key="add_task_btn"):
        if not task.strip():
            st.warning("Please enter a task.")
        else:
            app.add_task(username, task, status, date.strftime('%Y-%m-%d'), int(favorite), category, priority, recurring)
            st.success("Task Added")

    st.subheader("Your Tasks")
    tasks = app.get_tasks(username)
    for t in tasks:
        st.write(f"ID: {t[0]} | Task: {t[2]} | Status: {t[3]} | Date: {t[4]} | Fav: {bool(t[5])} | Cat: {t[6]} | Priority: {t[7]} | Recurring: {t[8]}")
        with st.expander("Edit/Delete"):
            new_task = st.text_input(f"Task {t[0]}", value=t[2], key=f"edit_task_{t[0]}")
            new_status = st.selectbox(f"Status {t[0]}", ["ToDo", "In Progress", "Done"], index=["ToDo", "In Progress", "Done"].index(t[3]), key=f"status_{t[0]}")
            new_date = st.date_input(f"Date {t[0]}", value=datetime.strptime(t[4], "%Y-%m-%d"), key=f"date_{t[0]}")
            new_fav = st.checkbox(f"Favorite {t[0]}", value=bool(t[5]), key=f"fav_{t[0]}")
            new_cat = st.text_input(f"Category {t[0]}", value=t[6], key=f"cat_{t[0]}")
            new_pri = st.selectbox(f"Priority {t[0]}", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(t[7]), key=f"pri_{t[0]}")
            new_rec = st.selectbox(f"Recurring {t[0]}", ["None", "Daily", "Weekly", "Monthly"], index=["None", "Daily", "Weekly", "Monthly"].index(t[8]), key=f"rec_{t[0]}")
            if st.button(f"Update {t[0]}"):
                app.update_task(t[0], new_task, new_status, new_date.strftime('%Y-%m-%d'), int(new_fav), new_cat, new_pri, new_rec)
                st.success("Task Updated")
                st.rerun()
            if st.button(f"Delete {t[0]}"):
                app.delete_task(t[0])
                st.success("Task Deleted")
                st.rerun()

    df = pd.DataFrame(tasks, columns=['ID', 'Username', 'Task', 'Status', 'Date', 'Favorite', 'Category', 'Priority', 'Recurring'])
    st.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'), "tasks.csv", "text/csv")

    pdf_bytes = app.export_pdf(tasks)
    b64 = base64.b64encode(pdf_bytes).decode()
    st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="tasks.pdf">Download PDF</a>', unsafe_allow_html=True)

    search = st.text_input("Search Tasks")
    if search:
        found = app.search_tasks(username, search)
        for f in found:
            st.write(f"Found: {f[0]} - {f[2]} - {f[4]}")

    if st.button("Send Reminders"):
        due_tasks = app.get_due_tasks()
        for t in due_tasks:
            user = t[1]
            task = t[2]
            email_key = app.get_user_email_key(user)
            if email_key and len(email_key) == 2:
                email, key = email_key
                app.send_email_reminder(email, task)
                app.send_push_notification(f"{user}, Reminder: {task} is due today!", key)

st.markdown(
    """
    <style>
    .footer {
        position: relative;
        bottom: -30px;
        text-align: center;
        width: 100%;
        margin-top: 50px;
        font-size: 14px;
        color: #888;
    }
    .footer a {
        color: #4CAF50;
        text-decoration: none;
    }
    .footer a:hover {
        text-decoration: underline;
    }
    </style>
    <div class='footer'>
        Made with ❤ using <a href="https://streamlit.io/" target="_blank">Streamlit</a><br>
        &copy; 2025 | <a href="https://github.com/nabila-sharif" target="_blank">Nabila Sharif</a>
    </div>
    """,
    unsafe_allow_html=True
)