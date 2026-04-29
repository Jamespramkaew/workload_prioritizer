'use client';
import { useState } from 'react';
import { SUBJECT_COLORS } from './data';

export default function SubjectsManager({ subjects, tasks, onUpdate, onDelete, onCancel, t }) {
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  const [editColor, setEditColor] = useState(SUBJECT_COLORS[0]);

  const startEdit = (s) => {
    setEditingId(s.id);
    setEditName(s.name);
    setEditColor(s.color);
  };
  const cancelEdit = () => setEditingId(null);
  const saveEdit = () => {
    const trimmed = editName.trim();
    if (!trimmed) return;
    onUpdate(editingId, {
      name: trimmed,
      color: editColor,
      short: trimmed.slice(0, 3).toUpperCase() || 'SUB',
    });
    setEditingId(null);
  };

  const tryDelete = (s, count) => {
    if (count > 0) {
      window.alert(t.cannotDeleteSubject);
      return;
    }
    onDelete(s.id);
  };

  return (
    <form className="addtask subj-mgr" onSubmit={(e) => e.preventDefault()}>
      <div className="at-head">
        <div className="at-title">{t.manageSubjects}</div>
        <button type="button" className="at-x" onClick={onCancel} aria-label="close">✕</button>
      </div>

      <div className="subj-mgr-list">
        {subjects.map((s) => {
          const isEditing = editingId === s.id;
          const count = tasks.filter((task) => task.subjectId === s.id).length;
          const canDelete = subjects.length > 1;

          if (isEditing) {
            return (
              <div key={s.id} className="subj-mgr-row editing">
                <input className="at-input"
                       value={editName}
                       onChange={(e) => setEditName(e.target.value)}
                       autoFocus
                       onKeyDown={(e) => {
                         if (e.key === 'Enter') { e.preventDefault(); saveEdit(); }
                         if (e.key === 'Escape') cancelEdit();
                       }} />
                <div className="color-palette">
                  {SUBJECT_COLORS.map((c) => (
                    <button key={c} type="button"
                            className={`color-swatch ${editColor === c ? 'on' : ''}`}
                            style={{ background: c }}
                            onClick={() => setEditColor(c)}
                            aria-label={t.color} />
                  ))}
                </div>
                <div className="subj-mgr-actions">
                  <button type="button" className="btn-ghost btn-sm" onClick={cancelEdit}>{t.cancel}</button>
                  <button type="button" className="btn-primary btn-sm"
                          onClick={saveEdit} disabled={!editName.trim()}>
                    {t.save}
                  </button>
                </div>
              </div>
            );
          }

          return (
            <div key={s.id} className="subj-mgr-row">
              <span className="subj-color-swatch" style={{ background: s.color }} />
              <span className="subj-mgr-name">{s.name}</span>
              <span className="subj-mgr-count mono">{count} {t.tasksUsing}</span>
              <div className="subj-mgr-actions">
                <button type="button" className="btn-add-subj"
                        onClick={() => startEdit(s)}>
                  {t.edit}
                </button>
                <button type="button" className="btn-add-subj danger"
                        onClick={() => tryDelete(s, count)}
                        disabled={!canDelete}
                        title={!canDelete ? '' : ''}>
                  {t.deleteTask}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </form>
  );
}
