# 🧠 Daemonium 
# Conversational Philosophy AI App — Planning Summary

## 🧠 Core Concept
An AI-powered app that enables users to have dynamic, interactive conversations with philosophers — either individually, by theme, or in multi-perspective debates. The goal is to teach philosophy through dialogue rather than didactic explanation.

---

## 🎯 Goals
- Make philosophy accessible, engaging, and interactive
- Offer users the ability to explore both abstract ideas and personal questions
- Provide educational depth through AI-guided conversations
- Build a long-term framework that supports future expansion (e.g., voice, multimedia)

---

## 🔑 Key Features (Initial Phase)

### 1. **Modes of Interaction**
- **By Philosopher**: Converse with a historical thinker (e.g., Nietzsche, Plato)
- **By Theme**: Explore topics like Free Will, Justice, Meaning of Life
- **Multi-Philosopher Dialogues**: Moderated and interact with debates between conflicting viewpoints

### 2. **Philosophical Profiles**
Each philosopher includes:
- Core beliefs & worldview
- Philosophical school
- Known works and key quotes
- Tone & language style (e.g., poetic, analytic, critical)

### 3. **Dynamic Learning Experience**
- "Pause and explain" feature
- Summaries of complex ideas
- References to related thinkers

### 4. **Metadata and Interaction Logging**
- Save conversations
- Track philosophical leanings
- Build user learning paths

### 5. **Future Feature: Voice Layer**
- Synthetic voices with accents (e.g., Nietzsche with a German accent)
- Optional speech-to-text interaction

---

## 🏗️ Data and Knowledge Design

### 1. **Entity Types**
- Philosopher
- Concept / Idea
- Theme
- Source (Book, Lecture, etc.)
- Interpretation
- Contradiction / Link

### 2. **Database Model**
- **Relational DB (PostgreSQL)**: To store and query relationships among concepts, themes, and philosophers
- **Graph DB (Neo4j)**: To store and query relationships among concepts, themes, and philosophers
- **Vector DB (Qdrant)**: For semantic search of idea chunks and conversational grounding

### 3. **Knowledge Base Construction**
- Use public domain primary sources (Gutenberg, Perseus, etc.)
- Use open-access summaries (IEP, SEP with citation)
- Chunk text by concept, not paragraph
- Tag metadata: themes, philosophers, difficulty, source, interpretation

### 4. **Embedding Strategy**
- Use HuggingFace models (e.g., `all-MiniLM-L6-v2`) for local embedding
- Store embedded data in Qdrant with metadata for filtering and retrieval

---

## 🛠️ Tools and Tech Stack (Planned, Not Finalized)

| Function                  | Tool/Service          |
|--------------------------|-----------------------|
| Graph Database           | Neo4j                 |
| Vector Database          | Qdrant                |
| Embedding Model          | SentenceTransformers |
| LLM                      | GPT-4o, Local (Ollama) |
| Voice (Future)           | ElevenLabs, Coqui TTS |
| Environment              | Python, VS Code       |

---

## 📚 Starting Set (Proposal)

### Philosophers
- Friedrich Nietzsche
- Plato
- Immanuel Kant
- Simone de Beauvoir

### Themes
- Free Will & Determinism
- Ethics without Religion
- Meaning of Life
- What is Knowledge?

---

## 💡 Philosophical Dictionary (Planned Feature)
- Curated entries for terms like "categorical imperative", "nihilism", "essence vs existence"
- Sources: IEP, SEP, Wikidata
- Accessible inline during conversations

---

## 🧭 Long-Term Vision
- Voice-enabled interaction with tonal realism
- Multi-modal output (chat, voice, visual aids)
- AI-augmented learning paths
- Gamified exploration of philosophical systems

---

## 🔜 Next Planning Steps
- Confirm initial 3–4 philosophers and 3–4 themes
- Finalize data schema and metadata design
- Lock in tech stack and tooling
- Draft content templates (philosopher profile, idea entry, etc.)

---

## 📝 Notes
> This document is designed for iterative updates. Add your thoughts inline or comment where you'd like to refine or expand ideas.

