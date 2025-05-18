# 📝 Multi-User To-Do List App (with Email & Push Notifications)

This is a fully functional **Streamlit-based To-Do list web application** that supports **multiple users**. Each user can securely log in, create and manage tasks, and receive **email and Pushover push notifications** for due tasks.

---

## 🚀 Features

- 🔐 User Authentication (Sign Up & Login)
- 🧾 Task Management: Add, Update, Delete
- 🗂️ Task Categorization and Priority levels
- ⏰ Recurring Tasks (Daily, Weekly, Monthly)
- 📌 Mark Tasks as Favorite
- 🔎 Search and Filter Tasks
- 🕒 Login History Tracking
- 📧 Email Reminders for Due Tasks
- 📲 Push Notifications via Pushover
- 📄 Export Tasks as CSV and PDF

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: SQLite (via sqlite3)
- **Email**: SMTP (Gmail)
- **Push Notification**: Pushover API
- **PDF Export**: FPDF
- **Data Handling**: pandas

---

## 📦 Setup Instructions

1. **Clone this repository:**

bash
git clone https://github.com/your-repo-name/todo-app.git
cd todo-app


2. **Install dependencies:**

bash
pip install -r requirements.txt


3. **Run the app:**

bash
streamlit run your_app_filename.py


> 🔑 Replace "your_email@example.com", "your_email_password", and "your_pushover_app_token" in the code with your actual credentials or environment variables.

---

## 📂 File Structure

├── todo_app.py         # Main application file
├── requirements.txt    # Python dependencies
├── README.md           # Project overview
└── todo.db             # SQLite database (created automatically)


---

## 🙋‍♀️ Author

Made with ❤️ by [Nabila Sharif](https://github.com/nabila-sharif)

---
