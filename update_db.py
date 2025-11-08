import sqlite3

# Connect to the database
conn = sqlite3.connect('trekmate.db')
cursor = conn.cursor()

# Add the image_filename column to the treks table
try:
    cursor.execute('ALTER TABLE treks ADD COLUMN image_filename TEXT')
    print("Successfully added image_filename column to treks table")
except sqlite3.OperationalError as e:
    print(f"treks.image_filename: {e}")

# Add trek_status to trek_posts table
try:
    cursor.execute('ALTER TABLE trek_posts ADD COLUMN trek_status TEXT')
    print("Successfully added trek_status column to trek_posts table")
except sqlite3.OperationalError as e:
    print(f"trek_posts.trek_status: {e}")

# Commit the changes and close the connection
conn.commit()
conn.close()

# from app import app, db, User

# with app.app_context():
#     user = db.session.get(User, 11)  # or: User.query.get(11)
#     if user:
#         user.name = "Admin - Adilb0t"
#         db.session.commit()