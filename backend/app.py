import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from bson import ObjectId
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

from db import users_collection, patients_collection, medical_records_collection, ecd_collection, audit_records_collection, init_db

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(base_dir, 'frontend', 'templates')
static_dir = os.path.join(base_dir, 'frontend', 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.getenv("SECRET_KEY", "default_fallback_secret_for_dev")
UPLOAD_FOLDER = os.path.join(static_dir, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB max

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                flash(f'Access denied. Required role: {role}')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Routes ---
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_collection.find_one({'username': username})
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if session['role'] == 'collector':
        return redirect(url_for('collector_dashboard'))
    elif session['role'] == 'auditor':
        return redirect(url_for('auditor_dashboard'))
    return "Unknown Role"

# --- Collector Routes ---
@app.route('/collector/dashboard')
@login_required
@role_required('collector')
def collector_dashboard():
    patients = list(patients_collection.find({'created_by_collector_id': session['user_id']}))
    return render_template('collector_dashboard.html', patients=patients)

@app.route('/patients/create', methods=['GET', 'POST'])
@login_required
@role_required('collector')
def create_patient():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        if not name or not age:
            flash("Name and age are required.")
            return redirect(url_for('create_patient'))
            
        patient_id = patients_collection.insert_one({
            'name': name,
            'age': age,
            'created_by_collector_id': session['user_id'],
            'created_at': datetime.utcnow()
        }).inserted_id
        flash('Patient created successfully.')
        return redirect(url_for('patient_view', patient_id=str(patient_id)))
    return render_template('patient_form.html')

@app.route('/patients/<patient_id>')
@login_required
def patient_view(patient_id):
    patient = patients_collection.find_one({'_id': ObjectId(patient_id)})
    if not patient:
        flash("Patient not found.")
        return redirect(url_for('dashboard'))
        
    records = list(medical_records_collection.find({'patient_id': patient_id}))
    ecd = ecd_collection.find_one({'patient_id': patient_id})
    return render_template('patient_view.html', patient=patient, records=records, ecd=ecd)

@app.route('/patients/<patient_id>/upload', methods=['POST'])
@login_required
@role_required('collector')
def upload_document(patient_id):
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('patient_view', patient_id=patient_id))
        
    file = request.files['file']
    file_type = request.form.get('file_type', 'unknown')
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('patient_view', patient_id=patient_id))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{patient_id}_{datetime.utcnow().timestamp()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        medical_records_collection.insert_one({
            'patient_id': patient_id,
            'file_name': filename,
            'file_path': unique_filename,
            'file_type': file_type,
            'uploaded_by': session['user_id'],
            'uploaded_at': datetime.utcnow()
        })
        flash('File uploaded successfully.')
    else:
        flash('Invalid file type.')
        
    return redirect(url_for('patient_view', patient_id=patient_id))

@app.route('/uploads/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/patients/<patient_id>/submit-ecd', methods=['POST'])
@login_required
@role_required('collector')
def submit_ecd(patient_id):
    # Check if ECD already exists
    existing_ecd = ecd_collection.find_one({'patient_id': patient_id})
    if existing_ecd:
        flash("ECD already submitted for this patient.")
        return redirect(url_for('patient_view', patient_id=patient_id))
        
    records = list(medical_records_collection.find({'patient_id': patient_id}))
    record_ids = [str(r['_id']) for r in records]
    
    if not record_ids:
        flash("Cannot submit an empty ECD. Please upload at least one document.")
        return redirect(url_for('patient_view', patient_id=patient_id))
        
    ecd_id = ecd_collection.insert_one({
        'patient_id': patient_id,
        'medical_record_ids': record_ids,
        'created_by_collector': session['user_id'],
        'created_at': datetime.utcnow(),
        'status': 'Pending Audit'
    }).inserted_id
    
    flash("ECD submitted successfully.")
    return redirect(url_for('patient_view', patient_id=patient_id))

# --- Auditor Routes ---
@app.route('/auditor/dashboard')
@login_required
@role_required('auditor')
def auditor_dashboard():
    # Fetch all ECDs with patient info
    ecds = list(ecd_collection.find())
    for ecd in ecds:
        patient = patients_collection.find_one({'_id': ObjectId(ecd['patient_id'])})
        ecd['patient_name'] = patient['name'] if patient else 'Unknown'
        audit = audit_records_collection.find_one({'ecd_id': str(ecd['_id'])})
        ecd['audit_status'] = audit['status'] if audit else 'Pending'
        
    return render_template('auditor_dashboard.html', ecds=ecds)

@app.route('/ecd/<ecd_id>')
@login_required
@role_required('auditor')
def ecd_review(ecd_id):
    ecd = ecd_collection.find_one({'_id': ObjectId(ecd_id)})
    if not ecd:
        flash("ECD not found.")
        return redirect(url_for('auditor_dashboard'))
        
    patient = patients_collection.find_one({'_id': ObjectId(ecd['patient_id'])})
    records = list(medical_records_collection.find({'patient_id': ecd['patient_id']}))
    audit = audit_records_collection.find_one({'ecd_id': ecd_id})
    
    return render_template('ecd_review.html', ecd=ecd, patient=patient, records=records, audit=audit)

@app.route('/ecd/<ecd_id>/audit', methods=['POST'])
@login_required
@role_required('auditor')
def submit_audit(ecd_id):
    status = request.form.get('status')
    notes = request.form.get('notes')
    
    if status not in ['ECD1', 'ECD2', 'ECD3']:
        flash("Invalid audit status.")
        return redirect(url_for('ecd_review', ecd_id=ecd_id))
        
    # Check if already audited, update or insert
    audit_records_collection.update_one(
        {'ecd_id': ecd_id},
        {
            '$set': {
                'auditor_id': session['user_id'],
                'status': status,
                'notes': notes,
                'audited_at': datetime.utcnow()
            }
        },
        upsert=True
    )
    
    # Update ECD status caching
    ecd_collection.update_one(
        {'_id': ObjectId(ecd_id)},
        {'$set': {'status': status}}
    )
    
    flash("Audit classification saved successfully.")
    return redirect(url_for('ecd_review', ecd_id=ecd_id))

if __name__ == '__main__':
    # Add a check to init DB on first run 
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
