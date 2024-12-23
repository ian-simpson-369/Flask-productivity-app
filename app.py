from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
import pandas as pd
import random
import json
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timetracker.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    stopwatches = db.relationship('Stopwatch', backref='user', lazy=True)

class Stopwatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    target_time = db.Column(db.Integer, nullable=False)  # in minutes
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    records = db.relationship('Record', backref='stopwatch', lazy=True)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stopwatch_id = db.Column(db.Integer, db.ForeignKey('stopwatch.id'), nullable=False)
    completion_date = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    duration = db.Column(db.Integer, nullable=False)  # actual duration in minutes

# Sample Mussar quotes
MUSSAR_QUOTES = [
    "Ben Zoma said - Who is wise? One who learns from every person.",
    "Shelomo HaMelekh said - The beginning of wisdom is the fear of Heaven.",
    "Shammai said - Say little and do much.",
    "Rambam Hilkhot De'ot 5:13 - A Torah Sage [should conduct] his business dealings with honesty and good faith. When [his] answer is no, he says, no; when [his answer] is yes, he says, yes.",
    "Rabbi Yaron Reuven shlita - Because of the sin of Pgam HaBrit a person could actually lose his destined wife"
    # Add more quotes as needed
]

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        # Very basic authentication - you'd want better security in production
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('index'))
            
        return 'Invalid username or password'
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            return 'Username already exists'
            
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    quote = random.choice(MUSSAR_QUOTES)
    stopwatches = Stopwatch.query.filter_by(user_id=session['user_id']).all()

    # If no stopwatches exist, create some sample ones
    if not stopwatches:
        sample_watches = [
            Stopwatch(name="Study Torah", target_time=30, user_id=session['user_id']),
            Stopwatch(name="Exercise", target_time=45, user_id=session['user_id']),
            Stopwatch(name="Learning", target_time=60, user_id=session['user_id'])
        ]
        db.session.add_all(sample_watches)
        db.session.commit()
        stopwatches = sample_watches

    return render_template('index.html', quote=quote, stopwatches=stopwatches)

@app.route('/api/stopwatch', methods=['POST'])
def add_stopwatch():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    new_stopwatch = Stopwatch(
        name=data.get('name'),
        target_time=data.get('target_time'),
        user_id=session['user_id']
    )
    db.session.add(new_stopwatch)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/stopwatch/<int:stopwatch_id>', methods=['DELETE'])
def delete_stopwatch(stopwatch_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    stopwatch = Stopwatch.query.filter_by(id=stopwatch_id, user_id=session['user_id']).first()
    if not stopwatch:
        return jsonify({'error': 'Stopwatch not found'}), 404
    
    db.session.delete(stopwatch)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/stopwatch/<int:stopwatch_id>/complete', methods=['POST'])
def complete_stopwatch(stopwatch_id):
    try:
        duration = request.json.get('duration')

        if duration is None:
                return jsonify({'error': 'Duration is required'}), 400
    
        record = Record(stopwatch_id=stopwatch_id, duration=duration)
        db.session.add(record)
        db.session.commit()
    
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error completing stopwatch: {e}")
        return jsonify({'error': str(e)}), 500

    
@app.route('/api/stats')
def get_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'})
    try:
        # Get all records for user's stopwatches
        user_stopwatches = Stopwatch.query.filter_by(user_id=session['user_id']).all()
        stopwatch_ids = [sw.id for sw in user_stopwatches]
    
        # Create DataFrame from records
        records = Record.query.filter(Record.stopwatch_id.in_(stopwatch_ids)).all()

        if not records:
            print("No records found")
            return jsonify({
                'weekly': {},
                'monthly': {}
            })
    
        df = pd.DataFrame([{
            'stopwatch_id': r.stopwatch_id,
            'completion_date': r.completion_date,
            'duration': r.duration
        } for r in records])

        # Ensure completion_date is datetime
        df['completion_date'] = pd.to_datetime(df['completion_date'])

        # Calculate weekly stats
    
        weekly_stats = df.groupby(pd.Grouper(key='completion_date', freq='W'))['stopwatch_id'].count()
        monthly_stats = df.groupby(pd.Grouper(key='completion_date', freq='ME'))['stopwatch_id'].count()
        
        # Convert to serializable format
        weekly_data = {d.strftime('%Y-%m-%d'): int(count) for d, count in weekly_stats.items()}
        monthly_data = {d.strftime('%Y-%m'): int(count) for d, count in monthly_stats.items()}

        return jsonify({
            'weekly': weekly_data,
            'monthly': monthly_data
        })
    
    except Exception as e:
        print(f"Error processing stats: {str(e)}")
        return jsonify({
            'error': str(e),
            'weekly': {},
            'monthly': {}
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)