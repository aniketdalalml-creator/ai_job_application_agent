import { useCallback, useEffect, useMemo, useState } from "react";

import CopilotPanel from "./components/CopilotPanel.jsx";
import DashboardView from "./components/DashboardView.jsx";
import NewApplicationView from "./components/NewApplicationView.jsx";
import ProcessingView from "./components/ProcessingView.jsx";
import ResultsView from "./components/ResultsView.jsx";
import Sidebar from "./components/Sidebar.jsx";

const SAMPLE_JOB = `Senior Machine Learning Engineer

We're looking for an ML Engineer to build production LLM applications and retrieval systems.

Requirements:
- 3+ years Python experience
- Experience with LLMs, prompt engineering, and RAG pipelines
- Strong software engineering practices (testing, APIs, CI)
- Ability to research companies and turn unstructured information into structured outputs
- Excellent written communication`;

const SAMPLE_RESUME = `Aniket — Machine Learning Engineer

Summary
ML engineer with experience building Python services, LLM applications, and data pipelines.

Experience
- Built multi-step LLM workflows (research → structure → generate → critique) for document automation
- Designed RAG pipelines over internal knowledge bases using embeddings and vector search
- Shipped FastAPI services with automated tests and CI
- Used OpenAI-compatible APIs for chat completions and JSON-mode structured extraction

Skills
Python, PyTorch, FastAPI, RAG, prompt engineering, SQL, Docker, Git`;

const HEADER_TITLES = {
  dashboard: "Executive Dashboard",
  "new-application": "New Application Entry",
  applications: "Application Registry",
  processing: "Live Optimization",
  results: "Application Analysis Report",
};

export default function App() {
  const [activeView, setActiveView] = useState("dashboard");
  const [companyName, setCompanyName] = useState("Anthropic");
  const [jobDescription, setJobDescription] = useState(SAMPLE_JOB);
  const [resumeText, setResumeText] = useState(SAMPLE_RESUME);
  const [runs, setRuns] = useState([]);
  const [runId, setRunId] = useState(null);
  const [run, setRun] = useState(null);
  const [events, setEvents] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const refreshRuns = useCallback(async () => {
    try {
      const response = await fetch("/api/runs");
      if (response.ok) {
        setRuns(await response.json());
      }
    } catch {
      // ignore fetch errors on dashboard refresh
    }
  }, []);

  useEffect(() => {
    refreshRuns();
  }, [refreshRuns]);

  useEffect(() => {
    if (!runId) return undefined;

    const source = new EventSource(`/api/runs/${runId}/events`);
    source.onmessage = (message) => {
      const event = JSON.parse(message.data);
      if (event.type === "run_finished") {
        source.close();
        fetch(`/api/runs/${runId}`)
          .then((response) => response.json())
          .then((payload) => {
            setRun(payload);
            setActiveView("results");
            refreshRuns();
          })
          .catch(() => {});
        return;
      }
      setEvents((current) => [...current, event]);
    };

    source.onerror = () => source.close();
    return () => source.close();
  }, [runId, refreshRuns]);

  useEffect(() => {
    if (run?.status === "running" || run?.status === "queued") {
      setActiveView("processing");
    }
  }, [run?.status]);

  const handoff = useMemo(
    () => events.find((event) => event.type === "handoff")?.payload ?? run?.result?.research ?? null,
    [events, run],
  );

  const finalMaterials = run?.result?.finalMaterials;
  const critique = run?.result?.critique;

  async function submitRun(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setEvents([]);
    setRun(null);

    try {
      const response = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ companyName, jobDescription, resumeText }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error || "Failed to queue run");
      }

      const body = await response.json();
      setRunId(body.id);
      setRun({ id: body.id, status: body.status, companyName, events: [] });
      setActiveView("processing");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : String(submitError));
    } finally {
      setSubmitting(false);
    }
  }

  function openRun(selectedRun) {
    setRun(selectedRun);
    setRunId(selectedRun.id);
    setEvents(selectedRun.events || []);
    setCompanyName(selectedRun.companyName);
    setActiveView(selectedRun.status === "completed" ? "results" : "processing");
  }

  function resetToNewApplication() {
    setRunId(null);
    setRun(null);
    setEvents([]);
    setError("");
    setActiveView("new-application");
  }

  function renderMainContent() {
    if (activeView === "dashboard") {
      return (
        <DashboardView
          runs={runs}
          onNewApplication={() => setActiveView("new-application")}
          onOpenRun={openRun}
        />
      );
    }

    if (activeView === "new-application") {
      return (
        <NewApplicationView
          companyName={companyName}
          setCompanyName={setCompanyName}
          jobDescription={jobDescription}
          setJobDescription={setJobDescription}
          resumeText={resumeText}
          setResumeText={setResumeText}
          submitting={submitting}
          error={error}
          onSubmit={submitRun}
        />
      );
    }

    if (activeView === "applications") {
      return (
        <DashboardView
          runs={runs}
          onNewApplication={() => setActiveView("new-application")}
          onOpenRun={openRun}
        />
      );
    }

    if (activeView === "processing") {
      return (
        <ProcessingView
          companyName={run?.companyName || companyName}
          events={events}
          runStatus={run?.status}
        />
      );
    }

    if (activeView === "results") {
      return (
        <ResultsView
          companyName={run?.companyName || companyName}
          handoff={handoff}
          finalMaterials={finalMaterials}
          critique={critique}
          revised={run?.result?.revised}
        />
      );
    }

    return null;
  }

  return (
    <div className="min-h-screen bg-surface-container-low">
      <Sidebar
        activeView={activeView === "processing" || activeView === "results" ? "applications" : activeView}
        onNavigate={setActiveView}
        runStatus={run?.status || "idle"}
      />

      <div className="pl-64 pr-96">
        <header className="fixed left-64 right-96 top-0 z-40 flex h-20 items-center justify-between border-b-2 border-primary bg-white px-10">
          <h1 className="text-[24px] font-black uppercase tracking-tight text-primary">
            {HEADER_TITLES[activeView] || "CareerPilot"}
          </h1>
          <div className="flex items-center gap-4">
            {activeView !== "new-application" ? (
              <button type="button" className="btn-primary" onClick={resetToNewApplication}>
                <span className="material-symbols-outlined text-[18px]">add</span>
                New Run
              </button>
            ) : null}
          </div>
        </header>

        <main className="min-h-screen p-10 pt-28">{renderMainContent()}</main>
      </div>

      <CopilotPanel
        companyName={run?.companyName || companyName}
        events={events}
        runStatus={run?.status}
        finalMaterials={finalMaterials}
        critique={critique}
        onQuickAction={resetToNewApplication}
      />
    </div>
  );
}
