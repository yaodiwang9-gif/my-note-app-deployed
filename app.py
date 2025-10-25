from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# 添加：配置静态文件文件夹
app.static_folder = '.'  # 当前目录作为静态文件目录

# Database configuration - 修复版
import os

# 在 Vercel 上使用内存数据库，在本地使用文件数据库
if 'VERCEL' in os.environ:
    # Vercel 环境：使用内存数据库（重启后数据丢失，但适合演示）
    DATABASE = ':memory:'
else:
    # 本地开发环境：使用文件数据库
    DATABASE = 'notes.db'


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    # 如果是内存数据库，每次连接都需要初始化表
    if DATABASE == ':memory:':
        init_db(conn)

    return conn


def init_db(conn=None):
    """Initialize the database with notes table"""
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    if should_close:
        conn.commit()
        conn.close()
    else:
        conn.commit()


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
def get_notes():
    """Get all notes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notes ORDER BY updated_at DESC')
        notes = cursor.fetchall()
        conn.close()
        
        return jsonify([
            {
                'id': note['id'],
                'title': note['title'],
                'content': note['content'],
                'created_at': note['created_at'],
                'updated_at': note['updated_at']
            }
            for note in notes
        ]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a single note by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
        note = cursor.fetchone()
        conn.close()
        
        if note is None:
            return jsonify({'error': 'Note not found'}), 404
        
        return jsonify({
            'id': note['id'],
            'title': note['title'],
            'content': note['content'],
            'created_at': note['created_at'],
            'updated_at': note['updated_at']
        }), 200
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO notes (title, content) VALUES (?, ?)',
            (title, content)
        )
        conn.commit()
        note_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'id': note_id,
            'title': title,
            'content': content,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }), 201
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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if note exists
        cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
        if cursor.fetchone() is None:
            conn.close()
            return jsonify({'error': 'Note not found'}), 404
        
        # Update the note
        cursor.execute(
            'UPDATE notes SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (title, content, note_id)
        )
        conn.commit()
        
        # Get updated note
        cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
        note = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'id': note['id'],
            'title': note['title'],
            'content': note['content'],
            'created_at': note['created_at'],
            'updated_at': note['updated_at']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a note"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if note exists
        cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
        if cursor.fetchone() is None:
            conn.close()
            return jsonify({'error': 'Note not found'}), 404
        
        # Delete the note
        cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Note deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

