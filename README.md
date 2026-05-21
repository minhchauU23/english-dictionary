# 📚 English Dictionary | Mars Tran

## 🧠 Introduction

- **Description**: English Dictionary System with full-text search, learning tools, and scalable backend architecture.
- **Author**: Mars Tran
- **Status**: 🚧 In development

---

## 🚀 Features

- 🔎 Word lookup with auto-complete & fuzzy search
- 📖 Multi-sense dictionary structure (POS-based)
- 🔊 Pronunciation (IPA + audio)
- 🧠 Flashcards (Spaced Repetition System)
- 🧪 Quiz system
- 📚 Search history tracking
- ⭐ Saved words / bookmarks
- 🌐 Synonyms & antonyms
- ⚡ Full-text search (ElasticSearch planned)

---

## 📦 Data Source

This project uses real-world lexical dataset from:

👉 [kaikki.org](https://kaikki.org)

### 📌 Dataset includes:
- Word & part of speech
- Definitions (senses)
- Examples
- Pronunciation (IPA + audio links)
- Word forms (tense, plural, etc.)
- Synonyms & antonyms

---

## 🗄️ Database Design

👉 [Database design](https://dbdiagram.io/d/english-dictionary-db-6a0d643d697f99c167bd1b98)

### Main entities:

- `word`
- `entry`
- `sense`
- `example`
- `pronunciation`
- `word_form`
- `sense_relation`
- `user`
- `flashcard`
- `quiz_session`

---

## 🧪 Techniques Used

- Data Modeling (Normalized schema)
- REST API Design
- Clean Architecture
- Database Optimization (Indexing)
- Full-text Search (ElasticSearch)
- Caching (Redis)
- Unit Testing (JUnit 5)

---

## 🛠️ Tech Stack

### Backend
- Java 21
- Spring Boot 4.0.6
- Spring Security + JWT
- JPA / Hibernate

### Database
- MySQL 8.0

### Cache
- Redis 7

### Search Engine
- Elasticsearch (planned / optional)

### DevOps
- Docker & Docker Compose
- GitHub Actions (CI/CD)
- Cloud deployment (VPS / Cloud server)

---

## 📡 API cURL Sample



