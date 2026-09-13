const NAV_ITEMS = [
  { id: "dashboard", label: "Overview", icon: "dashboard" },
  { id: "profile", label: "Profile", icon: "badge" },
  { id: "jobs", label: "Job Matches", icon: "radar" },
];

export default function Sidebar({ activeView, onNavigate, user, runStatus, onLogout }) {
  return (
    <aside className="fixed bottom-0 left-0 top-16 z-40 flex w-72 flex-col bg-surface-container-low shadow-[1px_0_8px_rgba(0,0,0,0.02)]">
      <div className="flex flex-1 flex-col gap-4 px-4 py-4">
        <p className="px-3 text-[11px] font-medium uppercase tracking-wider text-outline">Workspace</p>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={`nav-item w-full text-left ${activeView === item.id ? "nav-item-active" : ""}`}
            >
              <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
              <span className="text-[14px] font-medium">{item.label}</span>
            </button>
          ))}
        </nav>
      </div>

      <div className="space-y-3 px-4 pb-5">
        <div className="flex items-center gap-3 rounded-2xl bg-surface-container p-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-fixed text-primary">
            <span className="material-symbols-outlined text-[20px]">account_circle</span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] font-semibold text-on-surface">{user?.name || "Guest"}</p>
            <p className="truncate text-[11px] text-on-surface-variant">{user?.email || runStatus || "Ready"}</p>
          </div>
        </div>
        <button type="button" className="btn-secondary w-full" onClick={onLogout}>
          Sign out
        </button>
      </div>
    </aside>
  );
}
