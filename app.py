from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import os
import json
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Import helper functions
from utils import validate_name, validate_date, format_name, format_firebase_data

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_replace_in_production')

# Initialize Firebase
try:
    # Path to your Firebase service account JSON file
    cred = credentials.Certificate('pds-studio-firebase-adminsdk-fbsvc-cb9200e4d3.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', 'https://pds-studio-default-rtdb.asia-southeast1.firebasedatabase.app/')
    })
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    # Fallback to local storage if Firebase initialization fails
    pass


@app.route('/')
def index():
    # Clear any flash messages when returning to the home page
    session.pop('_flashes', None)
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('firstName', '').strip()
        last_name = request.form.get('lastName', '').strip()
        date_of_birth = request.form.get('dateOfBirth', '').strip()
        print(date_of_birth)
        
        # Validate first name
        is_valid, message = validate_name(first_name)
        if not is_valid:
            flash(f'First name error: {message}', 'error')
            return redirect(url_for('index'))
            
        # Validate last name
        is_valid, message = validate_name(last_name)
        if not is_valid:
            flash(f'Last name error: {message}', 'error')
            return redirect(url_for('index'))
            
        # Validate date of birth
        is_valid, message, dob_obj = validate_date(date_of_birth)
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('index'))
            
        # Format names properly
        first_name_formatted = format_name(first_name)
        last_name_formatted = format_name(last_name)
        
        # Create visitor data dictionary
        visitor_data = {
            'firstName': first_name_formatted,
            'lastName': last_name_formatted,
            'dob': dob_obj.strftime('%Y-%m-%d')
        }
        
        try:
            # Process data for Firebase
            processed_data = format_firebase_data(visitor_data)
            
            # Store in session
            session['visitor'] = processed_data
            
            return redirect(url_for('rfid_instructions'))
            
        except ValueError as e:
            flash(f'Error processing data: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route('/rfid-instructions')
def rfid_instructions():
    # Check if visitor info exists in session
    visitor = session.get('visitor')
    if not visitor:
        flash('Please complete the registration form first.', 'error')
        return redirect(url_for('index'))
    
    return render_template('rfid_instructions.html', visitor=visitor)

@app.route('/submit', methods=['POST'])
def submit():
    visitor = session.get('visitor')
    if not visitor:
        flash('Session expired. Please register again.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get references to different paths in Firebase
        users_ref = db.reference('users')
        people_ref = db.reference('people')
        commands_ref = db.reference('commands/write_rfid')
        
        # Get user ID and timestamp
        user_id = visitor['user_id']
        timestamp_ms = visitor['timestamp_ms']
        
        # 1. Save legacy user data (for backward compatibility)
        users_ref.child(user_id).set(visitor['legacy_user_data'])
        
        # 2. Save new people data structure
        people_ref.child(user_id).set(visitor['people_data'])
        
        # 3. Create RFID write command
        command_id = f"cmd_{timestamp_ms}"
        command_data = {
            'type': 'write_rfid',
            'status': 'pending',
            'params': {
                'user_id': user_id,
                'location': 'enrollment-station'
            },
            'created_at': timestamp_ms,
            'updated_at': timestamp_ms,
            'created_by': 'webapp'
        }
        commands_ref.child(command_id).set(command_data)
        
        # Store command ID in session for status checking
        session['command_id'] = command_id
        
        flash('Registration successful! RFID tag writing initiated.', 'success')
    except Exception as e:
        app.logger.error(f"Error saving to Firebase: {e}")
        flash('An error occurred while registering. Please try again.', 'error')
        return redirect(url_for('rfid_instructions'))
    
    # Don't clear session yet, we'll need command_id for status checking
    # session.pop('visitor', None)
    
    # Redirect to waiting page instead of success
    return redirect(url_for('waiting'))

@app.route('/waiting')
def waiting():
    # Get command ID from session
    command_id = session.get('command_id')
    if not command_id:
        flash('No active RFID writing process found.', 'error')
        return redirect(url_for('index'))
    
    return render_template('waiting.html', command_id=command_id)

@app.route('/check_command_status/<command_id>')
def check_command_status(command_id):
    """Check the status of an RFID write command from the server side."""
    try:
        # Get the command from Firebase
        command_ref = db.reference(f'commands/write_rfid/{command_id}')
        command = command_ref.get()
        
        # If command exists, check its status
        if command:
            status = command.get('status', '')
            # Check for various completed statuses
            if status.lower() in ['completed', 'success', 'done', 'tag_written'] or 'complet' in status.lower():
                return jsonify({'status': 'completed'})
            elif status.lower() in ['failed', 'failure', 'error']:
                return jsonify({'status': 'failed', 'message': 'Failed to write RFID tag'})
            else:
                return jsonify({'status': status.lower()})
        else:
            # Try an alternative path
            alt_command_ref = db.reference(f'commands/{command_id}')
            alt_command = alt_command_ref.get()
            if alt_command:
                status = alt_command.get('status', '')
                if status.lower() in ['completed', 'success', 'done', 'tag_written'] or 'complet' in status.lower():
                    return jsonify({'status': 'completed'})
                else:
                    return jsonify({'status': status.lower()})
            
            # If we still can't find it, check if there's a tag with this user ID
            # This is a fallback in case the command status isn't updated but the tag was written
            time.sleep(1)  # Small delay to ensure Firebase has time to update
            tags_ref = db.reference('tags')
            tags = tags_ref.get()
            if tags:
                for tag_id, tag_data in tags.items():
                    if tag_data.get('owner_id') == command_id.replace('cmd_', ''):
                        return jsonify({'status': 'completed'})
            
            return jsonify({'status': 'pending'})
    except Exception as e:
        app.logger.error(f"Error checking command status: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/success')
def success():
    # Clear command ID from session when reaching success page
    command_id = session.pop('command_id', None)
    
    # Clear visitor data from session
    session.pop('visitor', None)
    
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True)