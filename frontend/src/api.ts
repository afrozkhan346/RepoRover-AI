import axios from "axios";

const BASE_URL = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 20000,
});

export type BackendRootResponse = {
  message?: string;
  name?: string;
  version?: string;
  status?: string;
};

export type RepositoryAnalysisResponse = {
  name: string;
  full_name: string;
  description?: string | null;
  owner: string;
  stars: number;
  forks: number;
  watchers: number;
  open_issues: number;
  language: string;
  languages: Record<string, number>;
  topics: string[];
  license: string;
  created_at: string;
  updated_at: string;
  size: number;
  default_branch: string;
  readme: string;
  recent_commits: Array<{
    sha: string;
    message: string;
    author: string;
    date: string;
  }>;
  file_count: number;
  file_structure: Array<{
    path: string;
    type?: string;
    size?: number;
  }>;
};

export async function fetchBackendRoot() {
  const { data } = await apiClient.get<BackendRootResponse>("/");
  return data;
}

export async function analyzeGithubRepository(githubUrl: string) {
  const { data } = await apiClient.post<RepositoryAnalysisResponse>("/api/github/analyze", {
    github_url: githubUrl,
  });
  return data;
}

export async function uploadRepositoryArchive(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<RepositoryAnalysisResponse>("/api/github/analyze-archive", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
}

export type ProjectUploadResponse = {
  message: string;
  project_path: string;
  files_saved: number;
  total_size: number;
};

export type AIExplanationResponse = {
  explanation: string;
  language: string | null;
  timestamp: string;
  pipeline?: string | null;
  model?: string | null;
  complexity_score?: number | null;
  key_concepts?: string[];
};

export type ProjectCloneResponse = {
  message: string;
  repo_url: string;
  project_path: string;
};

export type ProjectAnalyzeResponse = {
  language: string;
  total_files: number;
  files: Array<{
    name: string;
    path: string;
    extension: string;
  }>;
};

export type LearningPath = {
  id: number;
  title: string;
  description: string | null;
  difficulty: string;
  estimated_hours: number;
  icon: string | null;
  order_index: number;
  created_at: string;
};

export async function uploadProjectFiles(files: File[]) {
  const formData = new FormData();
  files.forEach((file) => {
    const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
    formData.append("files", file);
    formData.append("relative_paths", relativePath);
  });

  const { data } = await apiClient.post<ProjectUploadResponse>("/project/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
}

export async function explainCode(code: string, language?: string, question?: string) {
  const payload: Record<string, string | undefined> = { code, language, question };
  const { data } = await apiClient.post<AIExplanationResponse>("/api/ai/explain-code", payload);
  return data;
}

export async function cloneProjectFromGithub(repoUrl: string) {
  const formData = new FormData();
  formData.append("repo_url", repoUrl);
  const { data } = await apiClient.post<ProjectCloneResponse>("/project/clone", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
}

export async function analyzeProjectByName(projectName: string) {
  const { data } = await apiClient.get<ProjectAnalyzeResponse>(`/project/analyze/${encodeURIComponent(projectName)}`);
  return data;
}

export async function fetchLearningPaths() {
  const { data } = await apiClient.get<LearningPath[]>('/api/learning-paths');
  return data;
}
