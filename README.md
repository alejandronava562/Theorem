```mermaid
flowchart TD
    A[User / Browser] --> B[Flask API app.py]

    B --> C[/api/start<br>Generate Learning Path/]
    B --> D[/api/unit/start<br>Generate Unit + Quiz/]
    B --> E[/api/answer<br>Check Answer + Coins/]
    B --> F[/api/auth<br>Login via Firebase/]

    C --> G[Path Generator]
    D --> H[Unit Generator]
    E --> I[AI Tutor Helper]

    B --> J[Session State (In-Memory)]
    B --> K[Firestore DB]

    K --> L[User Data]
    K --> M[Progress]
    K --> N[Learning Path]

    I --> O[LLM / AI Feedback]

    style B fill:#f9f,stroke:#333,stroke-width:2px
```

# Deployment Link
https://paicteam1.onrender.com/
