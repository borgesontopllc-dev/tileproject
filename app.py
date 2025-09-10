# app.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'static/uploads'
PROJECTS_FILE = 'data/projects.json'

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)

# Load and save project data
def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return []
    with open(PROJECTS_FILE, 'r') as f:
        return json.load(f)

def save_projects(projects):
    with open(PROJECTS_FILE, 'w') as f:
        json.dump(projects, f, indent=2)

# Dummy users
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'installer': {'password': 'install123', 'role': 'installer'}
}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        if user in USERS and USERS[user]['password'] == pw:
            session['user'] = user
            session['role'] = USERS[user]['role']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    projects = load_projects()
    return render_template('dashboard.html', projects=projects, role=session['role'])

@app.route('/project/<int:project_id>', methods=['GET', 'POST'])
def project_detail(project_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    projects = load_projects()
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        return 'Project not found', 404

    if request.method == 'POST':
        if session['role'] in ['admin', 'installer']:
            note = request.form.get('note')
            file = request.files.get('photo')
            if note:
                project['notes'].append(f"{session['user']}: {note}")
            if file:
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(path)
                project['photos'].append(f"/{path}")
            save_projects(projects)
            flash("Info added.")
            return redirect(url_for('project_detail', project_id=project_id))

    return render_template('project_detail.html', project=project, role=session['role'])

@app.route('/add_project', methods=['POST'])
def add_project():
    if session.get('role') != 'admin':
        return 'Unauthorized', 403

    projects = load_projects()
    new_project = {
        'id': len(projects) + 1,
        'name': request.form['name'],
        'location': request.form['location'],
        'client': request.form['client'],
        'notes': [],
        'photos': []
    }
    projects.append(new_project)
    save_projects(projects)
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
