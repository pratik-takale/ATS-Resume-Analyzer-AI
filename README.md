# SmartATS – AI Resume Screener

An AI-powered Applicant Tracking System (ATS) Resume Analyzer that evaluates resumes against job descriptions using Natural Language Processing (NLP), Machine Learning, and Large Language Models (LLMs). The application provides an ATS compatibility score, skill analysis, keyword matching, resume parsing, and personalized improvement suggestions.

---

## Overview

SmartATS is designed to simulate the behavior of modern Applicant Tracking Systems used by recruiters. It helps job seekers understand how well their resume matches a target job description by analyzing resume content, identifying missing skills, and generating actionable recommendations.

The system combines resume parsing, semantic search, keyword matching, and AI-powered analysis to produce detailed evaluation reports.

---

## Features

- Resume upload (PDF)
- Automatic resume parsing
- AI-powered resume analysis using Groq LLM
- ATS compatibility scoring
- Job Description matching
- Keyword extraction and comparison
- Skill extraction
- Missing keyword identification
- Resume summary generation
- Skill validation
- Grammar checking
- Formatting analysis
- Personalized improvement suggestions
- Resume history storage using Supabase
- Secure user authentication
- Interactive Streamlit dashboard

---

## Technology Stack

### Frontend

- Streamlit

### Backend

- FastAPI
- Python

### AI & NLP

- Groq LLM
- Sentence Transformers (BERT Embeddings)
- spaCy
- Scikit-learn

### Database

- Supabase
- PostgreSQL

### PDF Processing

- PyPDF2

### Authentication

- Clerk Authentication

### Deployment

- Streamlit Community Cloud
- FastAPI
- GitHub

---

## Project Architecture

```
User
   │
   ▼
Streamlit Frontend
   │
   ▼
FastAPI Backend
   │
   ├── Resume Parser
   ├── Skill Extractor
   ├── Keyword Matching
   ├── ATS Score Engine
   ├── Grammar Checker
   ├── Groq LLM
   └── Resume Recommendations
   │
   ▼
Supabase Database
```

---

## Folder Structure

```
ATS-Resume-Analyzer-AI
│
├── backend/
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── utils/
│   └── main.py
│
├── frontend/
│
├── static/
│
├── uploads/
│
├── requirements.txt
│
├── README.md
│
└── .env
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/ATS-Resume-Analyzer-AI.git

cd ATS-Resume-Analyzer-AI
```

---

### Create Virtual Environment

Windows

```bash
python -m venv .venv

.venv\Scripts\activate
```

Linux / Mac

```bash
python3 -m venv .venv

source .venv/bin/activate
```

---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file inside the project root.

```env
GROQ_API_KEY=YOUR_GROQ_API_KEY

SUPABASE_URL=YOUR_SUPABASE_URL

SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY

CLERK_SECRET_KEY=YOUR_CLERK_SECRET_KEY

CLERK_PUBLISHABLE_KEY=YOUR_CLERK_PUBLISHABLE_KEY
```

---

## Run Backend

```bash
uvicorn backend.main:app --reload
```

Backend URL

```
http://localhost:8000
```

---

## Run Frontend

```bash
streamlit run frontend/app.py
```

Frontend URL

```
http://localhost:8501
```

---

## ATS Scoring Parameters

The ATS score is calculated using multiple evaluation metrics.

| Category | Weight |
|-----------|---------|
| Keyword Matching | 35% |
| Skill Validation | 20% |
| Resume Content | 20% |
| Formatting | 10% |
| ATS Compatibility | 10% |
| Grammar & Bonus Factors | 5% |

---

## AI Workflow

1. Upload Resume
2. Extract Text
3. Parse Resume
4. Extract Skills
5. Extract Keywords
6. Compare with Job Description
7. Semantic Matching
8. Calculate ATS Score
9. Generate AI Suggestions
10. Store Analysis in Supabase

---

## Screenshots

### Home Page

```
Add Screenshot Here
```

### Resume Upload

```
Add Screenshot Here
```

### ATS Analysis

```
Add Screenshot Here
```

### AI Recommendations

```
Add Screenshot Here
```

---

## Future Improvements

- Multi-language resume support
- Resume template recommendations
- AI resume rewriting
- Cover letter generation
- Interview question generation
- Resume ranking dashboard
- Multiple resume comparison
- Recruiter dashboard
- Resume analytics
- Export PDF reports

---

## Challenges Solved

- Resume parsing from PDF
- Semantic keyword matching
- AI-generated resume analysis
- ATS compatibility evaluation
- Skill validation
- Secure authentication
- Cloud database integration
- FastAPI REST API development

---

## Learning Outcomes

This project helped strengthen practical knowledge of:

- Python
- FastAPI
- Streamlit
- REST APIs
- Machine Learning
- Natural Language Processing
- Large Language Models
- Retrieval-Augmented Analysis
- Supabase
- Authentication
- Git & GitHub

---

## Author

**Pratik Anil Takale**

AI / Machine Learning Engineer

LinkedIn

```
https://www.linkedin.com/in/pratik-takale-014071319?utm_source=share_via&utm_content=profile&utm_medium=member_android
```

GitHub

```
https://github.com/pratik-takale
```

---

## License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2026 Pratik Anil Takale

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files to deal in the Software
without restriction.
```
