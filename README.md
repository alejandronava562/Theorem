# Theorem
Theorem is an interactive and personalized learning application that teaches mathematics in a fun, engaging way.

## Deployment Link
To access the application, click this link: [www.theorem.com](https://paicteam1.onrender.com)

# App Structure
```mermaid
flowchart TD

    %% Frontend
    templates --> app
    static --> app

    %% Core backend
    app --> learning_path
    app --> path_generator
    app --> unit_generator
    app --> tutor_helper
    app --> session_state
    app --> firestore_db

    %% Internal logic flow
    path_generator --> learning_path
    learning_path --> unit_generator
    unit_generator --> tutor_helper

    %% State & storage
    session_state --> app
    firestore_db --> app

    %% External systems
    firestore_db --> firestore[(Firestore)]
    path_generator --> ai[(AI Model)]
    unit_generator --> ai
    tutor_helper --> ai
```
# Flow Chart app.py
```mermaid
flowchart LR
    A[User Browser] --> B[Flask API app.py]

    %% API routes
    B --> C[Start Topic]
    B --> D[Start Unit]
    B --> E[Answer Question]
    B --> F[Auth]

    %% Generators
    C --> G[Path Generator]
    D --> H[Unit Generator]
    E --> I[AI Tutor]

    %% State
    B --> J[Session Memory]
    B --> K[Firestore DB]

    %% Firestore data
    K --> L[Users]
    K --> M[Progress]
    K --> N[Learning Paths]
    K --> O[Sessions]

    %% AI usage
    G --> P[AI Model]
    H --> P
    I --> P
```


