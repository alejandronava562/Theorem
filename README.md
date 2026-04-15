# Theorem
Theorem is an interactive and personalized learning application that teaches mathematics in a fun, engaging way.

## Deployment Link
To access the application, click this link: [www.theorem.com](https://paicteam1.onrender.com)

# Flow Chart
```mermaid
flowchart LR
    A[User Browser] --> B[Flask API app.py]

    B --> C[API start - Learning Path]
    B --> D[API unit - Quiz]
    B --> E[API answer - Coins]
    B --> F[API auth]

    C --> G[Path Generator]
    D --> H[Unit Generator]
    E --> I[AI Tutor]

    B --> J[Session Memory]
    B --> K[Firestore DB]

    K --> L[User Data]
    K --> M[Progress]

    I --> N[AI Model]

```


