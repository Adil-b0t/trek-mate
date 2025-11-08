<div align="center">

<img src="static/LOGO.png" alt="TrekMate Logo" width="160" />

# TrekMate

Smart Trekking Companion for discovering treks, planning trips, tracking weather, and engaging with a trekking community.

</div>

---

## Table of Contents

- **Overview**
- **Features**
- **Tech Stack**
- **Project Structure**
- **Screenshots**
- **Getting Started**
- **Environment Variables**
- **Database & Migrations**
- **Running the App**
- **Seeding/Utilities**
- **Deployment**
- **Troubleshooting**
- **License**

---

## Overview

TrekMate is a Flask-based web application that helps trekkers explore treks across regions, check real-time or fallback weather, save favorite treks, share trek posts, react/comment, and receive notifications. It includes authentication, admin provisioning via environment variables, and image uploads with basic optimization.

---

## Features

- **User Accounts**
  - Registration with email OTP verification
  - Login/Logout, password reset via email OTP
  - Roles: `user`, `admin`

- **Trek Discovery**
  - Regions and treks with distance, duration, difficulty, and best season
  - Trek images mapping and default placeholders

- **Weather Integration**
  - OpenWeatherMap API integration with smart fallbacks by city/region
  - Safe fallback data if API key is missing

- **Social Feed**
  - Create trek posts with optional images
  - Reactions and threaded comments (with replies)
  - User notifications for reactions/comments/replies

- **Saved Treks**
  - Save/unsave treks per user with unique constraints

- **Admin Utilities**
  - Auto-create admin user from `ADMIN_EMAIL` and `ADMIN_PASSWORD`
  - Admin notifications for system events

- **Uploads & Media**
  - Uploads for comments/posts with size/type checks
  - Optional image optimization (Pillow) and auto directories

---

## Tech Stack

- **Backend**: Flask, Flask-Login, Flask-WTF (CSRF), Flask-Mail
- **Database/ORM**: SQLAlchemy (SQLite by default; `DATABASE_URL` supported)
- **Templating**: Jinja2
- **Env Management**: python-dotenv
- **HTTP**: requests
- **Optional**: Pillow (image optimization)
- **Static**: CSS/JS/Images under `static/`

---

## Project Structure

```
trekMate/
├─ app.py                # Flask app entrypoint (runs server)
├─ data.py               # Data-related helpers
├─ import_trek_data.py   # Script to import seed trek data
├─ update_db.py          # Script to update/maintain DB
├─ trekdata.txt          # Trek data source
├─ trekmate.db           # SQLite database (dev)
├─ requirements.txt      # Python dependencies
├─ templates/            # Jinja2 HTML templates
├─ static/
│  ├─ style.css
│  ├─ script.js
│  ├─ LOGO.png
│  ├─ sec2-bg.png
│  ├─ adminfooter.jpg
│  ├─ fog.mp4
│  ├─ bg-music-genshin.mp3
│  └─ trekimages/        # Trek images
├─ .env                  # Local environment variables
├─ .gitignore
├─ LICENSE
└─ README.md
```

---

## Screenshots

- **Home Section Background**
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/c80609d0-f40c-4f65-8e4c-3a28924bc702" />

- **explore section**
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/b0cf47ae-408c-4470-8dee-088d2105a398" />

- ** trek details page**
- <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/d1abd92e-1c59-4d8a-b7a5-7145ea3e6530" />

- **Trek feed**
- <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/92db5cf5-6454-4de7-88c0-f2f7d643391c" />

- **Trek match**
- <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/efb2db8c-bcc0-415d-ad46-8d4db62c9361" />



## Getting Started

### Prerequisites

- Python 3.10+ recommended
- pip
- A virtual environment tool (e.g., `venv` or `virtualenv`)

### 1) Clone

```bash
git clone <your-repo-url>.git
```

### 2) Create and activate virtualenv

```bash
python -m venv venv
```

Activate:

- Windows PowerShell:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- Windows CMD:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` has issues, install the core packages based on imports:

```bash
pip install Flask Flask-SQLAlchemy Flask-Login Flask-WTF Werkzeug Flask-Mail python-dotenv requests Pillow
```

### 4) Create `.env`

Copy `.env.example` below into `.env` (create the file if it doesn't exist) and update values.

---

## Environment Variables

Place these in a `.env` file in the project root.

```env
# Flask
SECRET_KEY=changeme-please

# Database (defaults to SQLite trekmate.db if not set)
# Example for Postgres: postgresql+psycopg2://user:pass@host:5432/dbname
DATABASE_URL=

# Mail (for OTP, notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_app_password
MAIL_DEFAULT_SENDER=your_email@example.com

# Weather
OPENWEATHER_API_KEY=your_openweather_api_key
OPENWEATHER_BASE_URL=https://api.openweathermap.org/data/2.5/weather

# Admin bootstrap (created at startup if not present)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=supersecurepassword
```

Notes:

- If `OPENWEATHER_API_KEY` is missing, the app gracefully falls back to mock data.
- Setting `ADMIN_EMAIL` and `ADMIN_PASSWORD` allows auto-creation of an admin user on startup.

---

## Database & Migrations

- Default DB is SQLite file `trekmate.db` in the project root.
- On first run, tables are created automatically.
- To switch to Postgres/MySQL, set `DATABASE_URL` accordingly and ensure the driver is installed (e.g., `psycopg2-binary` for Postgres).

---

## Running the App

Development run:

```bash
python app.py
```

This starts the server at `http://0.0.0.0:5000` with `debug=False` by default (adjust in code if needed).

---

## Seeding/Utilities

- `import_trek_data.py` — import initial trek data from `trekdata.txt` into the database.
- `update_db.py` — apply schema/data updates as needed.

Run these scripts with the virtualenv active, for example:

```bash
python import_trek_data.py
python update_db.py
```

Uploads:

- Comment images: `static/uploads/comments/`
- Post images: `static/uploads/posts/`
- Trek images: `static/trekimages/`

Directories are created automatically as needed.

---

## Deployment

TrekMate is a Python/Flask server app. Common deployment targets:

- **Render** (recommended for simplicity)
  1. Push code to GitHub
  2. Create a new Web Service on Render, select the repo
  3. Environment: Python 3.x
  4. Start Command: `gunicorn -w 2 -b 0.0.0.0:10000 app:app`
  5. Add your environment variables from `.env`

- **Railway/Heroku-like**
  - Add a `Procfile` (example):
    ```
    web: gunicorn app:app --worker-tmp-dir /dev/shm --workers 2 --bind 0.0.0.0:$PORT
    ```
  - Ensure `gunicorn` is in `requirements.txt`

- **Docker (optional)**
  - Create a Dockerfile that installs dependencies and starts with `gunicorn app:app`

Static files are served by Flask; for heavy static assets, consider a CDN.

---

## Troubleshooting

- **Email not sending**: Verify `MAIL_*` vars; for Gmail, use App Passwords and enable TLS on 587.
- **Weather unavailable**: Check `OPENWEATHER_API_KEY`. App falls back to mock data if missing.
- **Admin not created**: Ensure `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set before first run; check logs.
- **DB errors**: Delete `trekmate.db` (dev only) to recreate, or verify your `DATABASE_URL` and driver.
- **Image uploads failing**: Confirm file type and size limits; ensure `Pillow` installed.

---

## 📬 Contact Me

Feel free to connect or reach out through any of the platforms below:

- 💼 [LinkedIn – Adil Shaikh](https://www.linkedin.com/in/adil-shaikh-a2482a329/)
- 📸 [Instagram – @adill.b0t](https://www.instagram.com/adill.b0t?igsh=MWE1Mm9xcmpmZmVxMg%3D%3D)


## License

This project is licensed under the terms in the `LICENSE` file.
