import { useCallback, useEffect, useState } from "react";

import { api } from "./api.js";
import { useAuth } from "./auth.jsx";
import ApplicationsView from "./components/ApplicationsView.jsx";
import CopilotPanel from "./components/CopilotPanel.jsx";
import DashboardView from "./components/DashboardView.jsx";
import { JobsPage } from "./features/jobs";
import LoginView from "./components/LoginView.jsx";
import NewApplicationView from "./components/NewApplicationView.jsx";
import ProcessingView from "./components/ProcessingView.jsx";
import ProfileView from "./components/ProfileView.jsx";
import RegisterView from "./components/RegisterView.jsx";
import ResultsView from "./components/ResultsView.jsx";
import Sidebar from "./components/Sidebar.jsx";

const HEADER_TITLES = {
  dashboard: "Dashboard",
  profile: "Profile",
  jobs: "Job Matches",
  "new-application": "Paste a Job",
  applications: "Applications",
  processing: "Live Optimization",
  results: "Application Report",
  login: "Sign In",
  register: "Create Account",
};

const EMPTY_PROFILE = {
  resume_text: "",
  target_titles: [],
  skills: [],
  years_experience: 0,
  locations: [],
  work_mode: "hybrid",
  country: "us",
};

export default function App() {
  const { user, loading, setUser, logout } = useAuth();
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({ name: "", email: "", password: "" });
  const [authError, setAuthError] = useState("");
  const [authSubmitting, setAuthSubmitting] = useState(false);

  const [activeView, setActiveView] = useState("dashboard");
  const [profile, setProfile] = useState(EMPTY_PROFILE);
  const [profileSaving, setProfileSaving] = useState(false);
  const [resumeUploading, setResumeUploading] = useState(false);
  const [profileMessage, setProfileMessage] = useState({ error: "", success: "" });
  const [interview, setInterview] = useState(null);
  const [interviewMessages, setInterviewMessages] = useState([]);
  const [interviewBusy, setInterviewBusy] = useState(false);
  const [jobs, setJobs] = useState([]);
  const [jobFilter, setJobFilter] = useState("ALL");
  const [applications, setApplications] = useState([]);
  const [insights, setInsights] = useState(null);
  const [searching, setSearching] = useState(false);
  const [feedError, setFeedError] = useState("");

  const [companyName, setCompanyName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [jobLocation, setJobLocation] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [runId, setRunId] = useState(null);
  const [runKind, setRunKind] = useState("application");
  const [run, setRun] = useState(null);
  const [events, setEvents] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const refreshWorkspace = useCallback(async () => {
    const [nextProfile, nextJobs, nextApplications, nextInsights] = await Promise.all([
      api.getProfile(),
      api.listJobs(),
      api.listApplications(),
      api.insights(),
    ]);
    setProfile(nextProfile);
    setResumeText(nextProfile.resume_text || "");
    setJobs(nextJobs);
    setApplications(nextApplications);
    setInsights(nextInsights);
  }, []);

  useEffect(() => {
    if (!user) return undefined;
    refreshWorkspace().catch(() => {});
  }, [user, refreshWorkspace]);

  useEffect(() => {
    if (!runId) return undefined;
    const path = runKind === "search" ? `/api/searches/${runId}/events` : `/api/applications/${runId}/events`;
    const source = new EventSource(path);
    source.onmessage = (message) => {
      const event = JSON.parse(message.data);
      if (event.type === "run_finished") {
        source.close();
        refreshWorkspace().catch(() => {});
        if (runKind === "search") {
          setSearching(false);
          api
            .getSearch(runId)
            .then((payload) => {
              if (payload.status === "failed" || payload.error) {
                setFeedError(payload.error || "Job search failed.");
              }
              setActiveView("jobs");
            })
            .catch(() => {
              setFeedError(event.error || "Job search failed.");
              setActiveView("jobs");
            });
          return;
        }
        api
          .getApplication(runId)
          .then((payload) => {
            setRun(payload);
            setError(payload.error || "");
            setActiveView("results");
          })
          .catch(() => {
            setError(event.error || "Application prepare failed.");
            setActiveView("results");
          });
        return;
      }
      setEvents((current) => [...current, event]);
    };
    source.onerror = () => source.close();
    return () => source.close();
  }, [runId, runKind, refreshWorkspace]);

  const finalMaterials = run
    ? { coverLetter: run.cover_letter, resumeBullets: run.resume_bullets }
    : null;
  const handoff = run?.research || events.find((event) => event.type === "handoff")?.payload || null;
  const critique = run?.critique || null;
  const runFit = run?.fit || jobs.find((job) => job.id === run?.job_id)?.fit || null;
  const hasResume = Boolean((profile.resume_text || resumeText || "").trim());

  async function handleAuth(event) {
    event.preventDefault();
    setAuthSubmitting(true);
    setAuthError("");
    try {
      const nextUser =
        authMode === "register"
          ? await api.register({
              name: authForm.name,
              email: authForm.email,
              password: authForm.password,
            })
          : await api.login({ email: authForm.email, password: authForm.password });
      setUser(nextUser);
      setActiveView("profile");
    } catch (submitError) {
      setAuthError(submitError instanceof Error ? submitError.message : String(submitError));
    } finally {
      setAuthSubmitting(false);
    }
  }

  async function handleSaveProfile(event) {
    event.preventDefault();
    setProfileSaving(true);
    setProfileMessage({ error: "", success: "" });
    try {
      const saved = await api.saveProfile(profile);
      setProfile(saved);
      setResumeText(saved.resume_text || "");
      setProfileMessage({ error: "", success: "Profile saved." });
    } catch (saveError) {
      setProfileMessage({
        error: saveError instanceof Error ? saveError.message : String(saveError),
        success: "",
      });
    } finally {
      setProfileSaving(false);
    }
  }

  function seedInterview(nextInterview, nextProfile) {
    setInterview(nextInterview);
    const titles = (nextProfile.target_titles || []).join(", ") || "no titles yet";
    const messages = [
      {
        role: "assistant",
        content: `I pulled a draft from your resume (${titles}). I will ask about anything unclear.`,
      },
    ];
    if (nextInterview?.question) {
      messages.push({ role: "assistant", content: nextInterview.question });
    } else {
      messages.push({
        role: "assistant",
        content: "That draft looks complete. Edit the form or click Looks good — find jobs.",
      });
    }
    setInterviewMessages(messages);
  }

  function handleFieldEdit(field) {
    setInterview((current) => {
      if (!current) return current;
      return {
        ...current,
        resolved_fields: [...new Set([...(current.resolved_fields || []), field])],
        inferred_fields: (current.inferred_fields || []).filter((item) => item !== field),
        confidence: { ...(current.confidence || {}), [field]: 1 },
      };
    });
  }

  async function handleUploadResume(file) {
    setResumeUploading(true);
    setProfileMessage({ error: "", success: "" });
    try {
      const result = await api.uploadResume(file);
      setProfile(result.profile);
      setResumeText(result.profile.resume_text || "");
      seedInterview(result.interview, result.profile);
      setActiveView("profile");
      setProfileMessage({
        error: "",
        success: "Draft saved. Answer Copilot, skip to let it guess, or find jobs when it looks right.",
      });
    } catch (uploadError) {
      setProfileMessage({
        error: uploadError instanceof Error ? uploadError.message : String(uploadError),
        success: "",
      });
    } finally {
      setResumeUploading(false);
    }
  }

  async function handleInterview(action, message = "") {
    setInterviewBusy(true);
    setProfileMessage({ error: "", success: "" });
    if (action === "answer" && message.trim()) {
      setInterviewMessages((current) => [...current, { role: "user", content: message.trim() }]);
    }
    try {
      if (action === "confirm") {
        const saved = await api.saveProfile(profile);
        setProfile(saved);
        setResumeText(saved.resume_text || "");
        setInterview((current) =>
          current
            ? { ...current, done: true, question: null, question_field: null }
            : current,
        );
        await handleFindJobs();
        return;
      }
      const result = await api.profileChat({
        action,
        message,
        messages: interviewMessages.slice(-8),
        profile,
        interview,
      });
      setProfile(result.profile);
      setResumeText(result.profile.resume_text || "");
      setInterview(result.interview);
      if (result.assistant_message) {
        setInterviewMessages((current) => [...current, { role: "assistant", content: result.assistant_message }]);
      }
    } catch (chatError) {
      setProfileMessage({
        error: chatError instanceof Error ? chatError.message : String(chatError),
        success: "",
      });
    } finally {
      setInterviewBusy(false);
    }
  }

  async function handleFindJobs() {
    setSearching(true);
    setFeedError("");
    setEvents([]);
    try {
      const started = await api.startSearch();
      setRunKind("search");
      setRunId(started.id);
      setRun({ id: started.id, status: started.status, companyName: "Job search" });
      setActiveView("processing");
    } catch (searchError) {
      setSearching(false);
      setFeedError(searchError instanceof Error ? searchError.message : String(searchError));
    }
  }

  async function handlePrepare(job) {
    if (!hasResume) {
      setError("Add your resume on the Profile page before generating materials.");
      setFeedError("Add your resume on the Profile page before generating materials.");
      return;
    }
    setSubmitting(true);
    setError("");
    setEvents([]);
    try {
      const started = await api.prepareJob(job.id);
      setRunKind("application");
      setRunId(started.id);
      setRun({ id: started.id, status: started.status, company: job.company, title: job.title });
      setCompanyName(job.company);
      setActiveView("processing");
    } catch (prepareError) {
      setError(prepareError instanceof Error ? prepareError.message : String(prepareError));
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePasteJob(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const created = await api.createManualJob({
        company_name: companyName,
        job_description: jobDescription,
        title: jobTitle,
        location: jobLocation,
      });
      if (resumeText && resumeText !== profile.resume_text) {
        await api.saveProfile({ ...profile, resume_text: resumeText });
      }
      await handlePrepare({ id: created.id, company: companyName, title: jobTitle });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : String(submitError));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStatus(id, status) {
    const updated = await api.patchApplication(id, { status });
    setApplications((current) => current.map((item) => (item.id === id ? updated : item)));
    api.insights().then(setInsights).catch(() => {});
  }

  function openApplication(item) {
    setRun(item);
    setRunId(item.id);
    setRunKind("application");
    setEvents(item.events || []);
    setCompanyName(item.company);
    setActiveView(item.status === "generating" ? "processing" : "results");
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface text-[13px] font-semibold text-primary">
        Restoring session...
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-surface p-10">
        {authMode === "register" ? (
          <RegisterView
            name={authForm.name}
            setName={(value) => setAuthForm((current) => ({ ...current, name: value }))}
            email={authForm.email}
            setEmail={(value) => setAuthForm((current) => ({ ...current, email: value }))}
            password={authForm.password}
            setPassword={(value) => setAuthForm((current) => ({ ...current, password: value }))}
            submitting={authSubmitting}
            error={authError}
            onSubmit={handleAuth}
            onSwitch={() => {
              setAuthError("");
              setAuthMode("login");
            }}
          />
        ) : (
          <LoginView
            email={authForm.email}
            setEmail={(value) => setAuthForm((current) => ({ ...current, email: value }))}
            password={authForm.password}
            setPassword={(value) => setAuthForm((current) => ({ ...current, password: value }))}
            submitting={authSubmitting}
            error={authError}
            onSubmit={handleAuth}
            onSwitch={() => {
              setAuthError("");
              setAuthMode("register");
            }}
          />
        )}
      </div>
    );
  }

  function renderMainContent() {
    if (activeView === "dashboard") {
      return (
        <DashboardView
          user={user}
          profile={profile}
          insights={insights}
          applications={applications}
          onNewApplication={() => setActiveView("new-application")}
          onOpenApplication={openApplication}
          onFindJobs={() => setActiveView("jobs")}
        />
      );
    }
    if (activeView === "profile") {
      return (
        <ProfileView
          profile={profile}
          setProfile={setProfile}
          interview={interview}
          saving={profileSaving}
          uploading={resumeUploading}
          error={profileMessage.error}
          success={profileMessage.success}
          onSave={handleSaveProfile}
          onUpload={handleUploadResume}
          onFieldEdit={handleFieldEdit}
        />
      );
    }
    if (activeView === "jobs") {
      return (
        <JobsPage
          jobs={jobs}
          filter={jobFilter}
          setFilter={setJobFilter}
          searching={searching}
          error={feedError}
          hasResume={hasResume}
          onSearch={handleFindJobs}
          onPrepare={handlePrepare}
        />
      );
    }
    if (activeView === "new-application") {
      return (
        <NewApplicationView
          companyName={companyName}
          setCompanyName={setCompanyName}
          jobTitle={jobTitle}
          setJobTitle={setJobTitle}
          jobLocation={jobLocation}
          setJobLocation={setJobLocation}
          jobDescription={jobDescription}
          setJobDescription={setJobDescription}
          resumeText={resumeText}
          setResumeText={setResumeText}
          submitting={submitting}
          error={error}
          onSubmit={handlePasteJob}
        />
      );
    }
    if (activeView === "applications") {
      return (
        <ApplicationsView applications={applications} onOpen={openApplication} onStatus={handleStatus} />
      );
    }
    if (activeView === "processing") {
      return (
        <ProcessingView
          runKind={runKind}
          companyName={run?.company || run?.companyName || companyName || "search"}
          events={events}
          runStatus={run?.status || (searching ? "running" : "queued")}
          error={error || events.find((event) => event.type === "error")?.message || ""}
        />
      );
    }
    if (activeView === "results") {
      return (
        <ResultsView
          companyName={run?.company || companyName}
          handoff={handoff}
          finalMaterials={finalMaterials}
          critique={critique}
          revised={run?.revised}
          fit={runFit}
          error={run?.error || error}
        />
      );
    }
    return null;
  }

  const sidebarView =
    activeView === "processing" || activeView === "results" ? "applications" : activeView;

  return (
    <div className="min-h-screen bg-surface">
      <header className="fixed inset-x-0 top-0 z-50 flex h-16 items-center justify-between bg-surface/85 px-6 shadow-[0_1px_8px_rgba(0,0,0,0.04)] backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-on-primary">
            <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
          </span>
          <span className="text-[16px] font-semibold tracking-tight">Career Copilot</span>
        </div>
        <div className="flex items-center gap-3">
          <h1 className="hidden text-[14px] font-semibold text-on-surface-variant md:block">
            {HEADER_TITLES[activeView] || "Career Copilot"}
          </h1>
          <button type="button" className="btn-primary !py-2" onClick={() => setActiveView("jobs")}>
            <span className="material-symbols-outlined text-[18px]">travel_explore</span>
            Find jobs
          </button>
        </div>
      </header>

      <Sidebar
        activeView={sidebarView}
        onNavigate={setActiveView}
        user={user}
        runStatus={run?.status || "Ready"}
        onLogout={async () => {
          await logout();
          setActiveView("dashboard");
        }}
      />

      <div className="pl-72 pr-96">
        <main className="min-h-screen p-6 pt-24">{renderMainContent()}</main>
      </div>

      <CopilotPanel
        companyName={run?.company || companyName}
        events={events}
        runStatus={run?.status}
        finalMaterials={finalMaterials}
        critique={critique}
        onQuickAction={() => setActiveView("jobs")}
        mode={activeView === "profile" ? "profile" : "pipeline"}
        interview={interview}
        interviewMessages={interviewMessages}
        interviewBusy={interviewBusy}
        onInterviewSend={(text) => handleInterview("answer", text)}
        onInterviewSkip={() => handleInterview("skip")}
        onInterviewConfirm={() => handleInterview("confirm")}
      />
    </div>
  );
}
