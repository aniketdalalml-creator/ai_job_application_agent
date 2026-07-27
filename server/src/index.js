import cors from "cors";
import dotenv from "dotenv";
import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import { v4 as uuidv4 } from "uuid";

import { enqueue } from "./queue.js";
import { getRun, listRuns, saveRun } from "./store.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, "../../.env") });
const PORT = Number(process.env.PORT || 3001);

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, service: "ai-job-application-agent" });
});

app.get("/api/runs", (_req, res) => {
  res.json(listRuns());
});

app.get("/api/runs/:id", (req, res) => {
  const run = getRun(req.params.id);
  if (!run) {
    res.status(404).json({ error: "Run not found" });
    return;
  }
  res.json(run);
});

app.post("/api/runs", (req, res) => {
  const companyName = String(req.body.companyName || "").trim();
  const jobDescription = String(req.body.jobDescription || "").trim();
  const resumeText = String(req.body.resumeText || "").trim();

  if (!companyName || !jobDescription || !resumeText) {
    res.status(400).json({
      error: "companyName, jobDescription, and resumeText are required",
    });
    return;
  }

  const id = uuidv4();
  const run = {
    id,
    status: "queued",
    companyName,
    jobDescription,
    resumeText,
    createdAt: new Date().toISOString(),
    events: [],
  };

  saveRun(run);
  enqueue(id);

  res.status(202).json({ id, status: run.status });
});

app.get("/api/runs/:id/events", (req, res) => {
  const run = getRun(req.params.id);
  if (!run) {
    res.status(404).json({ error: "Run not found" });
    return;
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders?.();

  let cursor = 0;
  /** @type {ReturnType<typeof setInterval> | undefined} */
  let timer;

  const sendEvents = () => {
    while (cursor < run.events.length) {
      const event = run.events[cursor];
      cursor += 1;
      res.write(`data: ${JSON.stringify(event)}\n\n`);
    }

    if (run.status === "completed" || run.status === "failed") {
      res.write(
        `data: ${JSON.stringify({
          type: "run_finished",
          status: run.status,
          timestamp: new Date().toISOString(),
        })}\n\n`,
      );
      res.end();
      if (timer) clearInterval(timer);
    }
  };

  sendEvents();
  timer = setInterval(sendEvents, 500);

  req.on("close", () => {
    clearInterval(timer);
  });
});

const frontendDist = path.resolve(__dirname, "../../frontend/dist");
app.use(express.static(frontendDist));
app.get("*", (_req, res, next) => {
  if (_req.path.startsWith("/api")) return next();
  res.sendFile(path.join(frontendDist, "index.html"), (error) => {
    if (error) {
      res.status(404).json({
        error: "Frontend not built. Run: cd frontend && npm install && npm run build",
      });
    }
  });
});

app.listen(PORT, () => {
  console.log(`AI Job Application Agent API listening on http://localhost:${PORT}`);
});
