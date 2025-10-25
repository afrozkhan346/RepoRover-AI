````markdown
# RepoRoverAI 🤖

**Your AI-powered co-pilot for exploring and learning from GitHub repositories!**

**[➡️ View the Live Demo Here](https://your-app-name.streamlit.app/)**

RepoRoverAI transforms any GitHub repository into an **interactive learning experience**, featuring guided lessons, code explainers, visualizations, and quizzes. Built for developers, students, and mentors, RepoRoverAI makes understanding complex repositories simple and engaging.

---

## 🌟 Features

### 🔐 **GitHub OAuth Sign-in**
- Securely log in using your GitHub account.
- Role-based access: Users are assigned roles (`mentor` or `student`) based on the `roles.json` file.

### 🗺️ **Interactive Repository Map**
- Visualize the structure of a repository with an interactive **vis-network graph**.
- Explore key files, lessons, and their relationships in an intuitive interface.

### 🎓 **RAG-Powered Guided Lessons**
- Automatically generates **structured, multi-step lessons** from repository contexts.
- Lessons include:
  - **Beginner-friendly explanations**.
  - **Step-by-step instructions** with cited sources.
  - **Summaries** and **hints** for better understanding.

### 🧑‍💻 **RAG-Powered Code Explainer**
- Provides detailed explanations for any selected file or function.
- Outputs include:
  - **Summary** of the code.
  - **Key points** and **examples**.
  - **Unit tests** and **sources** for reference.

### 🧪 **RAG-Powered Quizzes**
- Generates **interactive multiple-choice quizzes** based on lesson content.
- Features:
  - AI-generated **hints** for incorrect answers.
  - Auto-grading with detailed feedback.
  - Practice quizzes when insufficient context is available.

### ⚡ **Persistent Caching**
- Analyzed repositories are cached in **Google Firestore** for instant re-loads.
- First-time analysis is slower (due to API limits), but subsequent loads are lightning-fast.

### 📊 **Mentor Tools**
- Role-gated features for mentors (demoed in sidebar).

---

## 🛠️ How It Works

### 1️⃣ **Authentication**
- Users log in via **GitHub OAuth**.
- The app requests `read:user` and `user:email` scopes for secure authentication.
- Roles (`mentor` or `student`) are assigned based on the `data/roles.json` file.

### 2️⃣ **Repository Ingestion**
- Fetches repository details, file trees, and content using the **GitHub REST API**.
- Uses **semantic chunking** (by file type) to split files into meaningful contexts (e.g., functions, classes, sections).

### 3️⃣ **Retrieval-Augmented Generation (RAG)**
- Generates embeddings for all contexts using the **Google Gemini API**.
- Relevant contexts are retrieved using **embedding similarity**.
- These contexts are fed into the **Google Gemini API** to generate:
  - **Lessons**: Structured, multi-step guides.
  - **Explanations**: Detailed breakdowns of code.
  - **Quizzes**: Interactive, auto-graded MCQs.

### 4️⃣ **Interactive UI**
- Visualize the repository structure with an **interactive graph**.
- Click on nodes to explore files, generate lessons, or take quizzes.

---

## 🧑‍💻 Tech Stack

### **Frontend**
- **Streamlit**: For a responsive and interactive UI.
- **vis-network**: For graph-based repository visualization (embedded via `streamlit.components`).

### **Backend**
- **Google Gemini API**: For embeddings and content generation.
- **Google Firestore**: For caching analyzed repository data.
- **GitHub REST API**: For fetching repository details and content.

### **Other Tools**
- **Python**: Core programming language.
- **GitHub OAuth**: For secure user authentication.

---

## 🚀 Getting Started

### 1️⃣ **Clone the Repository**
```bash
git clone [https://github.com/afrozkhan346/RepoRover-AI.git](https://github.com/afrozkhan346/RepoRover-AI.git)
cd RepoRover-AI
````

### 2️⃣ **Set Up a Virtual Environment**

```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
# OR
source venv/bin/activate      # On macOS/Linux
```

### 3️⃣ **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 4️⃣ **Configure Secrets**

Create a `.streamlit/secrets.toml` file and add your credentials:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "YOUR_GEMINI_KEY"
GITHUB_TOKEN = "ghp_...YOUR_API_TOKEN_FOR_INGESTION..."

# GitHub OAuth App credentials
GITHUB_CLIENT_ID = "YOUR_OAUTH_CLIENT_ID"
GITHUB_CLIENT_SECRET = "YOUR_OAUTH_CLIENT_SECRET"

# Firestore service account key
[firestore]
type = "service_account"
project_id = "..."
# ... (Paste your full JSON key here) ...
```

### 5️⃣ **Run the App**

```bash
streamlit run app/streamlit_app.py
```

-----

## 🛡️ Hackathon Disclosures

### **Authentication**

  - **Method**: GitHub OAuth App flow (direct).
  - **Purpose**: Securely verifies the user's GitHub identity.
  - **Scopes**: `read:user` and `user:email`.
  - **Role-Gating**: Roles (`mentor` or `student`) are assigned based on the `data/roles.json` file.

### **AI Usage**

  - **Google Gemini API** is used for:
      - Generating embeddings (`text-embedding-004`).
      - Generating structured JSON for lessons, explanations, quizzes, and hints (`gemini-pro-latest`).
  - **Prompts** are carefully designed with few-shot examples and constraints to ensure outputs are grounded in the repository's content and to reduce hallucinations.

### **Reproducibility**

  - **Logs:** To ensure transparency, the app saves detailed JSON logs for all major AI generation steps (lessons, explanations, and quizzes) to the `data/lesson_logs/`, `data/explain_logs/`, and `data/quiz_logs/` directories (when run locally).
  - **Replay Script:** You can inspect the exact prompt and AI response from any log file using the provided replay script:
    ```bash
    python replay_log.py data/lesson_logs/<log_file_name>.json
    ```

-----

## 🤝 Contributing

We welcome contributions\! Please fork the repo, create a feature branch, and submit a pull request.

-----

## 📜 License

This project is licensed under the **MIT License**. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

```
MIT License
Copyright (c) 2025 RepoRoverAI Team
```

-----

## ❤️ Acknowledgments

  - **Halothon 2025 Hackathon**: This project was built as part of the hackathon.
  - **Google Gemini API**: For powering the AI capabilities.
  - **Streamlit**: For the interactive UI framework.

-----

Made with ❤️ by the RepoRoverAI Team.

```
```