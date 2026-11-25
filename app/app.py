import os
import mysql.connector
from flask import Flask, render_template_string, request, redirect, url_for
from dotenv import load_dotenv

load_dotenv("/opt/twotierapp/.env")
app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", "3306")),
        ssl_disabled=False,
        connection_timeout=10,
    )

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Azure Two-Tier Project</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f2f5fa; padding: 40px; }
        .container { background: white; padding: 30px; max-width: 750px; margin: auto; border-radius: 12px; }
        h1 { color: #0078d4; }
        input, button { padding: 10px; margin: 5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background: #0078d4; color: white; }
        .status { color: green; font-weight: bold; }
    </style>
</head>
<body>
<div class="container">
    <h1>Azure Two-Tier Architecture</h1>
    <p>Web Server: Ubuntu 24.04 + Nginx + Gunicorn + Flask</p>
    <p>Database: Azure Database for MySQL Flexible Server 8.4</p>
    <p class="status">Application connected to the database</p>
    <h2>Add a visitor</h2>
    <form method="POST" action="/add">
        <input type="text" name="visitor_name" maxlength="100"
               placeholder="Enter visitor name" required>
        <button type="submit">Save Visitor</button>
    </form>
    <h2>Visitor Records</h2>
    <table>
        <tr><th>ID</th><th>Visitor</th><th>Created At</th></tr>
        {% for visitor in visitors %}
        <tr>
            <td>{{ visitor.id }}</td>
            <td>{{ visitor.visitor_name }}</td>
            <td>{{ visitor.created_at }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
</body>
</html>
"""

@app.route("/")
def home():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, visitor_name, created_at "
            "FROM visitors ORDER BY id DESC"
        )
        visitors = cursor.fetchall()
        return render_template_string(HTML, visitors=visitors)
    except Exception:
        app.logger.exception("Database connection failed")
        return "Database connection failed. Check application logs.", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/add", methods=["POST"])
def add_visitor():
    name = request.form.get("visitor_name", "").strip()
    if not name or len(name) > 100:
        return "Please enter a name of 1 to 100 characters.", 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO visitors (visitor_name) VALUES (%s)", (name,)
        )
        connection.commit()
        return redirect(url_for("home"))
    except Exception:
        app.logger.exception("Could not save visitor")
        return "Could not save visitor. Check application logs.", 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
