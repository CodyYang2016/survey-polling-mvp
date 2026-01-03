```mermaid
flowchart LR
  %% Polling Survey AI Moderator MVP - End-to-End Architecture

  %% ================
  %% Clients
  %% ================
  subgraph C["Clients"]
    R["Respondent Browser\n(frontend/index.html)"]
    A["Admin Browser\n(frontend/admin.html)"]
  end

  %% ================
  %% Frontend (Static)
  %% ================
  subgraph FE["Frontend (Static Assets)"]
    FEHTML["HTML\nindex.html, admin.html"]
    FEJS["JavaScript\nsurvey.js, admin.js, api.js, config.js"]
    FECSS["CSS\nmain.css, survey.css, admin.css"]
  end

  %% ================
  %% API (FastAPI)
  %% ================
  subgraph API["Backend API (FastAPI)"]
    Router["API Routers\n/api/v1/*"]
    Sessions["Sessions API\n/start, /{session_id}/answer"]
    AdminAPI["Admin API\n/admin/sessions, /admin/sessions/{id}"]
    ExportAPI["Export API\n/export/sessions.json, /export/sessions.csv"]
    CORS["CORS Middleware"]
  end

  %% ================
  %% Services (Business Logic)
  %% ================
  subgraph SVC["Backend Services Layer"]
    SurveySvc["SurveyService\n- ingest survey JSON\n- versioning\n- query questions/options"]
    SessionSvc["SessionService\n- create session\n- record answers\n- manage probes\n- end interview"]
    SurveyEngine["SurveyEngine\n- determine next baseline question\n- enforce ordering\n- future: skip logic"]
    LLMClient["LLM Client\n(provider wrapper)\n- cheap-first calls\n- pluggable provider"]
  end

  %% ================
  %% Agents (LLM Orchestration)
  %% ================
  subgraph AG["Agents"]
    FollowUpAgent["FollowUpAgent\n- max 3 probes per baseline\n- 1 question at a time\n- neutral probing\n- outputs JSON {action, followup_question, reason, confidence}"]
    SummaryAgent["SummaryAgent\n- <= 80-word running summary\n- neutral\n- outputs JSON {summary}"]
    Prompts["Prompts Module\n- system prompt templates\n- user prompt templates"]
  end

  %% ================
  %% Data Layer
  %% ================
  subgraph D["Data Layer"]
    PG["PostgreSQL\n(RDS later / Docker now)"]
    Tables["Core Tables\n- survey\n- survey_version\n- question\n- option\n- session\n- turn/message\n- followup\n- model_call\n- session_summary"]
  end

  %% ================
  %% External / Runtime
  %% ================
  subgraph RT["Runtime & Ops"]
    Docker["Docker Compose\n- api container\n- postgres container\n- nginx container (static FE)"]
    Logs["Logging\n- app logs\n- request id\n- errors"]
    Env["Config & Secrets\n.env\n- DATABASE_URL\n- ANTHROPIC_API_KEY\n- MAX_FOLLOWUP_PROBES"]
  end

  %% ================
  %% Connections: Client -> Frontend
  %% ================
  R -->|"Loads static assets"| FEHTML
  R -->|"Loads JS/CSS"| FEJS
  R -->|"Loads styles"| FECSS

  A -->|"Loads admin page"| FEHTML
  A -->|"Loads JS/CSS"| FEJS
  A -->|"Loads styles"| FECSS

  %% Static hosting (in MVP: nginx container)
  FEHTML -->|"Served by"| Docker
  FEJS -->|"Served by"| Docker
  FECSS -->|"Served by"| Docker

  %% ================
  %% Frontend -> Backend API
  %% ================
  FEJS -->|"HTTP JSON\nstart session"| Sessions
  FEJS -->|"HTTP JSON\nsubmit answer"| Sessions
  FEJS -->|"HTTP JSON\nadmin list/detail"| AdminAPI
  FEJS -->|"HTTP download\nexport JSON/CSV"| ExportAPI

  %% ================
  %% Backend internal routing
  %% ================
  Router --> Sessions
  Router --> AdminAPI
  Router --> ExportAPI
  CORS --> Router

  %% ================
  %% APIs -> Services
  %% ================
  Sessions --> SessionSvc
  Sessions --> SurveyEngine
  AdminAPI --> SessionSvc
  ExportAPI --> SessionSvc

  %% ================
  %% Services interplay
  %% ================
  SurveySvc --> PG
  SessionSvc --> PG
  SurveyEngine --> SurveySvc
  SurveyEngine --> PG

  %% ================
  %% LLM calls
  %% ================
  SessionSvc -->|"After each baseline answer\n(unless end interview)"| FollowUpAgent
  SessionSvc -->|"After each turn\nupdate summary (cheap)"| SummaryAgent

  FollowUpAgent --> Prompts
  SummaryAgent --> Prompts

  FollowUpAgent -->|"Calls via provider wrapper"| LLMClient
  SummaryAgent -->|"Calls via provider wrapper"| LLMClient

  %% ================
  %% Persistence of LLM outputs
  %% ================
  FollowUpAgent -->|"followup_question + reason + confidence"| SessionSvc
  SummaryAgent -->|"summary"| SessionSvc
  LLMClient -->|"request/response metadata\n(tokens, latency, model)"| SessionSvc
  SessionSvc -->|"write model_call records"| PG
  SessionSvc -->|"write turns/messages\n(baseline Q/A, followup Q/A)"| PG
  SessionSvc -->|"write session_summary"| PG

  %% ================
  %% Survey ingestion
  %% ================
  subgraph IN["Survey Ingestion (MVP)"]
    SurveyJSON["Survey JSON Files\nbackend/surveys/*.json"]
    IngestStep["Ingest Step\n(alembic + seed)\nload JSON into survey_version"]
  end

  SurveyJSON --> IngestStep
  IngestStep --> SurveySvc
  IngestStep --> PG

  %% ================
  %% Database detail link
  %% ================
  PG --- Tables

  %% ================
  %% Runtime/Ops links
  %% ================
  Env --> API
  Env --> LLMClient
  Docker --> API
  Docker --> PG
  Docker --> FEHTML
  Docker --> FEJS
  Docker --> FECSS
  API --> Logs
  SessionSvc --> Logs

  %% ================
  %% Key Interaction Flow (annotated)
  %% ================
  subgraph FLOW["Primary Interaction Flow (Respondent)"]
    Step1["1) Respondent opens survey UI"]
    Step2["2) Start session\nPOST /api/v1/sessions/start"]
    Step3["3) Receive baseline question"]
    Step4["4) Submit answer\nPOST /api/v1/sessions/{session_id}/answer"]
    Step5["5) FollowUpAgent decides:\nask_followup OR move_on"]
    Step6["6) If ask_followup:\nUI displays follow-up + capture free-text answer"]
    Step7["7) Repeat until:\n- 3 probes OR\n- confidence high OR\n- policy preference captured"]
    Step8["8) Next baseline question OR End interview"]
  end

  R --> Step1
  Step1 --> Step2 --> Step3 --> Step4 --> Step5
  Step5 --> Step6 --> Step7 --> Step8

  %% ================
  %% Special Cases
  %% ================
  subgraph SC["Special Cases (MVP)"]
    PNA["Prefer Not To Answer\n- stored as flag\n- skip follow-ups"]
    END["End Interview\n- immediate termination\n- persist final state"]
  end

  Step4 -->|"prefer_not_to_answer = true"| PNA
  Step4 -->|"end_interview = true"| END
  PNA --> Step8
  END -->|"session_status = ended"| PG
