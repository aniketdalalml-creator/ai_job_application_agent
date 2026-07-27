import { useEffect, useMemo, useState } from "react";

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

function eventTone(type) {
  if (type.includes("error")) return "error";
  if (type.includes("complete") || type === "handoff") return "success";
  if (type.includes("tool")) return "tool";
  return "default";
}

export default function App() {
  const [companyName, setCompanyName] = useState("Anthropic");
  const [jobDescription, setJobDescription] = useState(SAMPLE_JOB);
  const [resumeText, setResumeText] = useState(SAMPLE_RESUME);
  const [runId, setRunId] = useState(null);
  const [run, setRun] = useState(null);
  const [events, setEvents] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!runId) return undefined;

    const source = new EventSource(`/api/runs/${runId}/events`);
    source.onmessage = (message) => {
      const event = JSON.parse(message.data);
      if (event.type === "run_finished") {
        source.close();
        fetch(`/api/runs/${runId}`)
          .then((response) => response.json())
          .then(setRun)
          .catch(() => {});
        return;
      }
      setEvents((current) => [...current, event]);
    };

    source.onerror = () => {
      source.close();
    };

    return () => source.close();
  }, [runId]);

  const handoff = useMemo(
    () => events.find((event) => event.type === "handoff")?.payload ?? null,
    [events],
  );

  const finalMaterials = run?.result?.finalMaterials;

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
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : String(submitError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Multi-agent pipeline</p>
          <h1>AI Job Application Agent</h1>
          <p className="subtitle">
            Researcher and Writer agents with Claude tool-calling, live web search, structured JSON
            handoff, and async Express job queue.
          </p>
        </div>
        <div className="status-pill">{run?.status || "idle"}</div>
      </header>

      <div className="layout">
        <section className="panel">
          <h2>New application run</h2>
          <form onSubmit={submitRun} className="form">
            <label>
              Company
              <input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Company name"
                required
              />
            </label>
            <label>
              Job description
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                rows={10}
                required
              />
            </label>
            <label>
              Resume
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                rows={10}
                required
              />
            </label>
            {error ? <p className="error">{error}</p> : null}
            <button type="submit" disabled={submitting}>
              {submitting ? "Queueing..." : "Queue application run"}
            </button>
          </form>
        </section>

        <section className="panel">
          <h2>Live agent trace</h2>
          <div className="trace">
            {events.length === 0 ? (
              <p className="muted">Submit a run to stream Researcher tool calls and Writer steps.</p>
            ) : (
              events.map((event, index) => (
                <article key={`${event.timestamp}-${index}`} className={`trace-item ${eventTone(event.type)}`}>
                  <div className="trace-meta">
                    <span>{event.agent || "pipeline"}</span>
                    <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <strong>{event.type}</strong>
                  <p>{event.message}</p>
                </article>
              ))
            )}
          </div>
        </section>

        <section className="panel">
          <h2>Handoff state</h2>
          <pre className="json-block">
            {handoff ? JSON.stringify(handoff, null, 2) : "Waiting for Researcher JSON handoff..."}
          </pre>
        </section>

        <section className="panel wide">
          <h2>Generated materials</h2>
          {!finalMaterials ? (
            <p className="muted">Cover letter and resume bullets appear when the run completes.</p>
          ) : (
            <div className="outputs">
              <div>
                <h3>Cover letter</h3>
                <pre className="text-block">{finalMaterials.coverLetter}</pre>
              </div>
              <div>
                <h3>Tailored resume bullets</h3>
                <ul>
                  {(finalMaterials.resumeBullets || []).map((bullet) => (
                    <li key={bullet}>{bullet}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
