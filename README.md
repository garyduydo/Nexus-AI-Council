# Nexus AI - Intelligent AI Agent System

![Nexus AI Logo](https://raw.githubusercontent.com/nexus-ai/nexus-ai/main/logo.png)

## Table of Contents
- [Nexus AI - Intelligent AI Agent System](#nexus-ai---intelligent-ai-agent-system)
  - [Table of Contents](#table-of-contents)
  - [1. Overview](#1-overview)
  - [2. Product Vision](#2-product-vision)
  - [3. Target Audience](#3-target-audience)
  - [4. Business Objectives](#4-business-objectives)
  - [5. Key Features \& Functionality](#5-key-features--functionality)
  - [6. Integrated Tools](#6-integrated-tools)
  - [7. User Interface (Frontend)](#7-user-interface-frontend)
  - [8. Technologies Used](#8-technologies-used)
  - [9. Project Scope](#9-project-scope)
  - [10. Non-Functional Requirements](#10-non-functional-requirements)
  - [11. Project Roadmap/Timeline](#11-project-roadmaptimeline)
    - [Phase 1: Planning, Design \& Mathematical Foundation (Oct 20 – Nov 16, 2025)](#phase-1-planning-design--mathematical-foundation-oct-20--nov-16-2025)
    - [Phase 2: Core Development \& Tooling (Nov 17 – Dec 28, 2025)](#phase-2-core-development--tooling-nov-17--dec-28-2025)
    - [Phase 3: Security, Refinement \& Launch (Dec 29 – Jan 20, 2026)](#phase-3-security-refinement--launch-dec-29--jan-20-2026)
    - [Timeline Overview \& Milestones](#timeline-overview--milestones)
  - [12. Getting Started](#12-getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Accessing the Application](#accessing-the-application)
  - [13. Development](#13-development)
    - [Running Frontend Separately](#running-frontend-separately)
    - [Running Backend Separately](#running-backend-separately)
  - [14. Project Structure](#14-project-structure)
  - [15. Contributing](#15-contributing)
  - [16. License](#16-license)

## 1. Overview
Nexus AI is an advanced, production-ready AI Agent System designed for intelligent tool orchestration, real-time streaming conversations, and secure operation. It features a robust backend powered by FastAPI and a highly interactive React frontend. The system supports a dual-council architecture for advanced reasoning, integrated web search, file management, and secure system interactions.

## 2. Product Vision
To empower users with a versatile and intelligent AI agent that can autonomously understand, plan, and execute complex tasks through a natural language interface, utilizing a suite of integrated tools and a resilient multi-model AI architecture.

## 3. Target Audience
- Developers and engineers seeking an extensible AI agent framework.
- Researchers and data scientists needing advanced information retrieval and task automation.
- Tech-savvy individuals interested in experimenting with cutting-edge AI.
- Businesses looking to integrate intelligent automation into workflows.

## 4. Business Objectives
- **Enhance User Productivity:** Provide an intuitive and powerful AI assistant that automates routine tasks, accelerates information gathering, and assists with complex problem-solving.
- **Drive Innovation in AI Application:** Showcase a production-ready example of advanced AI agent architecture, including multi-model orchestration, persistent memory, and secure tool integration.
- **Establish a Secure & Reliable Platform:** Ensure the system operates with high security standards, protecting user data and preventing malicious operations, while maintaining high availability.
- **Facilitate Research & Development:** Offer a flexible and extensible platform for developers and researchers to build upon and experiment with new AI capabilities and integrations.
- **Expand Market Reach:** Attract a diverse user base, from individual developers to small businesses, by offering a versatile and powerful AI solution.

## 5. Key Features & Functionality

**Core Agent Capabilities:**
- **Dual-Council AI Orchestration:** Employs a primary (OpenRouter) and backup (Groq, Gemini, Ollama) council system for robust, multi-model reasoning and redundancy.
- **Intelligent Tool Use:** Automatically selects and executes a wide array of tools for web searching, file operations, system commands, and email.
- **Persistent Memory:** Utilizes both short-term conversation history and long-term vector memory (ChromaDB) for context and knowledge retention.
- **Secure Operations:** Features a hardened security manager with input sanitization, path validation, rate limiting, user confirmation for sensitive actions, and comprehensive audit logging.
- **Natural Language Understanding (NLU):** Ability to comprehend user requests, identify intent, and extract relevant entities.
- **Task Planning & Execution:** Capable of breaking down complex requests into smaller, actionable steps and executing them using available tools.
- **Real-time Streaming:** Provides instant feedback with token-by-token response streaming via WebSockets.

## 6. Integrated Tools
- **Web Search & Fetch:** Leverages DuckDuckGo for web searches and `BeautifulSoup4` for extracting clean content from webpages.
- **File Management:** Securely `create`, `read`, `list`, `delete`, and `append` to files within a designated data directory.
- **System Interaction:** Safely `run_command` (whitelisted), `open_application`, `get_system_info`, and `take_screenshot`.
- **Email Communication:** `send_email` with user confirmation and secure credential storage.

## 7. User Interface (Frontend)
- **Interactive Chat Interface:** A modern React application for seamless interaction.
- **Dynamic Theming:** Supports light and dark modes.
- **Markdown Rendering:** Displays AI responses with proper markdown formatting, including code blocks.
- **File Attachments:** Easily attach files for the agent to analyze.
- **Voice Input/Output:** Integrated speech-to-text and text-to-speech capabilities.
- **Conversation Management:** Create new chats, fork existing ones, regenerate responses, and export conversations.

## 8. Technologies Used

**Backend:**
- **Python:** Primary language.
- **FastAPI:** Web framework for the API and WebSockets.
- **LangChain:** For LLM integration and orchestration.
- **Ollama:** Local LLM server for `llama3.1:8b` (default model).
- **ChromaDB:** Vector store for long-term memory.
- **DuckDuckGo-Search, Requests, BeautifulSoup4, LXML:** For web interaction.
- **PyAutoGUI, Pillow, Psutil:** For system interactions (screenshots, system info).
- **Cryptography:** For secure encryption.
- **DiskCache:** For caching web requests and other operations.
- **python-dotenv:** For environment variable management.

**Frontend:**
- **React.js:** JavaScript library for building the user interface.
- **HTML/CSS:** For structure and styling.
- **Lucide-React:** For icons.

**Deployment & Containerization:**
- **Docker:** For containerizing the application.
- **Docker Compose:** For orchestrating multi-service deployments (Ollama & AI Agent).

## 9. Project Scope
Nexus AI will be a standalone application accessible via a web interface, designed to interact with users through natural language. Its primary function is to interpret user requests, engage in multi-turn conversations, execute relevant tools, and provide comprehensive responses. The scope includes:

- A backend API (FastAPI) for core agent logic, tool execution, memory management, and WebSocket communication.
- A frontend web application (React) for user interaction, real-time chat, and configuration.
- Integration with various external tools and services (web search, file system, system utilities, email).
- A robust security layer to protect against common vulnerabilities and ensure responsible AI use.
- Support for local (Ollama) and cloud-based (OpenRouter, Groq, Gemini) LLM integrations.

**In Scope:**
- Natural language processing and generation for conversational AI.
- Intelligent orchestration of predefined tools.
- Persistent short-term and long-term memory for context.
- Real-time streaming of AI responses.
- File upload and management within a controlled environment.
- Basic system interaction (read info, run whitelisted commands, screenshots).
- Secure credential management and audit logging.
- User interface for chat, settings, and conversation history.

**Out of Scope (for initial release):**
- Advanced user authentication and multi-user accounts.
- Complex data visualizations within the frontend.
- Direct integration with enterprise-specific internal systems without custom development.
- Support for all possible system commands or applications.
- Advanced multi-modal input beyond text and simple file uploads (e.g., direct image/video analysis).

## 10. Non-Functional Requirements
- **Performance:** AI responses and tool executions shall be delivered with minimal latency (target: < 5 seconds for most common tasks).
- **Scalability:** The backend infrastructure shall be scalable to accommodate increasing user loads (e.g., via containerization and efficient resource management).
- **Reliability:** The system shall maintain high availability (target: 99.9% uptime) and gracefully handle errors.
- **Security:** The system shall implement robust security measures, including input validation, access control, and data encryption, to protect against common cyber threats.
- **Maintainability:** The codebase shall be well-structured, documented, and adhere to coding standards to facilitate future updates and enhancements.
- **Extensibility:** The architecture shall allow for easy integration of new tools and different LLM providers.
- **User Experience (UX):** The frontend shall be intuitive, responsive, and provide a seamless user experience.
- **Observability:** The system shall provide comprehensive logging and monitoring capabilities for debugging and operational insights.

## 11. Project Roadmap/Timeline

**Estimated Timeline:** 3 Months (October 20, 2025 – January 20, 2026)

---

### Phase 1: Planning, Design & Mathematical Foundation (Oct 20 – Nov 16, 2025)
* **Weeks 1-2: Concept, Vision & Market Alignment (Oct 20 – Nov 02)**
    * Initial brainstorming and competitive analysis of existing LLM agent frameworks.
    * Defining the **Nexus AI** value proposition: minimizing hallucination via multi-model cross-verification.
    * Establishing high-level product goals and user experience (UX) flows for "Agentic Workflows."
* **Weeks 3-4: Requirements Gathering & System Architecture (Nov 03 – Nov 16)**
    * Drafting and finalizing Business (`BRD.md`) and Product (`PRD.md`) Requirements.
    * **Architecture Selection:** Finalizing the stack—FastAPI (Asynchronous Backend), React (State-heavy Frontend), Docker (Deployment), and ChromaDB (Vector Persistence).
    * **Mathematical Modeling:** Defining the "Dual-Council" consensus algorithm to weight model reliability:
        $$C_{final} = \frac{\sum_{i=1}^{n} (w_i \cdot R_i)}{\sum_{i=1}^{n} w_i}$$
        *Where $w_i$ represents the confidence weight of model $i$ and $R_i$ represents the response vector.*

---

### Phase 2: Core Development & Tooling (Nov 17 – Dec 28, 2025)
* **Weeks 5-6: Backend Foundation & Multi-LLM Routing (Nov 17 – Nov 30)**
    * Setting up the **FastAPI** framework, asynchronous task queues, and logging middleware.
    * Integration with **OpenRouter**, **Groq**, and **Gemini** APIs with robust fallback error handling.
    * Implementation of the "Planner" module: translating natural language into actionable tool-step sequences.
* **Weeks 7-8: Advanced Tooling & Memory Management (Dec 01 – Dec 14)**
    * Development of core capabilities: `web_search` (Tavily/DuckDuckGo), `file_system_io`, and `python_interpreter`.
    * Implementing **Long-Term Memory** via **ChromaDB**, utilizing cosine similarity for context retrieval:
        $$S(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$$
    * Developing short-term conversation context management (sliding window buffers).
* **Weeks 9-10: Frontend UI/UX & Real-time Streaming (Dec 15 – Dec 28)**
    * Building the **React** chat interface with support for complex Markdown, LaTeX, and code syntax highlighting.
    * Implementing **WebSockets** for real-time token streaming and "Thought Process" transparency displays.
    * Integrating file upload/attachment support and dynamic system prompt configuration.

---

### Phase 3: Security, Refinement & Launch (Dec 29 – Jan 20, 2026)
* **Weeks 11-12: Redundancy, Security & Hardening (Dec 29 – Jan 11)**
    * **Dual-Council Orchestration:** Implementing the final layer of redundancy where a "Critic" model reviews the "Primary" model's output.
    * **Security Hardening:** Input sanitization, regex-based path validation for file tools, rate limiting, and OAuth2 authentication.
    * Audit logging implementation to track tool usage and API costs.
* **Week 13: Deep Testing & Performance Tuning (Jan 12 – Jan 18)**
    * **Active Debugging Phase:** resolving race conditions in tool-calling sequences.
    * *Key Evidence:* Reference logs `agent_20260112.log` and `agent_20260113.log` document the final resolution of vector search latency and WebSocket reconnection logic.
    * End-to-end integration testing and User Acceptance Testing (UAT).
* **Deployment & Final Handover (Jan 19 – Jan 20)**
    * Finalizing technical documentation, API references, and `README.md`.
    * Optimizing `Dockerfile` layers and `docker-compose.yml` for production-grade deployment.

---

### Timeline Overview & Milestones

| Milestone | Target Date | Deliverable | Status |
| :--- | :--- | :--- | :--- |
| **Project Kickoff** | Oct 20, 2025 | Product Vision Document | Completed |
| **Architecture Freeze** | Nov 16, 2025 | System Design & PRD | Completed |
| **Alpha Release** | Dec 14, 2025 | Functional Backend & Tools | Completed |
| **Beta Release** | Jan 04, 2026 | Integrated UI & Memory | Completed |
| **Security Audit** | Jan 15, 2026 | Pentest & Logic Validation | Completed |
| **Official Launch** | **UNKNOWN** | **Nexus AI v1.0 Production** | **UNKNOWN** |

**Ongoing (Post-Launch):**
*   **Continuous Improvement:** Monitoring, gathering user feedback, and planning for future iterations and new features (e.g., those initially out of scope).

## 12. Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- (Optional) [Ollama](https://ollama.ai/) installed locally if not using Dockerized Ollama or cloud models.
- (Optional) API keys for OpenRouter, Groq, Google Gemini if you plan to use Council Mode with external LLMs. Set these in a `.env` file.

### Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/nexus-ai.git
    cd nexus-ai
    ```

2.  **Create a `.env` file (recommended):**
    Create a file named `.env` in the root directory of the project and add your API keys (if using external models):
    ```
    OPENROUTER_API_KEY="your_openrouter_api_key"
    GROQ_API_KEY="your_groq_api_key"
    GOOGLE_API_KEY="your_google_api_key"

    # Example panel configurations for Council Mode (adjust models as needed)
    PANEL_STRATEGIST="openrouter:google/gemini-pro"
    PANEL_LIBRARIAN="openrouter:mistralai/mistral-7b-instruct:free"
    PANEL_ARCHITECT="openrouter:perplexity/pplx-7b-online"
    PANEL_OBSERVER="openrouter:nousresearch/nous-hermes-2-mixtral-8x7b-dpo"
    PANEL_AUDITOR="openrouter:google/gemini-flash"

    CHAIRPERSON_MODEL="tngtech/deepseek-r1t2-chimera:free"

    # Backup Council (if primary fails)
    BACKUP_PANEL_STRATEGIST="groq:llama-3.1-8b-instant"
    BACKUP_PANEL_LIBRARIAN="gemini:gemini-2.5-flash"
    BACKUP_PANEL_ARCHITECT="ollama:llama3.1:8b"
    BACKUP_PANEL_OBSERVER="groq:mixtral-8x7b-32768"
    BACKUP_PANEL_AUDITOR="gemini:gemini-1.5-pro"

    BACKUP_CHAIRPERSON_MODEL="gemini:gemini-1.5-pro"

    # Frontend URL (if different from default)
    REACT_APP_API_URL=http://localhost:8000
    REACT_APP_WS_URL=ws://localhost:8000/ws
    
    # Default Agent Model (for Ollama Mode fallback)
    AGENT_MODEL=llama3.1:8b
    AGENT_TEMP=0.7
    ```

**Below are the models that I have used and are how I have set the fallback mechanic**
    # MY SETUP
    USE_BACKUP_ONLY=true
    ENABLE_QUALITY_FALLBACK=false

    # AI Agent Configuration
    AGENT_MODEL=llama3.1:8b
    AGENT_TEMP=0.7
    AGENT_MAX_ITER=15
    # ============================================================================
    # PRIMARY COUNCIL - OpenRouter Free Tier (Latest Models)
    # ============================================================================

    # Strategist - Fast reasoning models
    PANEL_STRATEGIST=xiaomi/mimo-v2-flash:free,nvidia/nemotron-nano-9b-v2:free

    # Librarian - Large knowledge models
    PANEL_LIBRARIAN=openai/gpt-oss-120b:free,qwen/qwen3-next-80b-a3b-instruct:free

    # Architect - Best coding models  
    PANEL_ARCHITECT=qwen/qwen3-coder:free,mistralai/devstral-2512:free

    # Observer - Analysis models
    PANEL_OBSERVER=google/gemma-3n-e4b-it:free,nvidia/nemotron-3-nano-30b-a3b:free

    # Auditor - Verification models
    PANEL_AUDITOR=nvidia/nemotron-nano-9b-v2:free,google/gemma-3n-e2b-it:free

    # Chairperson - High-reasoning synthesis
    CHAIRPERSON_MODEL=tngtech/deepseek-r1t2-chimera:free

    # ============================================================================
    # BACKUP COUNCIL - FREE TIER GEMINI MODELS ONLY
    # ============================================================================

    # Use gemini-2.5-flash (FREE) instead of gemini-2.5-pro (PAID)
    BACKUP_PANEL_STRATEGIST=groq:llama-3.3-70b-versatile,gemini:gemini-2.5-flash,ollama:llama3.1:8b

    # gemini-2.5-flash is FREE, gemini-2.5-pro requires payment
    BACKUP_PANEL_LIBRARIAN=groq:llama-3.3-70b-versatile,gemini:gemini-2.5-flash,ollama:llama3.1:8b

    BACKUP_PANEL_ARCHITECT=groq:llama-3.3-70b-versatile,gemini:gemini-2.5-flash,ollama:deepseek-coder:6.7b

    BACKUP_PANEL_OBSERVER=groq:llama-3.3-70b-versatile,gemini:gemini-2.5-flash,ollama:llama3.1:8b

    BACKUP_PANEL_AUDITOR=groq:llama-3.1-8b-instant,gemini:gemini-2.5-flash,ollama:llama3.1:8b

    # IMPORTANT: Change from gemini-2.5-pro to gemini-2.5-flash
    BACKUP_CHAIRPERSON_MODEL=gemini:gemini-2.5-flash

    # ============================================================================
    # FALLBACK BEHAVIOR
    # ============================================================================

    # Automatically switch to backup when primary fails
    ENABLE_BACKUP_COUNCIL=true

    # Number of failures before switching (1 = immediate fallback)
    FAILURES_BEFORE_BACKUP=1

    # Seconds to wait before retrying primary after failure
    PRIMARY_COOLDOWN=60

    # Display which council is being used in responses
    SHOW_COUNCIL_MODE=false

    # ============================================================================
    # RATE LIMITS
    # ============================================================================

    # OpenRouter free tier limits
    OPENROUTER_RPM=20

    # Groq limits
    GROQ_RPM=30
    GROQ_RPD=14400

    # Gemini limits  
    GEMINI_RPM=15
    GEMINI_RPD=1500

    # ============================================================================
    # DUAL CONSENSUS SETTINGS (Primary vs Backup)
    # ============================================================================


    # PRIMARY COUNCIL (OpenRouter - less reliable, needs higher thresholds)
    PRIMARY_ROLE_GAP=50              # Higher gap needed (less reliable models)
    PRIMARY_MIN_CONFIDENCE=75        # Higher confidence required
    PRIMARY_ENABLE_RETRIES=true      # Enable retries for failed calls
    PRIMARY_MAX_RETRIES=2            # Number of retries


    # BACKUP COUNCIL (Groq/Gemini/Ollama - more reliable, lower thresholds)
    BACKUP_ROLE_GAP=40               # Lower gap acceptable (more reliable)
    BACKUP_MIN_CONFIDENCE=70         # Standard confidence
    BACKUP_ENABLE_RETRIES=false      # Less retries needed
    BACKUP_MAX_RETRIES=1


    # CONSENSUS QUALITY TRACKING
    TRACK_CONSENSUS_SCORES=true      # Track consensus quality over time
    MIN_ACCEPTABLE_CONSENSUS=250     # Minimum average consensus score


    # AUTOMATIC FALLBACK
    AUTO_FALLBACK_ON_LOW_CONSENSUS=true   # Fallback if primary consensus too low
    LOW_CONSENSUS_THRESHOLD=280           # Trigger fallback below this score


    # DISAGREEMENT HANDLING
    DETECT_ROLE_CONFLICTS=true
    FLAG_HIGH_SEVERITY_CONFLICTS=true     # Flag severe disagreements


3.  **Build and run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```
    This will:
    - Pull the latest Ollama image.
    - Build the AI Agent Docker image.
    - Start both Ollama and the AI Agent services.
    - Pull the default LLM model (`llama3.1:8b`) into Ollama if not present.

    *(First run might take a while to download the LLM model.)*

### Accessing the Application
Once Docker Compose is running, open your web browser and navigate to:

```
http://localhost:3000
```

(The frontend runs on port 3000 by default. If it's not starting, you might need to run `npm install` and `npm start` in the `frontend/` directory separately, or check `frontend/package.json` for the correct start script and port.)

## 13. Development

### Running Frontend Separately
If you prefer to run the frontend outside of Docker (e.g., for faster development):

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the React development server:
    ```bash
    npm start
    ```
    The frontend will typically be available at `http://localhost:3000`.

### Running Backend Separately
If you prefer to run the backend outside of Docker:

1.  Ensure Ollama is running and has the `llama3.1:8b` model pulled:
    ```bash
    ollama serve
    ollama pull llama3.1:8b
    ```
2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the FastAPI application:
    ```bash
    python api_server.py
    ```
    The backend API will be available at `http://localhost:8000`.

## 14. Project Structure
```
.env                       # Environment variables for configuration
agent_code.py              # Core AI agent logic, tools, memory, security
api_server.py              # FastAPI backend for API and WebSockets
docker-compose.yml         # Defines Docker services (Ollama, AI Agent)
Dockerfile                 # Dockerfile for building the AI Agent image
README.md                  # Project overview, setup, and usage
requirements.txt           # Python dependencies for the backend

frontend/                  # React frontend application
├── public/                # Static assets
├── src/                   # React source code
│   ├── App.js             # Main React component, UI logic
│   ├── index.js           # Entry point for React app
│   └── ...                # Other CSS, test files
├── package.json           # Frontend dependencies and scripts
├── README.md              # Frontend specific README
└── tailwind.config.js     # Tailwind CSS configuration

agent_data/                # (Volume) Stores user-uploaded files, agent data
agent_logs/                # (Volume) Stores agent logs (general, security)
agent_memory/              # (Volume) Stores ChromaDB vector store, conversation DB
agent_cache/               # (Volume) Stores DiskCache for web requests
agent_secure/              # (Volume) Stores encryption keys, audit DB, credentials
```

## 15. Contributing
Contributions are welcome! Please feel free to open issues or submit pull requests.

## 16. License
This project is licensed under the MIT License.
