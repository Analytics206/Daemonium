# 📘 Business Requirements Document (BRD)

## Project Name: Daemonium

## 1. Overview
**Daemonium** is a conversational AI platform that enables users to engage with philosophical ideas by interacting with simulated philosophers and thematic explorations. Designed for modularity, educational value, and long-term growth, the system will be containerized for reproducibility and local development. All components — including the LLM interface, vector/graph databases, data curation tools, and front-end — will run in a cohesive, maintainable architecture.

## 2. Goals
- Create an immersive, educational AI experience rooted in philosophy
- Use modular components to allow seamless switching between themes, philosophers, and models
- Maintain all code, curated data, and tools within a unified local-first development environment
- Use open-source tools and components to ensure cost-effectiveness and accessibility (MVP focus)
- Use open-access and public domain sources for content
- Philosophy papers, books, and articles raw data should be stored in document database
- Relational database should be used to store metadata about philosophers, themes, and ideas
- Web UI data such as users, sessions, and preferences should be stored in database
- Support structured philosophical knowledge modeling using both vector and graph databases
- Support retrieval-augmented generation (RAG) for grounded conversations
- Support for both text chat with text response and speech-to-text/text-to-speech
- Future-proof the system for voice, user learning tracking, extended philosophical content, and potential monetization

## 3. Business Features
| BRD ID | Feature Description                                                                 | Linked PRD Requirement(s)       |
|--------|--------------------------------------------------------------------------------------|---------------------------------|
| BRD-01 | Modular interaction system: by philosopher, by theme, or multi-philosopher dialogue | INT-01 to INT-03                |
| BRD-02 | Curated knowledge base with concept-tagged philosophical ideas                      | DATA-01 to DATA-04              |
| BRD-03 | Use Neo4j to model relationships among philosophers, ideas, and themes              | DB-01 to DB-02                  |
| BRD-04 | Use Qdrant to enable semantic search over curated text chunks                       | DB-03                           |
| BRD-05 | Use HuggingFace sentence transformers for local embedding pipeline                  | EMB-01                          |
| BRD-06 | Offline-capable architecture using Docker containers for each service               | DCK-01 to DCK-03                |
| BRD-07 | System supports retrieval-augmented generation (RAG) for grounded conversations     | AI-01 to AI-02                  |
| BRD-08 | In-app philosophical dictionary powered by open-access sources                      | LRN-01                          |
| BRD-09 | Save conversation history and log philosophical leaning development                 | UX-01 to UX-02                  |
| BRD-10 | Local-friendly UI with possible PWA front-end for seamless user experience          | UI-01                           |
| BRD-11 | Configurable LLM integration with support for both Ollama (local) and ChatGPT (cloud) | AI-03                           |
| BRD-12 | Modern, minimalistic web UI that mimics the look and feel of ChatGPT                | UI-02                           |
| BRD-13 | Responsive and mobile-friendly website design                                      | UI-03                           |
| BRD-14 | Design architecture that considers future Android and iOS app development           | UI-04                           |
| BRD-15 | Mode switching interface for philosopher, theme, and dialogue interactions          | UI-05 to UI-06                  |
| BRD-16 | System monitoring and metrics collection using Prometheus and Grafana               | MON-01 to MON-03                |
| BRD-17 | Embedding pipeline using HuggingFace transformers for semantic search              | EMB-01 to EMB-02                |
| BRD-18 | AI integration supporting RAG and configurable LLM selection                       | AI-01 to AI-04                  |
| BRD-19 | Feature to save philosophical learning development                                  | LRN-02                          |
| BRD-20 | Centralized configuration management with YAML files and environment overrides     | CON-01 to CON-02                |
| BRD-21 | Comprehensive logging and error handling for debugging and monitoring               | LOG-01 to LOG-03                |
| BRD-22 | Knowledge learning test/quiz functionality                                         | LRN-04                          |
| BRD-23 | Secure authentication system supporting Google and custom email/password login      | AUTH-01 to AUTH-08              |
| BRD-24 | Advanced user experience features including pause-and-explain for complex concepts | UX-03                           |
| BRD-25 | Curated philosophical content with minimum 4 philosophers and 4 themes for MVP     | PHIL-01 to PHIL-03              |
| BRD-26 | Unified voice interaction system supporting TTS, ASR, and philosopher-specific voices | VOICE-01 to VOICE-04           |
| BRD-27 | Document database storage for philosophy papers, books, and articles raw data        | DATA-01                         |
| BRD-28 | Relational database for storing metadata about philosophers, themes, and ideas       | DB-01 to DB-02                  |
| BRD-29 | Database storage for web UI data including users, sessions, and preferences         | AUTH-03, UX-01                  |

## 4. Post-MVP Features (Future Roadmap)
- Subscription model with tiered access levels and payment processing (SUB-01 to SUB-08)
- UI for data curation and management
- Advanced voice synthesis pipeline with philosopher-specific accents
- Gamified exploration of philosophical systems
- AI-augmented learning paths based on user interests
- Multi-modal output including visual aids and diagrams

## 5. Constraints
- Must prioritize open-access and public domain sources for content
- System should run entirely offline in development environments
- Preference for open-source components (e.g., Neo4j, Qdrant, HF models)

## 6. Assumptions
- User has access to moderate local compute resources
- Philosophical content can be chunked and interpreted using LLM + human QA
- Data curation can be aided by GPT-based automation and refined manually

## 7. Dependencies
- Embedding model availability (HuggingFace)
- Containerization toolchain (Docker, Docker Compose)
- Neo4j and Qdrant local installation
- GPT-4o or local LLM integration (via Ollama or similar)

## 8. Out of Scope (MVP)
- Multiplayer or social interaction features
- Paid subscriptions or monetization features (moved to post-MVP roadmap)
- Advanced voice synthesis with philosopher-specific accents (basic voice support included in MVP)
- Gamification features
- Advanced AI-augmented learning paths
- Multi-modal visual outputs

