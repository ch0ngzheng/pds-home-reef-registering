"""
Helper functions for the Home Reef Visitor Registration system.
You can import these in app.py to keep your main file cleaner.
"""

from datetime import datetime
import random
import string
import re

def validate_name(name):
    """Validate a name string."""
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long."
    
    # Check for invalid characters
    if not re.match(r'^[A-Za-z\-\'\s]+$', name):
        return False, "Name contains invalid characters. Only letters, hyphens, apostrophes, and spaces are allowed."
    
    return True, "Valid"

def validate_date(date_str):
    """Validate date format and return a datetime object if valid."""
    print(date_str)
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            date_obj = datetime.strptime(date_str, fmt)
            print(date_obj)
            
            # Check if date is in the past
            if date_obj > datetime.now():
                return False, "Date of birth cannot be in the future.", None
            
            return True, "Valid", date_obj
        except ValueError:
            pass
    
    return False, "Invalid date format. Please use YYYY-MM-DD or DD/MM/YYYY.", None
    
def format_name(name):
    """Format name with proper capitalization."""
    # Handle multi-part names like "van der Waals" or "O'Connor"
    parts = name.strip().split()
    formatted_parts = []
    
    for i, part in enumerate(parts):
        # Always capitalize first word
        if i == 0:
            formatted_parts.append(part.capitalize())
        # Check for prefixes that should remain lowercase
        elif part.lower() in ['van', 'der', 'von', 'de', 'la', 'du']:
            formatted_parts.append(part.lower())
        # Check for parts with apostrophes (like O'Connor)
        elif "'" in part:
            subparts = part.split("'")
            formatted_part = "'".join([sp.capitalize() for sp in subparts])
            formatted_parts.append(formatted_part)
        # Regular capitalization
        else:
            formatted_parts.append(part.capitalize())
    
    return " ".join(formatted_parts)

def generate_user_id(first_name, last_name, date_of_birth): # this part generates the UserID eg AWongYYMMDD
    """Generate a random alphanumeric check-in code."""
    first_letter = first_name[0]
    last_name = last_name.capitalize()

    return first_letter + last_name + date_of_birth.strftime('%y') + date_of_birth.strftime('%m') + date_of_birth.strftime('%d')

def format_firebase_data(visitor_data):
    """Format data for Firebase storage."""
    # Ensure required fields are present
    required_fields = ['firstName', 'lastName', 'dob']
    for field in required_fields:
        if field not in visitor_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Get current timestamp
    current_time = datetime.now()
    timestamp_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    timestamp_ms = int(current_time.timestamp() * 1000)
    
    # Process names
    visitor_data['firstName'] = format_name(visitor_data['firstName'])
    visitor_data['lastName'] = format_name(visitor_data['lastName'])
    visitor_data['name'] = f"{visitor_data['firstName']} {visitor_data['lastName']}"
    
    # Process date
    is_valid, message, dob = validate_date(visitor_data['dob'])
    if not is_valid:
        raise ValueError(message)
    
    dob_str = dob.strftime('%Y-%m-%d')
    
    # Generate user ID
    user_id = generate_user_id(visitor_data['firstName'], visitor_data['lastName'], dob)
    
    # Create the improved data structure
    
    # 1. Legacy users path (for backward compatibility)
    legacy_user_data = {
        'firstName': visitor_data['firstName'],
        'lastName': visitor_data['lastName'],
        'name': visitor_data['name'],
        'dob': dob_str,
        'userId': user_id,
        'timestamp': timestamp_str,
        'status': 'active'  # Changed from 'Pending' to 'active'
    }
    
    # 2. New people path structure
    people_data = {
        'user_id': user_id,
        'name': visitor_data['name'],
        'profile': {
            'firstName': visitor_data['firstName'],
            'lastName': visitor_data['lastName'],
            'dob': dob_str
        },
        'locations': {
            'current': 'enrollment-station'
        },
        'created_at': timestamp_ms,
        'updated_at': timestamp_ms,
        'status': 'active'
    }
    
    # Return all the data structures
    return {
        'user_id': user_id,
        'legacy_user_data': legacy_user_data,
        'people_data': people_data,
        'timestamp_ms': timestamp_ms
    }

