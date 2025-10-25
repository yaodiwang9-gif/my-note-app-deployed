// ==================== Configuration ====================

// Auto-detect API URL based on current environment
const getApiUrl = () => {
    // 如果已经在 localhost:5000 上运行，API 应该是相对路径
    if (window.location.hostname === 'localhost' && window.location.port === '5000') {
        return '/api';  // 使用相对路径，不是 http://localhost:5000/api
    }
    // If running on localhost but different port (like 3000), use localhost API
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:5000/api';
    }
    // 其他情况保持不变...
    if (window.location.hostname.includes('manus-asia.computer')) {
        return 'https://5000-iy3dzuu9o9f507w5n343g-fae055ac.manus-asia.computer/api';
    }
    // Default fallback
    return '/api';  // 默认使用相对路径
};
const API_BASE_URL = getApiUrl();
let currentNoteId = null;
let notes = [];
let hasUnsavedChanges = false;

// ==================== DOM Elements ====================

const notesList = document.getElementById('notesList');
const newNoteBtn = document.getElementById('newNoteBtn');
const noteTitle = document.getElementById('noteTitle');
const noteContent = document.getElementById('noteContent');
const saveBtn = document.getElementById('saveBtn');
const deleteBtn = document.getElementById('deleteBtn');
const editorHeader = document.getElementById('editorHeader');
const editorActions = document.getElementById('editorActions');
const editorMeta = document.getElementById('editorMeta');
const editorStatus = document.getElementById('editorStatus');
const editorFooter = document.getElementById('editorFooter');
const confirmModal = document.getElementById('confirmModal');
const cancelBtn = document.getElementById('cancelBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const toast = document.getElementById('toast');

// ==================== Initialization ====================

document.addEventListener('DOMContentLoaded', () => {
    loadNotes();
    setupEventListeners();
});

function setupEventListeners() {
    newNoteBtn.addEventListener('click', createNewNote);
    saveBtn.addEventListener('click', saveCurrentNote);
    deleteBtn.addEventListener('click', showDeleteConfirmation);
    cancelBtn.addEventListener('click', closeModal);
    confirmDeleteBtn.addEventListener('click', deleteCurrentNote);
    noteTitle.addEventListener('input', onNoteChanged);
    noteContent.addEventListener('input', onNoteChanged);
    window.addEventListener('beforeunload', (e) => {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
}

// ==================== API Calls ====================

async function loadNotes() {
    try {
        const response = await fetch(`${API_BASE_URL}/notes`);
        if (!response.ok) throw new Error('Failed to load notes');
        
        notes = await response.json();
        renderNotesList();
        
        if (notes.length === 0) {
            clearEditor();
        }
    } catch (error) {
        console.error('Error loading notes:', error);
        showToast('加载笔记失败', 'error');
    }
}

async function createNewNote() {
    try {
        const newNote = {
            title: '新笔记',
            content: '开始记录你的想法...'  // 添加默认内容
        };
        
        const response = await fetch(`${API_BASE_URL}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newNote)
        });
        
        if (!response.ok) throw new Error('Failed to create note');
        
        const createdNote = await response.json();
        notes.unshift(createdNote);
        renderNotesList();
        selectNote(createdNote.id);
        showToast('新笔记已创建', 'success');
    } catch (error) {
        console.error('Error creating note:', error);
        showToast('创建笔记失败', 'error');
    }
}

async function saveCurrentNote() {
    if (!currentNoteId) return;
    
    try {
        const title = noteTitle.value.trim();
        const content = noteContent.value.trim();
        
        if (!title || !content) {
            showToast('标题和内容不能为空', 'error');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/notes/${currentNoteId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                content: content
            })
        });
        
        if (!response.ok) throw new Error('Failed to save note');
        
        const updatedNote = await response.json();
        
        // Update notes array
        const index = notes.findIndex(n => n.id === currentNoteId);
        if (index !== -1) {
            notes[index] = updatedNote;
        }
        
        hasUnsavedChanges = false;
        renderNotesList();
        selectNote(currentNoteId);
        updateEditorMeta();
        showToast('笔记已保存', 'success');
    } catch (error) {
        console.error('Error saving note:', error);
        showToast('保存笔记失败', 'error');
    }
}

async function deleteCurrentNote() {
    if (!currentNoteId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/notes/${currentNoteId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete note');
        
        notes = notes.filter(n => n.id !== currentNoteId);
        currentNoteId = null;
        renderNotesList();
        clearEditor();
        closeModal();
        showToast('笔记已删除', 'success');
    } catch (error) {
        console.error('Error deleting note:', error);
        showToast('删除笔记失败', 'error');
    }
}

// ==================== UI Rendering ====================

function renderNotesList() {
    if (notes.length === 0) {
        notesList.innerHTML = `
            <div class="empty-state">
                <p>暂无笔记</p>
                <p class="empty-hint">点击"新建笔记"开始创建</p>
            </div>
        `;
        return;
    }
    
    notesList.innerHTML = notes.map(note => `
        <div class="note-item ${note.id === currentNoteId ? 'active' : ''}" data-id="${note.id}">
            <div class="note-item-title">${escapeHtml(note.title)}</div>
            <div class="note-item-preview">${escapeHtml(note.content.substring(0, 60))}</div>
            <div class="note-item-date">${formatDate(note.updated_at)}</div>
        </div>
    `).join('');
    
    // Add click listeners
    document.querySelectorAll('.note-item').forEach(item => {
        item.addEventListener('click', () => {
            selectNote(parseInt(item.dataset.id));
        });
    });
}

function selectNote(noteId) {
    if (hasUnsavedChanges && currentNoteId !== noteId) {
        const confirmed = confirm('有未保存的更改，是否继续？');
        if (!confirmed) return;
    }
    
    currentNoteId = noteId;
    const note = notes.find(n => n.id === noteId);
    
    if (note) {
        noteTitle.value = note.title;
        noteContent.value = note.content;
        noteTitle.disabled = false;
        noteContent.disabled = false;
        editorActions.style.display = 'flex';
        hasUnsavedChanges = false;
        updateEditorMeta();
        renderNotesList();
    }
}

function clearEditor() {
    currentNoteId = null;
    noteTitle.value = '';
    noteContent.value = '';
    noteTitle.disabled = true;
    noteContent.disabled = true;
    editorActions.style.display = 'none';
    editorMeta.textContent = '';
    editorStatus.textContent = '';
    hasUnsavedChanges = false;
}

function updateEditorMeta() {
    if (!currentNoteId) return;
    
    const note = notes.find(n => n.id === currentNoteId);
    if (note) {
        const createdDate = formatDate(note.created_at);
        const updatedDate = formatDate(note.updated_at);
        editorMeta.textContent = `创建于 ${createdDate} | 更新于 ${updatedDate}`;
    }
}

function onNoteChanged() {
    if (currentNoteId) {
        hasUnsavedChanges = true;
        updateEditorStatus();
    }
}

function updateEditorStatus() {
    if (hasUnsavedChanges) {
        editorStatus.textContent = '✏️ 有未保存的更改';
        editorStatus.style.color = '#ef4444';
    } else {
        editorStatus.textContent = '✅ 已保存';
        editorStatus.style.color = '#10b981';
    }
}

// ==================== Modal ====================

function showDeleteConfirmation() {
    confirmModal.classList.add('show');
}

function closeModal() {
    confirmModal.classList.remove('show');
}

// ==================== Toast Notification ====================

function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ==================== Utility Functions ====================

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) {
        return '刚刚';
    } else if (diffMins < 60) {
        return `${diffMins}分钟前`;
    } else if (diffHours < 24) {
        return `${diffHours}小时前`;
    } else if (diffDays < 7) {
        return `${diffDays}天前`;
    } else {
        return date.toLocaleDateString('zh-CN');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

