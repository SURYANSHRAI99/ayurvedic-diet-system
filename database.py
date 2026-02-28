import sqlite3

def get_connection():
    conn = sqlite3.connect('ayurvedic.db')
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'patient',
            phone TEXT,
            patient_id TEXT UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            age INTEGER,
            gender TEXT,
            weight REAL,
            height REAL,
            bmi REAL,
            medical_history TEXT,
            prakriti TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diet_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            prakriti TEXT,
            plan_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nutrient_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            food_items TEXT,
            total_calories REAL,
            total_protein REAL,
            total_carbs REAL,
            total_fats REAL,
            total_fiber REAL,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            patient_name TEXT,
            patient_id TEXT,
            phone TEXT,
            appointment_date TEXT,
            appointment_time TEXT,
            reason TEXT,
            doctor_name TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            admin_id INTEGER,
            note TEXT,
            prescription TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Default Admin
    cursor.execute('''
        INSERT OR IGNORE INTO users (name, email, password, role, patient_id)
        VALUES ('Admin', 'admin@ayurveda.com', 'admin123', 'admin', 'ADMIN-001')
    ''')

    # Default Doctors
    cursor.execute('''
        INSERT OR IGNORE INTO users (name, email, password, role, patient_id)
        VALUES ('Dr. Suryansh Rai', 'suryansh@ayurveda.com', 'doctor123', 'practitioner', 'DOC-001')
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO users (name, email, password, role, patient_id)
        VALUES ('Dr. Pratyush Singh', 'pratyush@ayurveda.com', 'doctor123', 'practitioner', 'DOC-002')
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO users (name, email, password, role, patient_id)
        VALUES ('Dr. Garvit Kumar', 'garvit@ayurveda.com', 'doctor123', 'practitioner', 'DOC-003')
    ''')

    conn.commit()
    conn.close()

def generate_patient_id(cursor):
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
    count = cursor.fetchone()[0]
    return f"AYU-{str(count + 1).zfill(4)}"

def register_user(name, email, password, role, phone):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        patient_id = None
        if role == 'patient':
            patient_id = generate_patient_id(cursor)
        cursor.execute('''
            INSERT INTO users (name, email, password, role, phone, patient_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, password, role, phone, patient_id))
        conn.commit()
        conn.close()
        return "success", patient_id
    except sqlite3.IntegrityError:
        return "exists", None

def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, role, phone, patient_id FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def save_patient_profile(user_id, age, gender, weight, height, medical_history, prakriti):
    bmi = round(weight / ((height/100) ** 2), 2)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO patient_profiles (user_id, age, gender, weight, height, bmi, medical_history, prakriti)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            age=excluded.age, gender=excluded.gender, weight=excluded.weight,
            height=excluded.height, bmi=excluded.bmi,
            medical_history=excluded.medical_history, prakriti=excluded.prakriti
    ''', (user_id, age, gender, weight, height, bmi, medical_history, prakriti))
    conn.commit()
    conn.close()
    return bmi

def get_patient_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM patient_profiles WHERE user_id=?', (user_id,))
    profile = cursor.fetchone()
    conn.close()
    return profile

def save_diet_plan(user_id, prakriti, plan_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO diet_plans (user_id, prakriti, plan_data)
        VALUES (?, ?, ?)
    ''', (user_id, prakriti, plan_data))
    conn.commit()
    conn.close()

def get_latest_diet_plan(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM diet_plans WHERE user_id=?
        ORDER BY created_at DESC LIMIT 1
    ''', (user_id,))
    plan = cursor.fetchone()
    conn.close()
    return plan

def save_nutrient_log(user_id, food_items, total_calories, total_protein, total_carbs, total_fats, total_fiber):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO nutrient_logs (user_id, food_items, total_calories, total_protein, total_carbs, total_fats, total_fiber)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, food_items, total_calories, total_protein, total_carbs, total_fats, total_fiber))
    conn.commit()
    conn.close()

def get_nutrient_logs(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM nutrient_logs WHERE user_id=? ORDER BY logged_at DESC LIMIT 7', (user_id,))
    logs = cursor.fetchall()
    conn.close()
    return logs

def book_appointment(user_id, patient_name, patient_id, phone, date, time, reason, doctor_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (user_id, patient_name, patient_id, phone, appointment_date, appointment_time, reason, doctor_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, patient_name, patient_id, phone, date, time, reason, doctor_name))
    conn.commit()
    conn.close()

def get_patient_appointments(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM appointments WHERE user_id=?
        ORDER BY appointment_date DESC
    ''', (user_id,))
    appointments = cursor.fetchall()
    conn.close()
    return appointments

def get_all_appointments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM appointments ORDER BY appointment_date ASC')
    appointments = cursor.fetchall()
    conn.close()
    return appointments

def update_appointment_status(appointment_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE appointments SET status=? WHERE id=?', (status, appointment_id))
    conn.commit()
    conn.close()

def change_password(user_id, old_password, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id=? AND password=?', (user_id, old_password))
    user = cursor.fetchone()
    if user:
        cursor.execute('UPDATE users SET password=? WHERE id=?', (new_password, user_id))
        conn.commit()
        conn.close()
        return "success"
    else:
        conn.close()
        return "wrong_password"

def reset_password_by_email(email, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email=?', (email,))
    user = cursor.fetchone()
    if user:
        cursor.execute('UPDATE users SET password=? WHERE email=?', (new_password, email))
        conn.commit()
        conn.close()
        return "success"
    else:
        conn.close()
        return "not_found"

def get_patient_details(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.id, u.name, u.email, u.phone, u.patient_id, u.role,
               p.age, p.gender, p.weight, p.height, p.bmi, p.prakriti, p.medical_history
        FROM users u
        LEFT JOIN patient_profiles p ON u.id = p.user_id
        WHERE u.id = ?
    ''', (user_id,))
    details = cursor.fetchone()
    conn.close()
    return details

def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM patient_profiles WHERE user_id=?', (user_id,))
    cursor.execute('DELETE FROM appointments WHERE user_id=?', (user_id,))
    cursor.execute('DELETE FROM nutrient_logs WHERE user_id=?', (user_id,))
    cursor.execute('DELETE FROM diet_plans WHERE user_id=?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()

def get_admin_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
    total_patients = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='practitioner'")
    total_practitioners = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status='Pending'")
    pending_appointments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE status='Approved'")
    approved_appointments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM nutrient_logs")
    total_nutrient_logs = cursor.fetchone()[0]
    conn.close()
    return {
        'total_patients': total_patients,
        'total_practitioners': total_practitioners,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'approved_appointments': approved_appointments,
        'total_nutrient_logs': total_nutrient_logs
    }

def get_appointment_by_id(appointment_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM appointments WHERE id=?', (appointment_id,))
    apt = cursor.fetchone()
    conn.close()
    return apt

def get_user_email(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM users WHERE id=?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_patient_full_report(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.name, u.email, u.phone, u.patient_id,
               p.age, p.gender, p.weight, p.height, p.bmi, p.prakriti, p.medical_history
        FROM users u
        LEFT JOIN patient_profiles p ON u.id = p.user_id
        WHERE u.id = ?
    ''', (user_id,))
    report = cursor.fetchone()
    conn.close()
    return report

def get_recent_nutrient_log(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT food_items, total_calories, total_protein, total_carbs, total_fats, total_fiber, logged_at
        FROM nutrient_logs WHERE user_id=?
        ORDER BY logged_at DESC LIMIT 1
    ''', (user_id,))
    log = cursor.fetchone()
    conn.close()
    return log

def save_doctor_note(user_id, admin_id, note, prescription):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO doctor_notes (user_id, admin_id, note, prescription)
        VALUES (?, ?, ?, ?)
    ''', (user_id, admin_id, note, prescription))
    conn.commit()
    conn.close()

def get_doctor_notes(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM doctor_notes WHERE user_id=? ORDER BY created_at DESC', (user_id,))
    notes = cursor.fetchall()
    conn.close()
    return notes

def get_all_doctor_notes_for_patient(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM doctor_notes WHERE user_id=? ORDER BY created_at DESC', (user_id,))
    notes = cursor.fetchall()
    conn.close()
    return notes

def get_doctor_note_by_date(user_id, appointment_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM doctor_notes WHERE user_id=?
        AND date(created_at) = ?
        ORDER BY created_at DESC LIMIT 1
    ''', (user_id, appointment_date))
    note = cursor.fetchone()
    conn.close()
    return note

def get_appointment_by_id_for_user(appointment_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM appointments WHERE id=? AND user_id=?', (appointment_id, user_id))
    apt = cursor.fetchone()
    conn.close()
    return apt

def get_doctors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users WHERE role='practitioner'")
    doctors = cursor.fetchall()
    conn.close()
    return doctors

def check_slot_available(doctor_name, apt_date, apt_time):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM appointments
        WHERE doctor_name=? AND appointment_date=? AND appointment_time=?
        AND status != 'Rejected'
    ''', (doctor_name, apt_date, apt_time))
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0
def get_doctor_appointments(doctor_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM appointments WHERE doctor_name=?
        ORDER BY appointment_date ASC
    ''', (doctor_name,))
    appointments = cursor.fetchall()
    conn.close()
    return appointments

def get_doctor_stats(doctor_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE doctor_name=?", (doctor_name,))
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE doctor_name=? AND status='Pending'", (doctor_name,))
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE doctor_name=? AND status='Approved'", (doctor_name,))
    approved = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE doctor_name=? AND status='Rejected'", (doctor_name,))
    rejected = cursor.fetchone()[0]
    conn.close()
    return {
        'total': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected
    }