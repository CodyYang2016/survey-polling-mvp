graph TB
    subgraph "Polling Survey System"
        subgraph "Survey Respondent Actions"
            UC1[Start Survey Session]
            UC2[View Question]
            UC3[Submit Single Choice Answer]
            UC4[Submit Free Text Answer]
            UC5[Answer Follow-up Question]
            UC6[Prefer Not to Answer]
            UC7[End Survey Early]
            UC8[View Progress]
            UC9[Recover Incomplete Session]
            UC10[View Completion Summary]
        end
        
        subgraph "Admin Actions"
            UC11[View All Sessions]
            UC12[View Session Details]
            UC13[Filter Sessions by Status]
            UC14[Export Session Data]
            UC15[View Response Analytics]
            UC16[Monitor Survey Costs]
            UC17[Create New Survey]
            UC18[Manage Survey Questions]
        end
        
        subgraph "Claude AI Agent Actions"
            UC19[Generate Follow-up Questions]
            UC20[Analyze Response Depth]
            UC21[Generate Session Summary]
            UC22[Extract Key Themes]
        end
        
        subgraph "System Actions"
            UC23[Persist Session State]
            UC24[Track Model Usage Costs]
            UC25[Store Conversation History]
            UC26[Generate Respondent ID]
        end
    end
    
    %% Actors
    Respondent((Survey<br/>Respondent))
    Admin((Survey<br/>Administrator))
    ClaudeAPI[Claude API<br/>Sonnet 4 / Haiku]
    Database[(PostgreSQL<br/>Database)]
    
    %% Respondent Use Cases
    Respondent -->|initiates| UC1
    Respondent -->|views| UC2
    Respondent -->|provides| UC3
    Respondent -->|provides| UC4
    Respondent -->|responds to| UC5
    Respondent -->|chooses| UC6
    Respondent -->|requests| UC7
    Respondent -->|monitors| UC8
    Respondent -->|resumes| UC9
    Respondent -->|reviews| UC10
    
    %% Admin Use Cases
    Admin -->|accesses| UC11
    Admin -->|examines| UC12
    Admin -->|filters| UC13
    Admin -->|downloads| UC14
    Admin -->|analyzes| UC15
    Admin -->|monitors| UC16
    Admin -->|creates| UC17
    Admin -->|configures| UC18
    
    %% Claude AI Use Cases
    UC5 -.->|triggers| UC19
    UC19 -->|uses| ClaudeAPI
    UC4 -.->|triggers| UC20
    UC20 -->|uses| ClaudeAPI
    UC7 -.->|triggers| UC21
    UC10 -.->|includes| UC21
    UC21 -->|uses| ClaudeAPI
    UC21 -.->|performs| UC22
    
    %% System Use Cases
    UC1 -.->|includes| UC23
    UC1 -.->|includes| UC26
    UC3 -.->|includes| UC23
    UC4 -.->|includes| UC23
    UC5 -.->|includes| UC25
    UC19 -.->|includes| UC24
    UC21 -.->|includes| UC24
    
    %% Database Interactions
    UC23 -->|persists to| Database
    UC25 -->|stores in| Database
    UC24 -->|logs to| Database
    UC11 -->|queries| Database
    UC12 -->|retrieves from| Database
    UC15 -->|analyzes from| Database
    
    %% Use Case Relationships
    UC2 -.->|extends| UC3
    UC2 -.->|extends| UC4
    UC4 -.->|may trigger| UC5
    UC3 -.->|may trigger| UC5
    
    %% Styling
    classDef primary fill:#3b82f6,stroke:#1e40af,color:#fff
    classDef secondary fill:#10b981,stroke:#059669,color:#fff
    classDef ai fill:#f59e0b,stroke:#d97706,color:#fff
    classDef system fill:#6b7280,stroke:#4b5563,color:#fff
    classDef actor fill:#8b5cf6,stroke:#6d28d9,color:#fff
    
    class UC1,UC2,UC3,UC4,UC5,UC6,UC7 primary
    class UC8,UC9,UC10 primary
    class UC11,UC12,UC13,UC14,UC15,UC16,UC17,UC18 secondary
    class UC19,UC20,UC21,UC22 ai
    class UC23,UC24,UC25,UC26 system
    class Respondent,Admin actor