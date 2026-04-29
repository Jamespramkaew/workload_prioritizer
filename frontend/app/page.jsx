'use client';
import { useState, useMemo, useEffect } from 'react';
import { SUBJECTS, STRINGS, makeInitialTasks, weekDates, dateKey } from '../components/data';
import WorkloadChart from '../components/Chart';
import AddTaskForm from '../components/AddTaskForm';
import { TaskList, StatTile, OverloadBanner } from '../components/TaskList';
import {
  useTweaks, TweaksPanel, TweakSection,
  TweakSlider, TweakToggle, TweakRadio,
} from '../components/TweaksPanel';

const TWEAK_DEFAULTS = {
  language: 'en',
  chartType: 'stacked',
  capacity: 7,
  density: 'comfortable',
  dark: false,
};

export default function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const t = STRINGS[tweaks.language] || STRINGS.en;
  const [weekOffset, setWeekOffset] = useState(0);
  const [allTasks, setTasks] = useState(makeInitialTasks);
  const [showAdd, setShowAdd] = useState(false);
  const [showOnb, setShowOnb] = useState(true);
  const [onbCap, setOnbCap] = useState(tweaks.capacity);
  const [selectedTaskId, setSelectedTaskId] = useState(null);

  const dates = useMemo(() => weekDates(weekOffset), [weekOffset]);
  const todayDate = useMemo(() => new Date(2026, 3, 27), []);
  const dayLabels = t.dayLabels;
  const weekKeys = useMemo(() => dates.map(dateKey), [dates]);

  const tasks = useMemo(() => allTasks.filter((task) =>
    task.slots.some((s) => weekKeys.includes(s.dateKey)) ||
    weekKeys.includes(task.deadlineKey)
  ), [allTasks, weekKeys]);

  useEffect(() => {
    document.documentElement.lang = tweaks.language;
  }, [tweaks.language]);

  const dayTotals = useMemo(() => {
    const out = Array(7).fill(0);
    tasks.forEach((task) => task.slots.forEach((s) => {
      const idx = weekKeys.indexOf(s.dateKey);
      if (idx >= 0) out[idx] += s.hours;
    }));
    return out;
  }, [tasks, weekKeys]);

  const total = dayTotals.reduce((a, b) => a + b, 0);
  const overDays = dayTotals.map((v, i) => v > tweaks.capacity ? i : -1).filter((i) => i >= 0);
  const heaviestDay = dayTotals.indexOf(Math.max(...dayTotals));
  const heaviestHours = dayTotals[heaviestDay];

  const fmtRange = (ds) => {
    const a = ds[0], b = ds[6];
    const m = (d) => d.toLocaleDateString(tweaks.language === 'th' ? 'th-TH' : 'en-US', { month: 'short' });
    if (a.getMonth() === b.getMonth()) {
      return `${m(a)} ${a.getDate()}–${b.getDate()}, ${a.getFullYear()}`;
    }
    return `${m(a)} ${a.getDate()} – ${m(b)} ${b.getDate()}`;
  };

  const handleAddTask = ({ title, subjectId, deadlineKey, difficulty, importance, comfortable, hours, slots }) => {
    const task = {
      id: 't' + Date.now(),
      title, subjectId, deadlineKey, difficulty, importance, comfortable, hours,
      slots: slots || [],
    };
    setTasks((prev) => [...prev, task]);
    setShowAdd(false);
  };

  const handleMoveSlot = (taskId, slotIdx, newDateKey) => {
    setTasks((prev) => prev.map((task) => {
      if (task.id !== taskId) return task;
      const slots = task.slots.map((s, i) => i === slotIdx ? { ...s, dateKey: newDateKey } : s);
      return { ...task, slots };
    }));
  };

  const handleDeleteTask = (taskId) => {
    setTasks((prev) => prev.filter((task) => task.id !== taskId));
    if (selectedTaskId === taskId) setSelectedTaskId(null);
  };

  const handleUpdateTask = (updated) => {
    setTasks((prev) => prev.map((task) => task.id === updated.id ? updated : task));
  };

  const onbStart = () => {
    setTweak('capacity', onbCap);
    setShowOnb(false);
  };

  return (
    <div className={`app ${tweaks.density === 'compact' ? 'compact' : ''}`}
         data-theme={tweaks.dark ? 'dark' : 'light'}>

      {showOnb && (
        <div className="onb">
          <div className="onb-card">
            <div className="onb-mark"></div>
            <h1>{t.onboardingTitle}</h1>
            <p>{t.onboardingDesc}</p>
            <div className="onb-q">{t.capacityQ}</div>
            <div className="onb-cap">
              <span className="onb-cap-val mono">{onbCap}</span>
              <span className="onb-cap-unit">{t.hoursFull} {t.perDay}</span>
            </div>
            <input type="range" className="onb-slider"
                   min="2" max="12" step="1"
                   value={onbCap}
                   onChange={(e) => setOnbCap(Number(e.target.value))} />
            <button className="onb-start" onClick={onbStart}>{t.start} →</button>
          </div>
        </div>
      )}

      <div className="main">
        <div className="hdr">
          <div className="hdr-brand">
            <div className="brand-mark"></div>
            <div className="brand-text">
              <span className="brand-name">{t.appName}</span>
              <span className="brand-tag">{t.tagline}</span>
            </div>
          </div>
          <div className="week-nav">
            <button className="week-arrow" onClick={() => setWeekOffset((w) => w - 1)} aria-label="prev week">‹</button>
            <div className="week-label">
              <div className="week-range">{fmtRange(dates)}</div>
              <div className="week-sub mono">{t.week} · {dates[0].getDate()}–{dates[6].getDate()}</div>
            </div>
            <button className="week-arrow" onClick={() => setWeekOffset((w) => w + 1)} aria-label="next week">›</button>
            {weekOffset !== 0 && (
              <button className="week-today" onClick={() => setWeekOffset(0)}>{t.today}</button>
            )}
          </div>
        </div>

        <div className="stats">
          <StatTile label={t.totalThisWeek} value={total} unit={t.hours} />
          <StatTile label={t.tasksThisWeek} value={tasks.length} />
          <StatTile label={t.weekHigh}
                    value={heaviestHours > 0 ? `${dayLabels[heaviestDay]} ${heaviestHours}` : t.none}
                    unit={heaviestHours > 0 ? t.hours : ''}
                    tone={heaviestHours > tweaks.capacity ? 'warn' : ''} />
          <StatTile label={t.overdays}
                    value={overDays.length}
                    tone={overDays.length > 0 ? 'warn' : ''} />
        </div>

        <OverloadBanner overDays={overDays} dayLabels={dayLabels} dates={dates} t={t} />

        <div className="chart-section">
          <div className="chart-head">
            <div className="chart-title">
              {t.week} {t.chartType.toLowerCase()}
            </div>
            <div className="chart-toggle">
              <button className={tweaks.chartType === 'stacked' ? 'on' : ''}
                      onClick={() => setTweak('chartType', 'stacked')}>{t.stacked}</button>
              <button className={tweaks.chartType === 'bar' ? 'on' : ''}
                      onClick={() => setTweak('chartType', 'bar')}>{t.bar}</button>
              <button className={tweaks.chartType === 'heatmap' ? 'on' : ''}
                      onClick={() => setTweak('chartType', 'heatmap')}>{t.heatmap}</button>
            </div>
          </div>
          <WorkloadChart
            tasks={tasks}
            subjects={SUBJECTS}
            capacity={tweaks.capacity}
            dayLabels={dayLabels}
            dates={dates}
            todayDate={todayDate}
            chartType={tweaks.chartType}
            density={tweaks.density}
            t={t}
            onMoveSlot={handleMoveSlot}
            onSelectTask={(id) => setSelectedTaskId(id === selectedTaskId ? null : id)}
            selectedTaskId={selectedTaskId}
          />
        </div>

        <div className="legend">
          <div className="legend-title">{t.legend}</div>
          <div className="legend-row">
            {SUBJECTS.filter((s) => tasks.some((task) => task.subjectId === s.id)).map((s) => (
              <div key={s.id} className="legend-item">
                <span className="legend-dot" style={{ background: s.color }} />
                <span>{s.name}</span>
              </div>
            ))}
            {tasks.length === 0 && <span className="legend-item" style={{ color: 'var(--ink-3)' }}>—</span>}
          </div>
        </div>
      </div>

      <div className="side">
        <div className="side-head">
          <div className="side-title">{t.yourTasks}</div>
          <button className="btn-add" onClick={() => setShowAdd(true)}>{t.addTask}</button>
        </div>
        <TaskList
          tasks={tasks}
          subjects={SUBJECTS}
          dayLabels={dayLabels}
          dates={dates}
          capacity={tweaks.capacity}
          t={t}
          onDeleteTask={handleDeleteTask}
          onUpdateTask={handleUpdateTask}
          onSelectTask={(id) => setSelectedTaskId(id === selectedTaskId ? null : id)}
          selectedTaskId={selectedTaskId}
        />
      </div>

      {showAdd && (
        <div className="modal-bg" onClick={(e) => e.target === e.currentTarget && setShowAdd(false)}>
          <AddTaskForm
            subjects={SUBJECTS}
            dayLabels={dayLabels}
            dates={dates}
            capacity={tweaks.capacity}
            onAdd={handleAddTask}
            onCancel={() => setShowAdd(false)}
            t={t}
          />
        </div>
      )}

      <TweaksPanel title="Tweaks">
        <TweakSection label="Display" />
        <TweakRadio label="Language" value={tweaks.language}
                    options={[{value:'en',label:'EN'}, {value:'th',label:'TH'}]}
                    onChange={(v) => setTweak('language', v)} />
        <TweakRadio label="Chart" value={tweaks.chartType}
                    options={[
                      {value:'stacked', label:'Stack'},
                      {value:'bar', label:'Bar'},
                      {value:'heatmap', label:'Heat'}
                    ]}
                    onChange={(v) => setTweak('chartType', v)} />
        <TweakRadio label="Density" value={tweaks.density}
                    options={[{value:'compact',label:'Compact'},{value:'comfortable',label:'Comfortable'}]}
                    onChange={(v) => setTweak('density', v)} />
        <TweakToggle label="Dark mode" value={tweaks.dark}
                     onChange={(v) => setTweak('dark', v)} />
        <TweakSection label="Capacity" />
        <TweakSlider label="Hours per day" value={tweaks.capacity}
                     min={2} max={12} step={1} unit="h"
                     onChange={(v) => setTweak('capacity', v)} />
      </TweaksPanel>
    </div>
  );
}
