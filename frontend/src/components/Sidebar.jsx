const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "dashboard" },
  { id: "new-application", label: "New Application", icon: "add_box" },
  { id: "applications", label: "Applications", icon: "fact_check" },
];

export default function Sidebar({ activeView, onNavigate, runStatus }) {
  return (
    <aside className="fixed left-0 top-0 z-50 flex h-full w-64 flex-col border-r border-primary-dark bg-primary-dark">
      <div className="flex items-center gap-3 border-b border-white/10 p-8">
        <div className="flex h-8 w-8 items-center justify-center bg-primary">
          <span className="material-symbols-outlined text-[20px] text-white">account_balance</span>
        </div>
        <span className="text-[20px] font-extrabold uppercase italic tracking-tight text-white">
          CareerPilot
        </span>
      </div>

      <nav className="flex-1 space-y-0.5 py-4">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onNavigate(item.id)}
            className={`nav-item w-full text-left ${activeView === item.id ? "nav-item-active" : ""}`}
          >
            <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
            <span className="text-[11px] font-bold uppercase tracking-wider">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="mt-auto space-y-4 border-t border-white/10 bg-black/20 p-6">
        <div className="flex items-center justify-around border border-white/10 py-2 text-white/60">
          <span className="material-symbols-outlined text-[18px]">notifications</span>
          <span className="material-symbols-outlined text-[18px]">help</span>
        </div>
        <div className="flex items-center gap-3 border border-white/10 bg-white/5 p-3">
          <div className="flex h-10 w-10 items-center justify-center border border-white/10 bg-white/10">
            <span className="material-symbols-outlined text-[20px] text-white/60">account_circle</span>
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="truncate text-[12px] font-bold uppercase tracking-tighter text-white">
              Aniket Dalal
            </p>
            <p className="text-[10px] font-bold uppercase tracking-widest text-primary-fixed-dim">
              {runStatus || "Ready"}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
