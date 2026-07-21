import sqlite3
import bcrypt
from datetime import datetime

def init_db():
    conn = sqlite3.connect('auditiq.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL,
            plan TEXT DEFAULT 'free'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            company_name TEXT,
            standard TEXT,
            industry TEXT,
            audit_type TEXT,
            date TEXT NOT NULL,
            findings_count INTEGER,
            high_risk_count INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def register_user(name, email, password):
    try:
        conn = sqlite3.connect('auditiq.db')
        c = conn.cursor()
        hashed = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        c.execute('''
            INSERT INTO users (name, email, password, created_at)
            VALUES (?, ?, ?, ?)
        ''', (name, email, hashed,
              datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        conn.close()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    except Exception as e:
        return False, str(e)

def login_user(email, password):
    try:
        conn = sqlite3.connect('auditiq.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        if user and bcrypt.checkpw(
            password.encode('utf-8'),
            user[3].encode('utf-8')
        ):
            return True, {
                'id':         user[0],
                'name':       user[1],
                'email':      user[2],
                'created_at': user[4],
                'plan':       user[5]
            }
        return False, "Invalid email or password."
    except Exception as e:
        return False, str(e)

def reset_password(email, new_password):
    try:
        conn = sqlite3.connect('auditiq.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        if not user:
            conn.close()
            return False, "No account found with this email address."
        hashed = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        c.execute(
            'UPDATE users SET password = ? WHERE email = ?',
            (hashed, email)
        )
        conn.commit()
        conn.close()
        return True, "Password updated successfully."
    except Exception as e:
        return False, str(e)

def save_audit_history(user_email, company, standard,
                        industry, audit_type, findings, high_risk):
    try:
        conn = sqlite3.connect('auditiq.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO audit_history
            (user_email, company_name, standard, industry,
             audit_type, date, findings_count, high_risk_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_email, company, standard, industry,
            audit_type,
            datetime.now().strftime('%Y-%m-%d %H:%M'),
            findings, high_risk
        ))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_audit_history(user_email):
    try:
        conn = sqlite3.connect('auditiq.db')
        c = conn.cursor()
        c.execute('''
            SELECT * FROM audit_history
            WHERE user_email = ?
            ORDER BY date DESC
        ''', (user_email,))
        history = c.fetchall()
        conn.close()
        return history
    except:
        return []

init_db()