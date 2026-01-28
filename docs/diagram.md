```mermaid
flowchart LR
  %% ===============================
  %% STYLE DEFINITIONS
  %% ===============================
  classDef client fill:#E3F2FD,stroke:#1E88E5,stroke-width:1px,color:#0D47A1
  classDef frontend fill:#E0F7FA,stroke:#00838F,stroke-width:1px,color:#004D40
  classDef api fill:#E8F5E9,stroke:#2E7D32,stroke-width:1px,color:#1B5E20
  classDef service fill:#FFFDE7,stroke:#F9A825,stroke-width:1px,color:#5D4037
  classDef agent fill:#F3E5F5,stroke:#6A1B9A,stroke-width:1px,color:#4A148C
  classDef data fill:#FFF3E0,stroke:#EF6C00,stroke-width:1px,color:#E65100
  classDef ops fill:#ECEFF1,stroke:#546E7A,stroke-width:1px,color:#263238
  classDef flow fill:#FFFFFF,stroke:#000000,stroke-width:2px

  %% ===============================
  %% CLIENTS
  %% ===============================
  subgraph C["🧑‍💻 Clients"]
    R["Respondent Browser"]
    A["Admin Browser"]
  end
  class R,A client

  %% ===============================
  %% FRONTEND
  %% ===============================
  subgraph FE["🎨 Frontend (Static Assets)"]
    FEHTML["HTML\nindex.html / admin.html"]
    FEJS["JavaScript\nsurvey.js / admin.js"]
    FECSS["CSS\nmain.css / survey.css"]
  end
  class FEHTML,FEJS,FECSS frontend

  %% ===============================
  %% API
  %% ===============================
  subgraph API["🚀 Backend API (FastAPI)"]
    Router["API Router\n/api/v1/*"]
    Sessions["Sessions API\nstart / answer"]
    AdminAPI["Admin API"]
    ExportAPI["Export API"]
    CORS["CORS Middleware"]
  end
  class Router,Sessions,AdminAPI,ExportAPI,CORS api

  %% ===============================
  %% SERVICES
  %% ===============================
  subgraph SVC["🧠 Services Layer"]
    SurveySvc["SurveyService\n(JSON ingest & versioning)"]
    SessionSvc["SessionService\n(session lifecycle)"]
    SurveyEngine["SurveyEngine\n(ordering / skip logic)"]
    LLMClient["LLM Client\n(provider wrapper)"]
  end
  class SurveySvc,SessionSvc,SurveyEngine,LLMClient service

  %% ===============================
  %% AGENTS
  %% ===============================
  subgraph AG["🤖 LLM Agents"]
    FollowUpAgent["FollowUpAgent\n(max 3 probes)"]
    SummaryAgent["SummaryAgent\n(running summary)"]
    Prompts["Prompt Templates"]
  end
  class FollowUpAgent,SummaryAgent,Prompts agent

  %% ===============================
  %% DATA LAYER
  %% ===============================
  subgraph D["🗄️ Data Layer"]
    PG["PostgreSQL"]
    Tables["Tables\nsurvey / session / turn / model_call"]
  end
  class PG,Tables data

  %% ===============================
  %% OPS
  %% ===============================
  subgraph OPS["⚙️ Runtime & Ops"]
    Docker["Docker Compose"]
    Env["Env & Secrets"]
    Logs["Logging"]
  end
  class Docker,Env,Logs ops

  %% ===============================
  %% CONNECTIONS
  %% ===============================
  R --> FEHTML
  R --> FEJS
  R --> FECSS
  A --> FEHTML

  FEJS --> Sessions
  FEJS --> AdminAPI
  FEJS --> ExportAPI

  CORS --> Router
  Router --> Sessions
  Router --> AdminAPI
  Router --> ExportAPI

  Sessions --> SessionSvc
  Sessions --> SurveyEngine
  SurveyEngine --> SurveySvc

  SessionSvc --> FollowUpAgent
  SessionSvc --> SummaryAgent

  FollowUpAgent --> Prompts
  SummaryAgent --> Prompts
  FollowUpAgent --> LLMClient
  SummaryAgent --> LLMClient

  SurveySvc --> PG
  SessionSvc --> PG
  PG --- Tables

  Docker --> API
  Docker --> PG
  Docker --> FEHTML
  Env --> API
  Env --> LLMClient
  API --> Logs

  %% ===============================
  %% PRIMARY FLOW
  %% ===============================
  subgraph FLOW["🔄 Primary Respondent Flow"]
    F1["Open Survey"]
    F2["Start Session"]
    F3["Answer Question"]
    F4["Follow-Up Decision"]
    F5["Next Question / End"]
  end
  class F1,F2,F3,F4,F5 flow

  R --> F1 --> F2 --> F3 --> F4 --> F5