from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 配置静态文件文件夹
app.static_folder = '.'  # 当前目录作为静态文件目录

# JSON 文件存储方案
DATABASE_FILE = '/tmp/notes.json'


def init_db():
    """Initialize the database with empty list"""
    try:
        if not os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'w') as f:
                json.dump([], f)
    except Exception as e:
        print(f"Init DB error: {e}")


def get_notes():
    """Get all notes from JSON file"""
    try:
        with open(DATABASE_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


def save_notes(notes):
    """Save notes to JSON file"""
    try:
        with open(DATABASE_FILE, 'w') as f:
            json.dump(notes, f, indent=2)
        return True
    except Exception as e:
        print(f"Save notes error: {e}")
        return False


def get_next_id(notes):
    """Get next available ID"""
    if not notes:
        return 1
    return max(note['id'] for note in notes) + 1


# Initialize database on startup
init_db()


@app.route('/')
def index():
    """Serve the main frontend page"""
    return app.send_static_file('index.html')


@app.route('/<path:path>')
def serve_static_files(path):
    """Serve other static files (CSS, JS, etc)"""
    return app.send_static_file(path)


# ==================== API Endpoints ====================

@app.route('/api/notes', methods=['GET'])
def get_notes_api():
    """Get all notes"""
    try:
        notes = get_notes()
        # 按更新时间倒序排列
        notes.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return jsonify(notes), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a single note by ID"""
    try:
        notes = get_notes()
        note = next((n for n in notes if n['id'] == note_id), None)

        if note is None:
            return jsonify({'error': 'Note not found'}), 404

        return jsonify(note), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.get_json()

        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400

        title = data.get('title', '').strip()
        content = data.get('content', '').strip()

        if not title or not content:
            return jsonify({'error': 'Title and content cannot be empty'}), 400

        notes = get_notes()
        new_note = {
            'id': get_next_id(notes),
            'title': title,
            'content': content,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        notes.append(new_note)

        if save_notes(notes):
            return jsonify(new_note), 201
        else:
            return jsonify({'error': 'Failed to save note'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update an existing note"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        title = data.get('title', '').strip()
        content = data.get('content', '').strip()

        if not title or not content:
            return jsonify({'error': 'Title and content cannot be empty'}), 400

        notes = get_notes()
        note_index = next((i for i, n in enumerate(notes) if n['id'] == note_id), -1)

        if note_index == -1:
            return jsonify({'error': 'Note not found'}), 404

        # Update the note
        notes[note_index]['title'] = title
        notes[note_index]['content'] = content
        notes[note_index]['updated_at'] = datetime.now().isoformat()

        if save_notes(notes):
            return jsonify(notes[note_index]), 200
        else:
            return jsonify({'error': 'Failed to update note'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a note"""
    try:
        notes = get_notes()
        note_index = next((i for i, n in enumerate(notes) if n['id'] == note_id), -1)

        if note_index == -1:
            return jsonify({'error': 'Note not found'}), 404

        # Delete the note
        deleted_note = notes.pop(note_index)

        if save_notes(notes):
            return jsonify({'message': 'Note deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete note'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'storage': 'json'}), 200


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)