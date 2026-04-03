import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  ArrowRight,
  BarChart3,
  Brain,
  Code2,
  FolderOpen,
  GitBranch,
  Layers3,
  Sparkles,
  Wand2,
} from "lucide-react";

import "./App.css";
import {
  analyzeProjectByName,
  explainCode,
  cloneProjectFromGithub,
  fetchLearningPaths,
  uploadProjectFiles,
  type AIExplanationResponse,
  type LearningPath,
  type ProjectAnalyzeResponse,
  type ProjectCloneResponse,
  type ProjectUploadResponse,
} from "./api";

type ResultPayload = ProjectUploadResponse | ProjectCloneResponse | ProjectAnalyzeResponse | null;

type SavedWorkspaceState = {
  projectName: string;
  lastAction: string;
  payload: ResultPayload;
  analysisResult: unknown;
  savedAt: string;
};

const WORKSPACE_STORAGE_KEY = "repoorover:vite-workspace";
const LEARNING_PATHS_KEY = "repoorover:vite-learning-paths";

const SAMPLE_CODE = `function calculateScore(items) {
  const total = items.reduce((sum, item) => sum + item.value, 0);
  if (total > 100) {
    return total * 1.1;
  }
  return total;
}`;

const pillars = [
  {
    icon: GitBranch,
    title: "Repository intelligence",
    description: "Scan projects, map structure, and prepare the codebase for deeper analysis.",
  },
  {
    icon: BarChart3,
    title: "Backend metrics",
    description: "Use FastAPI outputs for summaries, quality signals, and analysis summaries.",
  },
  {
    icon: Wand2,
    title: "AST parsing",
    description: "Extract functions, classes, and imports from Python code first.",
  },
  {
    icon: Brain,
    title: "Explainable pipeline",
    description: "Move from raw files to semantic data ready for graph building and AI layers.",
  },
];

export default function App() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [projectName, setProjectName] = useState("your_project_name");
  const [projectFiles, setProjectFiles] = useState<File[]>([]);
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [loadingClone, setLoadingClone] = useState(false);
  const [loadingAnalyze, setLoadingAnalyze] = useState(false);
  const [tutorCode, setTutorCode] = useState(SAMPLE_CODE);
  const [tutorLanguage, setTutorLanguage] = useState("typescript");
  const [tutorQuestion, setTutorQuestion] = useState("");
  const [tutorResponse, setTutorResponse] = useState<AIExplanationResponse | null>(null);
  const [loadingTutor, setLoadingTutor] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<ResultPayload>(null);
  const [analysisResult, setAnalysisResult] = useState<unknown>(null);
  const [savedWorkspace, setSavedWorkspace] = useState<SavedWorkspaceState | null>(null);
  const [learningPaths, setLearningPaths] = useState<LearningPath[]>([]);
  const [learningPathsLoading, setLearningPathsLoading] = useState(true);

  useEffect(() => {
    if (!fileInputRef.current) {
      return;
    }

    fileInputRef.current.setAttribute("webkitdirectory", "");
    fileInputRef.current.setAttribute("directory", "");
  }, []);

  useEffect(() => {
    const saved = window.localStorage.getItem(WORKSPACE_STORAGE_KEY);
    if (!saved) {
      return;
    }

    try {
      setSavedWorkspace(JSON.parse(saved) as SavedWorkspaceState);
    } catch {
      window.localStorage.removeItem(WORKSPACE_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    const saved = window.localStorage.getItem(LEARNING_PATHS_KEY);
    if (saved) {
      try {
        setLearningPaths(JSON.parse(saved) as LearningPath[]);
      } catch {
        window.localStorage.removeItem(LEARNING_PATHS_KEY);
      }
    }

    const loadLearningPaths = async () => {
      try {
        const data = await fetchLearningPaths();
        const sorted = [...data].sort((a, b) => a.order_index - b.order_index);
        setLearningPaths(sorted);
        window.localStorage.setItem(LEARNING_PATHS_KEY, JSON.stringify(sorted));
      } catch {
        // Keep the dashboard usable even if the backend list is unavailable.
      } finally {
        setLearningPathsLoading(false);
      }
    };

    loadLearningPaths();
  }, []);

  const persistWorkspace = (nextPayload: ResultPayload, nextAnalysis: unknown, lastAction: string) => {
    const nextState: SavedWorkspaceState = {
      projectName,
      lastAction,
      payload: nextPayload,
      analysisResult: nextAnalysis,
      savedAt: new Date().toISOString(),
    };

    setSavedWorkspace(nextState);
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(nextState));
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async () => {
    if (!projectFiles.length) {
      setError("Choose a project folder before uploading.");
      return;
    }

    setLoadingUpload(true);
    setError(null);

    try {
      const response = await uploadProjectFiles(projectFiles);
      setPayload(response);
      setAnalysisResult(null);
      persistWorkspace(response, null, "upload");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to reach backend";
      setError(message);
    } finally {
      setLoadingUpload(false);
    }
  };

  const handleClone = async () => {
    if (!githubUrl.trim()) {
      setError("Enter a GitHub repository URL first.");
      return;
    }

    setLoadingClone(true);
    setError(null);

    try {
      const response = await cloneProjectFromGithub(githubUrl.trim());
      setPayload(response);
      setAnalysisResult(null);
      persistWorkspace(response, null, "clone");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to reach backend";
      setError(message);
    } finally {
      setLoadingClone(false);
    }
  };

  const handleAnalyzeProject = async () => {
    if (!projectName.trim()) {
      setError("Enter a project name first.");
      return;
    }

    setLoadingAnalyze(true);
    setError(null);

    try {
      const response = await analyzeProjectByName(projectName.trim());
      setPayload(response);
      setAnalysisResult(response);
      persistWorkspace(response, response, "project-analysis");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to analyze project";
      setError(message);
    } finally {
      setLoadingAnalyze(false);
    }
  };

  const analyzeCode = async () => {
    if (!projectName.trim()) {
      setError("Enter a project name first.");
      return;
    }

    setLoadingAnalyze(true);
    setError(null);

    try {
      const res = await axios.get(`http://127.0.0.1:8000/project/code-analysis/${encodeURIComponent(projectName.trim())}`);
      setAnalysisResult(res.data);
      persistWorkspace(payload, res.data, "code-analysis");
      console.log(res.data);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to analyze code";
      setError(message);
    } finally {
      setLoadingAnalyze(false);
    }
  };

  const handleExplainCode = async () => {
    if (!tutorCode.trim()) {
      setError("Paste code before requesting an explanation.");
      return;
    }

    setLoadingTutor(true);
    setError(null);

    try {
      const response = await explainCode(tutorCode, tutorLanguage, tutorQuestion.trim() || undefined);
      setTutorResponse(response);
      persistWorkspace(payload, response, "ai-tutor");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to explain code";
      setError(message);
    } finally {
      setLoadingTutor(false);
    }
  };

  const copyTutorExplanation = async () => {
    if (!tutorResponse?.explanation) {
      return;
    }

    await navigator.clipboard.writeText(tutorResponse.explanation);
  };

  const payloadPreview = useMemo(() => {
    if (analysisResult) {
      return analysisResult;
    }
    return payload;
  }, [analysisResult, payload]);

  const workspaceSummary = useMemo(() => {
    const latest = savedWorkspace ?? {
      projectName,
      lastAction: "none",
      payload,
      analysisResult,
      savedAt: null,
    };

    const totalFiles =
      typeof latest.payload === "object" && latest.payload !== null && "total_files" in latest.payload
        ? Number((latest.payload as ProjectAnalyzeResponse).total_files)
        : typeof latest.payload === "object" && latest.payload !== null && "files_saved" in latest.payload
          ? Number((latest.payload as ProjectUploadResponse).files_saved)
          : projectFiles.length;

    const projectPath =
      typeof latest.payload === "object" && latest.payload !== null && "project_path" in latest.payload
        ? (latest.payload as ProjectUploadResponse | ProjectCloneResponse).project_path
        : "n/a";

    return {
      ...latest,
      totalFiles,
      projectPath,
    };
  }, [analysisResult, payload, projectFiles.length, projectName, savedWorkspace]);

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero-copy">
          <div className="eyebrow">
            <Sparkles className="icon-sm" />
            React + Vite frontend
          </div>
          <h1>Repository intelligence, explanation, and parsing without Next.js.</h1>
          <p>
            The active frontend now runs as a standalone Vite app and talks directly to FastAPI for project
            ingestion, code analysis, and AST-ready parsing workflows.
          </p>
          <div className="hero-actions">
            <a className="primary-link" href="#workspace">
              Open workspace <ArrowRight className="icon-sm" />
            </a>
            <a className="secondary-link" href="#features">
              View capabilities
            </a>
          </div>
        </div>

        <aside className="hero-panel">
          <div className="panel-kicker">
            <Layers3 className="icon-sm" />
            Migration status
          </div>
          <ul>
            <li>Vite is the active UI runtime.</li>
            <li>FastAPI powers upload, clone, and analysis.</li>
            <li>Parser and AST services are ready for graph building.</li>
          </ul>
        </aside>
      </header>

      <section className="feature-grid" id="features">
        {pillars.map((pillar) => {
          const Icon = pillar.icon;
          return (
            <article key={pillar.title} className="feature-card">
              <div className="feature-icon">
                <Icon className="icon-md" />
              </div>
              <h2>{pillar.title}</h2>
              <p>{pillar.description}</p>
            </article>
          );
        })}
      </section>

      <section className="dashboard-section">
        <div className="section-heading dashboard-heading">
          <div>
            <h2>Dashboard</h2>
            <p>The migrated dashboard view now lives inside the Vite frontend and reads the latest workspace state.</p>
          </div>
        </div>

        <div className="dashboard-grid">
          <article className="dashboard-card">
            <span className="dashboard-label">Workspace status</span>
            <strong>{savedWorkspace ? "Loaded" : "No saved data"}</strong>
            <p>{savedWorkspace ? `Last action: ${workspaceSummary.lastAction}` : "Run upload, clone, or analysis to populate the dashboard."}</p>
          </article>
          <article className="dashboard-card">
            <span className="dashboard-label">Project name</span>
            <strong>{workspaceSummary.projectName || "n/a"}</strong>
            <p>{workspaceSummary.projectPath}</p>
          </article>
          <article className="dashboard-card">
            <span className="dashboard-label">File count</span>
            <strong>{workspaceSummary.totalFiles}</strong>
            <p>Derived from the latest upload or code-analysis response.</p>
          </article>
          <article className="dashboard-card">
            <span className="dashboard-label">Saved at</span>
            <strong>{workspaceSummary.savedAt ? new Date(workspaceSummary.savedAt).toLocaleString() : "n/a"}</strong>
            <p>Persisted in browser local storage.</p>
          </article>
        </div>
      </section>

      <section className="learning-section">
        <div className="section-heading learning-heading">
          <div>
            <h2>Learning paths</h2>
            <p>Public course structure from the backend, surfaced here as the next self-contained migration step.</p>
          </div>
        </div>

        <div className="learning-grid">
          {learningPathsLoading ? (
            <div className="learning-card learning-card-empty">Loading learning paths...</div>
          ) : learningPaths.length ? (
            learningPaths.map((path) => (
              <article key={path.id} className="learning-card">
                <div className="learning-card-top">
                  <span className="learning-icon">{path.icon || "📘"}</span>
                  <span className="learning-difficulty">{path.difficulty}</span>
                </div>
                <h3>{path.title}</h3>
                <p>{path.description || "Structured lessons for this path are available in the backend."}</p>
                <div className="learning-meta">
                  <span>{path.estimated_hours} hours</span>
                  <span>Order {path.order_index}</span>
                </div>
              </article>
            ))
          ) : (
            <div className="learning-card learning-card-empty">No learning paths available.</div>
          )}
        </div>
      </section>

      <section className="workspace" id="workspace">
        <div className="workspace-card">
          <div className="section-heading">
            <h2>Project workspace</h2>
            <p>Upload a folder, clone from GitHub, or analyze a saved project by name.</p>
          </div>

          <div className="form-row">
            <label htmlFor="github-url">GitHub URL</label>
            <input
              id="github-url"
              type="url"
              placeholder="https://github.com/owner/repo"
              value={githubUrl}
              onChange={(event) => setGithubUrl(event.target.value)}
            />
          </div>

          <div className="form-row">
            <label htmlFor="project-name">Project Name</label>
            <input
              id="project-name"
              type="text"
              placeholder="upload-project-20260403123456-ab12cd34"
              value={projectName}
              onChange={(event) => setProjectName(event.target.value)}
            />
          </div>

          <div className="upload-card">
            <input
              ref={fileInputRef}
              id="project-file"
              type="file"
              className="hidden-file-input"
              multiple
              onChange={(event) => setProjectFiles(Array.from(event.target.files ?? []))}
            />

            <button type="button" className="upload-picker" onClick={openFilePicker}>
              <span className="upload-plus" aria-hidden="true">
                +
              </span>
              <span>{projectFiles.length ? "Change project folder" : "Choose project folder"}</span>
            </button>

            <p className="file-selection">
              {projectFiles.length ? `Selected files: ${projectFiles.length}` : "No folder selected yet"}
            </p>
          </div>

          <div className="action-row">
            <button onClick={handleUpload} disabled={loadingUpload}>
              {loadingUpload ? "Uploading..." : "Upload"}
            </button>

            <button onClick={handleClone} disabled={loadingClone}>
              {loadingClone ? "Cloning..." : "Clone"}
            </button>

            <button onClick={handleAnalyzeProject} disabled={loadingAnalyze}>
              {loadingAnalyze ? "Analyzing..." : "Analyze Project"}
            </button>

            <button onClick={analyzeCode} disabled={loadingAnalyze} className="secondary-button">
              {loadingAnalyze ? "Analyzing..." : "Analyze Code"}
            </button>
          </div>

          {error ? <div className="error">{error}</div> : null}
        </div>

        <aside className="workspace-card result-card">
          <div className="section-heading">
            <h2>Latest output</h2>
            <p>Results are shown here after upload, clone, analyze, or code analysis.</p>
          </div>
          {payloadPreview ? (
            <pre>{JSON.stringify(payloadPreview, null, 2)}</pre>
          ) : (
            <div className="empty-state">
              <FolderOpen className="icon-lg" />
              <p>No output yet. Run one of the actions to load project data.</p>
            </div>
          )}
        </aside>
      </section>

      <section className="tutor-section">
        <div className="section-heading tutor-heading">
          <div>
            <h2>AI tutor</h2>
            <p>Code explanation is still powered by FastAPI, now surfaced directly in the Vite app.</p>
          </div>
        </div>

        <div className="tutor-grid">
          <div className="workspace-card">
            <div className="form-row">
              <label htmlFor="tutor-language">Language</label>
              <input id="tutor-language" value={tutorLanguage} onChange={(event) => setTutorLanguage(event.target.value)} />
            </div>

            <div className="form-row">
              <label htmlFor="tutor-question">Question</label>
              <input
                id="tutor-question"
                placeholder="What is this function doing?"
                value={tutorQuestion}
                onChange={(event) => setTutorQuestion(event.target.value)}
              />
            </div>

            <div className="form-row">
              <label htmlFor="tutor-code">Code</label>
              <textarea
                id="tutor-code"
                className="code-editor"
                value={tutorCode}
                onChange={(event) => setTutorCode(event.target.value)}
              />
            </div>

            <div className="action-row">
              <button onClick={handleExplainCode} disabled={loadingTutor}>
                {loadingTutor ? "Explaining..." : "Explain Code"}
              </button>
              <button onClick={() => setTutorCode(SAMPLE_CODE)} className="secondary-button" type="button">
                Load sample
              </button>
            </div>
          </div>

          <div className="workspace-card result-card">
            <div className="section-heading">
              <h2>Explanation</h2>
              <p>FastAPI output appears here and can be copied for later use.</p>
            </div>

            {tutorResponse ? (
              <div className="tutor-output">
                <div className="tutor-output-bar">
                  <div>
                    <strong>{tutorResponse.language ?? "Unknown"}</strong>
                    <span>{tutorResponse.pipeline ?? "pipeline"}</span>
                  </div>
                  <button type="button" className="secondary-button" onClick={copyTutorExplanation}>
                    Copy
                  </button>
                </div>
                <pre>{tutorResponse.explanation}</pre>
              </div>
            ) : (
              <div className="empty-state">
                <Brain className="icon-lg" />
                <p>Run the explanation pipeline to view the result here.</p>
              </div>
            )}
          </div>
        </div>
      </section>

      <footer className="footer-note">
        <Code2 className="icon-sm" />
        <span>Frontend migration continues in small, safe steps.</span>
      </footer>
    </div>
  );
}
