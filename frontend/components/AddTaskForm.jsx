'use client';
import { useState, useMemo, useEffect } from 'react';
import { estimateHours, daysToSplit, splitHours, dateKey, keyToDate, fmtTime, PROTO_TODAY } from './data';

function StarRow({ value, onChange, max = 5 }) {
  return (
    <div className="star-row">
      {Array.from({ length: max }).map((_, i) => (
        <button key={i} type="button"
                className={`star ${i < value ? 'on' : ''}`}
                onClick={() => onChange(i + 1)}
                aria-label={`${i + 1}`}>
          <span className="star-dot" />
        </button>
      ))}
    </div>
  );
}

function SessionRow({ session, idx, t, onChange, onRemove, canRemove, weekKeys }) {
  const inWeek = weekKeys.includes(session.dateKey);
  return (
    <div className={`sess-row ${!inWeek ? 'other-week' : ''}`}>
      <div className="sess-num mono">{idx + 1}</div>
      <input type="date" className="sess-date"
             value={session.dateKey}
             onChange={(e) => onChange({ ...session, dateKey: e.target.value })} />
      <div className="sess-time">
        <input type="time"
               value={fmtTime(session.startHour)}
               onChange={(e) => {
                 const [h, m] = e.target.value.split(':').map(Number);
                 onChange({ ...session, startHour: h + (m || 0) / 60 });
               }} />
      </div>
      <div className="sess-dur">
        <input type="number" min="0.5" max="12" step="0.5"
               value={session.hours}
               onChange={(e) => onChange({ ...session, hours: Number(e.target.value) || 0.5 })} />
        <span className="sess-unit">{t.hours}</span>
      </div>
      {canRemove ? (
        <button type="button" className="sess-x" onClick={onRemove} aria-label={t.removeSession}>✕</button>
      ) : <span></span>}
    </div>
  );
}

export default function AddTaskForm({ subjects, dayLabels, dates, capacity, onAdd, onCancel, t }) {
  const weekKeys = dates.map(dateKey);
  const [title, setTitle] = useState('');
  const [subjectId, setSubjectId] = useState(subjects[0].id);
  const [deadlineKey, setDeadlineKey] = useState(weekKeys[4]);
  const [difficulty, setDifficulty] = useState(3);
  const [importance, setImportance] = useState(3);
  const [comfortable, setComfortable] = useState(true);

  const autoHours = useMemo(
    () => estimateHours({ difficulty, importance, comfortable }),
    [difficulty, importance, comfortable]
  );

  const [mode, setMode] = useState('auto');
  const [sessions, setSessions] = useState([{ dateKey: weekKeys[0], startHour: 19, hours: 2 }]);

  useEffect(() => {
    if (mode !== 'auto') return;
    const nDays = daysToSplit(autoHours);
    const split = splitHours(autoHours, nDays);

    const dl = keyToDate(deadlineKey);
    const start = new Date(PROTO_TODAY);
    if (dl < start) start.setTime(dl.getTime());
    const candidates = [];
    const cursor = new Date(start);
    while (cursor <= dl) {
      candidates.push(dateKey(cursor));
      cursor.setDate(cursor.getDate() + 1);
    }
    const chosen = candidates.slice(0, nDays);
    while (chosen.length < nDays) chosen.push(deadlineKey);
    setSessions(split.map((h, i) => ({
      dateKey: chosen[i],
      startHour: 19,
      hours: h,
    })));
  }, [mode, autoHours, deadlineKey]);

  const subj = subjects.find((s) => s.id === subjectId);
  const totalHours = sessions.reduce((a, s) => a + s.hours, 0);

  const updateSession = (i, next) => {
    setMode('custom');
    setSessions((prev) => prev.map((s, idx) => idx === i ? next : s));
  };
  const removeSession = (i) => {
    setMode('custom');
    setSessions((prev) => prev.filter((_, idx) => idx !== i));
  };
  const addSession = () => {
    setMode('custom');
    setSessions((prev) => [...prev, { dateKey: deadlineKey, startHour: 20, hours: 1 }]);
  };

  const submit = (e) => {
    e.preventDefault();
    if (!title.trim() || sessions.length === 0) return;
    onAdd({
      title: title.trim(),
      subjectId, deadlineKey, difficulty, importance, comfortable,
      hours: totalHours,
      slots: sessions.map((s) => ({ dateKey: s.dateKey, startHour: s.startHour, hours: s.hours })),
    });
    setTitle('');
  };

  return (
    <form className="addtask" onSubmit={submit}>
      <div className="at-head">
        <div className="at-title">{t.addNewTask}</div>
        <button type="button" className="at-x" onClick={onCancel} aria-label="close">✕</button>
      </div>

      <div className="at-field">
        <label>{t.title}</label>
        <input className="at-input"
               value={title}
               onChange={(e) => setTitle(e.target.value)}
               placeholder="e.g. AWS Lambda assignment"
               autoFocus />
      </div>

      <div className="at-field">
        <label>{t.subject}</label>
        <div className="subject-grid">
          {subjects.map((s) => (
            <button key={s.id} type="button"
                    className={`subj-chip ${subjectId === s.id ? 'on' : ''}`}
                    onClick={() => setSubjectId(s.id)}>
              <span className="subj-dot" style={{ background: s.color }} />
              <span className="subj-name">{s.name}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="at-field">
        <label>{t.deadline}</label>
        <div className="deadline-row">
          {dayLabels.map((d, i) => (
            <button key={i} type="button"
                    className={`deadline-chip ${deadlineKey === weekKeys[i] ? 'on' : ''}`}
                    onClick={() => setDeadlineKey(weekKeys[i])}>
              <span className="dl-day">{d}</span>
              <span className="dl-date mono">{dates[i].getDate()}</span>
            </button>
          ))}
          <input type="date" className="deadline-other"
                 value={deadlineKey}
                 onChange={(e) => setDeadlineKey(e.target.value)} />
        </div>
      </div>

      <div className="at-row-2">
        <div className="at-field">
          <label>{t.difficulty}</label>
          <StarRow value={difficulty} onChange={setDifficulty} />
        </div>
        <div className="at-field">
          <label>{t.importance}</label>
          <StarRow value={importance} onChange={setImportance} />
        </div>
      </div>

      <div className="at-field">
        <label>{t.comfortable}</label>
        <div className="seg-2">
          <button type="button" className={comfortable ? 'on' : ''}
                  onClick={() => setComfortable(true)}>{t.yes}</button>
          <button type="button" className={!comfortable ? 'on' : ''}
                  onClick={() => setComfortable(false)}>{t.no}</button>
        </div>
      </div>

      <div className="at-field at-est">
        <div className="at-est-head">
          <label>{t.sessions}</label>
          <div className="seg-2 mini">
            <button type="button" className={mode === 'auto' ? 'on' : ''}
                    onClick={() => setMode('auto')}>{t.autoSchedule}</button>
            <button type="button" className={mode === 'custom' ? 'on' : ''}
                    onClick={() => setMode('custom')}>{t.customSchedule}</button>
          </div>
        </div>

        <div className="sess-list">
          <div className="sess-head">
            <span className="sess-h-num">#</span>
            <span className="sess-h-day">{t.date}</span>
            <span className="sess-h-time">{t.startTime}</span>
            <span className="sess-h-dur">{t.duration}</span>
            <span></span>
          </div>
          {sessions.map((s, i) => (
            <SessionRow key={i} session={s} idx={i}
                        t={t} weekKeys={weekKeys}
                        onChange={(next) => updateSession(i, next)}
                        onRemove={() => removeSession(i)}
                        canRemove={sessions.length > 1} />
          ))}
        </div>

        <div className="sess-foot">
          <button type="button" className="sess-add" onClick={addSession}>{t.addSession}</button>
          <span className="sess-total">
            {t.estimated}: <span className="mono">{totalHours}{t.hours}</span>
            <span className="sess-auto-hint mono"> · {t.autoCalc} {autoHours}{t.hours}</span>
          </span>
        </div>
      </div>

      <div className="at-actions">
        <button type="button" className="btn-ghost" onClick={onCancel}>{t.cancel}</button>
        <button type="submit" className="btn-primary"
                disabled={!title.trim() || sessions.length === 0}>
          {t.save}
        </button>
      </div>
    </form>
  );
}
