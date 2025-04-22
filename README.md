# HomeReefRegistering

A web application for registering users with Firebase integration. Built with Flask and Firebase Admin SDK.

## Features
- User registration form with validation
- Stores user data in Firebase Realtime Database
- Flash messaging and session management

## Setup Instructions

### 1. Clone the repository
```
git clone https://github.com/yourusername/your-repo-name.git
cd HomeReefRegistering
```

### 2. Create and activate a virtual environment
```
python -m venv venv
# Activate on Windows:
venv\Scripts\activate
# Or on PowerShell:
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Add Firebase Credentials
- Place your Firebase service account JSON file (e.g., `pds-studio-firebase-adminsdk-fbsvc-cb9200e4d3.json`) in the project directory.
- **Do not commit this file to GitHub.**

### 5. Set Environment Variables (optional)
- Create a `.env` file or set environment variables for sensitive data like `SECRET_KEY` and `FIREBASE_DATABASE_URL`.

### 6. Run the application
```
python app.py
```

Visit [http://127.0.0.1:5000/](http://127.0.0.1:5000/) to access the app.

## Project Structure
```
HomeReefRegistering/
├── app.py
├── requirements.txt
├── utils.py
├── templates/
├── static/
├── .gitignore
└── README.md
```

## License
Specify your license here (e.g., MIT, Apache 2.0).

---

**Note:**
- Never upload your Firebase credentials or other secrets to public repositories.
- Update `requirements.txt` if you add more dependencies.
