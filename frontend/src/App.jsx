import { useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  CircleDashed,
  ListChecks,
  Tag,
  TriangleAlert,
  CalendarClock,
  Activity,
  LayoutGrid,
  ChevronsLeft,
  ChevronsRight,
  ChevronDown,
  ChevronsDownUp,
  ChevronsUpDown,
  Loader2,
  Moon,
  Sun,
  Search,
  X,
  AlertCircle,
} from "lucide-react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000/api";
const SIDEBAR_ROW_HEIGHT = 40;

const GROUPS = [
  { key: "broken", label: "Broken", Icon: TriangleAlert },
  { key: "open", label: "Open", Icon: CircleDashed },
  { key: "kept", label: "Kept", Icon: CheckCircle2 },
];

const NAV_ITEMS = [{ key: "all", label: "All promises", Icon: LayoutGrid }, ...GROUPS];

function Sidebar({ open, setOpen, filter, setFilter, counts }) {
  const activeIndex = NAV_ITEMS.findIndex((item) => item.key === filter);

  return (
    <nav className={`sidebar ${open ? "" : "collapsed"}`} aria-label="Promise filters">
      <div className="sidebar-brand">
        <ListChecks size={24} aria-hidden="true" className="sidebar-brand-icon" />
        {open && <span className="brand-name">Promyx</span>}
      </div>
      <div className="sidebar-nav" role="group" aria-label="Filter by status">
        <div
          className="sidebar-indicator"
          style={{ transform: `translateY(${activeIndex * SIDEBAR_ROW_HEIGHT}px)` }}
          aria-hidden="true"
        />
        {NAV_ITEMS.map((item) => (
          <button
            key={item.key}
            type="button"
            className={`sidebar-item ${filter === item.key ? "active" : ""}`}
            aria-pressed={filter === item.key}
            onClick={() => setFilter(item.key)}
            title={open ? undefined : item.label}
          >
            <item.Icon size={16} aria-hidden="true" />
            {open && <span>{item.label}</span>}
            {open && item.key !== "all" && (
              <span className="sidebar-count">{counts[item.key]}</span>
            )}
          </button>
        ))}
      </div>
      <button
        type="button"
        className="sidebar-collapse"
        onClick={() => setOpen(!open)}
        aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
      >
        {open ? <ChevronsLeft size={16} aria-hidden="true" /> : <ChevronsRight size={16} aria-hidden="true" />}
        {open && <span>Collapse</span>}
      </button>
    </nav>
  );
}

function useCountUp(value) {
  const [display, setDisplay] = useState(value);
  const fromRef = useRef(value);

  useEffect(() => {
    const from = fromRef.current;
    if (from === value) return;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      fromRef.current = value;
      setDisplay(value);
      return;
    }
    const duration = 300;
    const start = performance.now();
    let frame;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(from + (value - from) * eased));
      if (t < 1) frame = requestAnimationFrame(tick);
      else fromRef.current = value;
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);

  return display;
}

function Stat({ Icon, count, label }) {
  const display = useCountUp(count);
  return (
    <div className="stat">
      <Icon size={18} aria-hidden="true" />
      <div><span className="num">{display}</span><span className="label">{label}</span></div>
    </div>
  );
}

function Row({ promise, onDecide, pendingDecision, justSaved, saveError }) {
  const decision = promise.final_decision;
  const overridden = promise.human_decision && promise.human_decision !== promise.tool_decision;
  const saving = pendingDecision != null;

  return (
    <div className={`row ${justSaved ? "row-saved" : ""}`}>
      <div className="row-main">
        <div className="row-meta">
          <span className="speaker">{promise.speaker}</span>
          <span className="meeting">{promise.meeting}</span>
        </div>
        <div className="promise-text">{promise.promise_text}</div>
        <div className="evidence">
          <span><Tag size={13} aria-hidden="true" /> <code>{promise.ticket || "none"}</code></span>
          <span><Activity size={13} aria-hidden="true" /> <code>{promise.ticket_status || "unknown"}</code></span>
          <span><CalendarClock size={13} aria-hidden="true" /> <code>{promise.deadline || "none"}</code></span>
        </div>
      </div>
      <div className="controls">
        <div className="decision-buttons" role="group" aria-label={`Decision for ${promise.speaker}'s promise`}>
          {GROUPS.map((g) => {
            const isPending = pendingDecision === g.key;
            return (
              <button
                key={g.key}
                type="button"
                className={decision === g.key ? `active ${g.key}` : ""}
                aria-pressed={decision === g.key}
                disabled={saving}
                onClick={() => onDecide(promise.id, g.key)}
              >
                {isPending ? (
                  <Loader2 size={14} aria-hidden="true" className="spin" />
                ) : (
                  <g.Icon size={14} aria-hidden="true" />
                )}
                {g.label}
              </button>
            );
          })}
        </div>
        {overridden && !saveError && <span className="overridden-tag">Overridden by reviewer</span>}
        {saveError && (
          <span className="row-error">
            <AlertCircle size={13} aria-hidden="true" /> {saveError.message}
            <button type="button" onClick={() => onDecide(promise.id, saveError.decision)}>Retry</button>
          </span>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [promises, setPromises] = useState(null);
  const [error, setError] = useState(null);
  const [pending, setPending] = useState({});
  const [rowErrors, setRowErrors] = useState({});
  const [justSaved, setJustSaved] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState("default");
  const [collapsedGroups, setCollapsedGroups] = useState(() => new Set(["kept"]));
  const [isDark, setIsDark] = useState(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches
  );

  const toggleGroup = (key) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  const allCollapsed = GROUPS.every((g) => collapsedGroups.has(g.key));
  const toggleAllGroups = () => {
    setCollapsedGroups(allCollapsed ? new Set() : new Set(GROUPS.map((g) => g.key)));
  };

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  const load = () => {
    setError(null);
    fetch(`${API_BASE}/promises/`)
      .then((r) => r.json())
      .then((data) => setPromises(data.promises))
      .catch(() => setError("Could not reach the backend. Is `python manage.py runserver` running?"));
  };

  useEffect(load, []);

  const decide = (id, decision) => {
    const previous = promises.find((p) => p.id === id);
    setPromises((prev) =>
      prev.map((p) =>
        p.id === id
          ? { ...p, human_decision: decision, final_decision: decision }
          : p
      )
    );
    setPending((prev) => ({ ...prev, [id]: decision }));
    setRowErrors((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
    fetch(`${API_BASE}/promises/${id}/override/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    })
      .then((r) => {
        if (!r.ok) throw new Error("save failed");
        setJustSaved((prev) => ({ ...prev, [id]: true }));
        setTimeout(() => {
          setJustSaved((prev) => {
            const next = { ...prev };
            delete next[id];
            return next;
          });
        }, 700);
      })
      .catch(() => {
        setPromises((prev) => prev.map((p) => (p.id === id ? previous : p)));
        setRowErrors((prev) => ({
          ...prev,
          [id]: { message: "Save failed.", decision },
        }));
      })
      .finally(() => {
        setPending((prev) => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
      });
  };

  if (error) {
    return (
      <div className="state-msg" role="status" aria-live="polite">
        <p>{error}</p>
        <button type="button" onClick={load}>Try again</button>
      </div>
    );
  }
  if (!promises) {
    return (
      <div className="page">
        <div className="skeleton-group" role="status" aria-live="polite">
          <span className="visually-hidden">Loading promises...</span>
          {Array.from({ length: 4 }).map((_, i) => (
            <div className="skeleton-row" key={i}>
              <div className="skeleton-bar" style={{ width: "30%" }} />
              <div className="skeleton-bar" style={{ width: "70%" }} />
              <div className="skeleton-bar" style={{ width: "45%" }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const counts = { kept: 0, broken: 0, open: 0 };
  for (const p of promises) counts[p.final_decision]++;
  const visibleGroups = filter === "all" ? GROUPS : GROUPS.filter((g) => g.key === filter);

  const q = query.trim().toLowerCase();
  const searched = q
    ? promises.filter(
        (p) =>
          p.speaker.toLowerCase().includes(q) ||
          (p.ticket || "").toLowerCase().includes(q)
      )
    : promises;

  const sortRows = (rows) => {
    if (sortBy === "deadline") {
      return [...rows].sort((a, b) => (a.deadline || "9999").localeCompare(b.deadline || "9999"));
    }
    if (sortBy === "speaker") {
      return [...rows].sort((a, b) => a.speaker.localeCompare(b.speaker));
    }
    return rows;
  };

  const groupsWithRows = visibleGroups.map((g) => ({
    ...g,
    rows: sortRows(searched.filter((p) => p.final_decision === g.key)),
  }));
  const totalVisible = groupsWithRows.reduce((sum, g) => sum + g.rows.length, 0);

  return (
    <div className="layout">
      <Sidebar
        open={sidebarOpen}
        setOpen={setSidebarOpen}
        filter={filter}
        setFilter={setFilter}
        counts={counts}
      />
      <div className="page">
        <header className="page-header">
          <div>
            <div className="brand-lockup">
              <ListChecks size={26} aria-hidden="true" className="brand-lockup-icon" />
              <span className="brand-mark">Promyx</span>
            </div>
            <h1>Promise Tracker</h1>
            <span className="subtitle">Human review</span>
          </div>
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setIsDark((v) => !v)}
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          >
            {isDark ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
          </button>
        </header>

        <div className="stats">
          <Stat Icon={TriangleAlert} count={counts.broken} label="Broken" />
          <Stat Icon={CircleDashed} count={counts.open} label="Open" />
          <Stat Icon={CheckCircle2} count={counts.kept} label="Kept" />
        </div>

        {promises.length > 0 && (
          <div className="toolbar">
            <div className="search-box">
              <Search size={14} aria-hidden="true" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search speaker or ticket"
                aria-label="Search speaker or ticket"
              />
              {query && (
                <button type="button" onClick={() => setQuery("")} aria-label="Clear search">
                  <X size={13} aria-hidden="true" />
                </button>
              )}
            </div>
            <select
              className="sort-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              aria-label="Sort promises"
            >
              <option value="default">Sort: default</option>
              <option value="deadline">Sort: deadline</option>
              <option value="speaker">Sort: speaker</option>
            </select>
            <button type="button" className="collapse-all" onClick={toggleAllGroups}>
              {allCollapsed ? <ChevronsUpDown size={14} aria-hidden="true" /> : <ChevronsDownUp size={14} aria-hidden="true" />}
              {allCollapsed ? "Expand all" : "Collapse all"}
            </button>
          </div>
        )}

        <main>
          {promises.length === 0 && (
            <p className="state-msg">No promises tracked yet. Run `python src/store.py` to load extracted promises.</p>
          )}
          {promises.length > 0 && totalVisible === 0 && (
            <p className="state-msg">
              {q ? `No promises match "${query}".` : `No ${filter} promises.`}
            </p>
          )}
          {groupsWithRows.map((g) => {
            if (g.rows.length === 0) return null;
            const isCollapsed = collapsedGroups.has(g.key);
            return (
              <section className={`group ${g.key}`} key={g.key} aria-label={`${g.label} promises`}>
                <h2>
                  <button
                    type="button"
                    className="group-toggle"
                    onClick={() => toggleGroup(g.key)}
                    aria-expanded={!isCollapsed}
                  >
                    <g.Icon size={15} aria-hidden="true" />
                    {g.label} ({g.rows.length})
                    <ChevronDown size={15} aria-hidden="true" className="group-chevron" />
                  </button>
                </h2>
                <div className={`group-rows ${isCollapsed ? "collapsed" : ""}`}>
                  <div className="group-rows-inner">
                    {g.rows.map((p) => (
                      <Row
                        key={p.id}
                        promise={p}
                        onDecide={decide}
                        pendingDecision={pending[p.id]}
                        justSaved={justSaved[p.id]}
                        saveError={rowErrors[p.id]}
                      />
                    ))}
                  </div>
                </div>
              </section>
            );
          })}
        </main>
      </div>
    </div>
  );
}
