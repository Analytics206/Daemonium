# 📘 Business Requirements Document (BRD)

## Project Name: Daemonium

## 1. Overview
**Daemonium** is a conversational AI platform that enables users to engage with philosophical ideas by interacting with simulated philosophers and thematic explorations. Designed for modularity, educational value, and long-term growth, the system will be containerized for reproducibility and local development. All components — including the LLM interface, vector/graph databases, data curation tools, and front-end — will run in a cohesive, maintainable architecture.

## 2. Goals
- Create an immersive, educational AI experience rooted in philosophy
- Use modular components to allow seamless switching between themes, philosophers, and models
- Maintain all code, curated data, and tools within a unified local-first development environment
- Support structured philosophical knowledge modeling using both vector and graph databases
- Future-proof the system for voice, user learning tracking, and extended philosophical content

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
| BRD-08 | Planned voice support using synthetic voices with accents for philosophers          | VOICE-01 (future roadmap)       |
| BRD-09 | In-app philosophical dictionary powered by open-access sources                      | LRN-01                          |
| BRD-10 | Save conversation history and log philosophical leaning development                 | UX-01 to UX-02                  |
| BRD-11 | Local-friendly UI with possible PWA front-end for seamless user experience          | UI-01                           |
| BRD-12 | Configurable LLM integration with support for both Ollama (local) and ChatGPT (cloud) | AI-03                           |
| BRD-13 | Configurable TTS integration with support for both local models and ElevenLabs      | VOICE-02                        |
| BRD-14 | Configurable ASR integration with support for both local models and OpenAI          | VOICE-03                        |
| BRD-15 | Modern, minimalistic web UI that mimics the look and feel of ChatGPT                | UI-02                           |
| BRD-16 | Responsive and mobile-friendly website design                                      | UI-03                           |
| BRD-17 | Design architecture that considers future Android and iOS app development           | UI-04                           |
| BRD-18 | Support for both text chat with text response and speech-to-text/text-to-speech    | INT-04                          |
| BRD-19 | Feature to save philosophical learning development                                  | LRN-02                          |
| BRD-21 | Knowledge learning test/quiz functionality                                         | LRN-04                          |
| BRD-22 | Secure authentication system supporting Google and custom email/password login      | AUTH-01                         |
| BRD-23 | Subscription model with tiered access levels and payment processing                  | SUB-01                          |

## 4. Constraints
- Must prioritize open-access and public domain sources for content
- System should run entirely offline in development environments
- Preference for open-source components (e.g., Neo4j, Qdrant, HF models)

## 5. Assumptions
- User has access to moderate local compute resources
- Philosophical content can be chunked and interpreted using LLM + human QA
- Data curation can be aided by GPT-based automation and refined manually

## 6. Dependencies
- Embedding model availability (HuggingFace)
- Containerization toolchain (Docker, Docker Compose)
- Neo4j and Qdrant local installation
- GPT-4o or local LLM integration (via Ollama or similar)

## 7. Out of Scope (MVP)
- Multiplayer or social interaction features
- Paid subscriptions or monetization features
- Voice synthesis pipeline (planned post-MVP)

