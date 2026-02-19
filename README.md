# Orchid

An AI-enabled **online marketplace for artisans**, built during the **Hack2Skills × Google Cloud Hackathon**.

This repository contains a multi-service architecture with:
- A React + TypeScript frontend
- A Node.js + Express backend API
- FastAPI-based AI services (vision and gift intelligence)

---

## 🚀 Project Overview

The platform is designed to help users discover and purchase artisan products while adding AI-assisted capabilities like:
- Product and catalog workflows (artwork, cart, likes, orders)
- Vision-powered analysis endpoints
- Gift recommendation and bundle generation flows

---

## 🧱 Repository Structure

```text
online-marketplace/
├── frontend/          # React + Vite + TypeScript client app
├── backend/           # Node.js + Express API
├── genai-services/    # FastAPI vision AI microservice
├── gift_ai_service/   # FastAPI gift AI + orchestration service
├── docs/              # Project docs
├── docker-compose.yml # Multi-service compose file (needs env alignment)
└── README.md
```

---

## 🛠️ Tech Stack

### Frontend
- React 18
- TypeScript
- Vite
- Tailwind CSS
- Radix UI / shadcn-ui components

### Backend
- Node.js
- Express.js
- Mongoose (MongoDB)
- JWT authentication

### AI Services
- FastAPI
- Google Generative AI (Gemini)
- OpenAI SDK (in service dependencies)
- Qdrant client (vector search integration path)

### DevOps / Tooling
- Docker / Docker Compose
- ESLint
- Nodemon

---

## ✅ Prerequisites

Install these before running locally:

- **Node.js** 18+
- **npm** 9+
- **Python** 3.10+
- **pip** / virtualenv
- (Optional) **Docker** + Docker Compose
- Access to required API keys (Gemini/OpenAI/etc.)

---

## ⚙️ Local Development Setup

### 1) Clone and enter repo

```bash
git clone <your-repo-url>
cd online-marketplace
```

### 2) Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 3) Install backend dependencies

```bash
cd backend
npm install
cd ..
```

### 4) Install Python service dependencies

```bash
cd genai-services
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..

cd gift_ai_service
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

---

## ▶️ Run Services (Development)

### Backend

```bash
cd backend
npm run dev
```

Default backend port is configured via environment variables (commonly `5000`).

### Frontend

```bash
cd frontend
npm run client
```

Vite frontend typically runs on `http://localhost:5173`.

### Vision AI service

```bash
cd genai-services
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn src.main:app --host 0.0.0.0 --port 5001 --reload
```

### Gift AI service

```bash
cd gift_ai_service
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

---

## 🔐 Environment Variables

Create `.env` files per service as needed.

### Backend (`backend/.env`) typical variables

```env
PORT=5000
NODE_ENV=development
MONGODB_URI=<your-mongodb-uri>
JWT_SECRET=<your-jwt-secret>
FRONTEND_URL=http://localhost:5173
GIFT_AI_SERVICE_URL=http://localhost:8001
VISION_AI_SERVICE_URL=http://localhost:5001
AI_SERVICE_KEY=<optional-internal-service-key>
```

### Frontend (`frontend/.env`) typical variables

```env
VITE_API_BASE_URL=http://localhost:5000/api/v1
VITE_GIFT_AI_API_URL=http://localhost:5000/api/v1/gift-ai
VITE_RAZORPAY_KEY_ID=<your-key>
```

### AI services
Add provider keys and service-level config required by each Python service (Gemini/OpenAI, DB/vector config, etc.).


Frontend lint:

```bash
cd frontend
npm run lint
```

(Additional test hardening and CI unification are recommended.)

---

## 🐳 Docker Notes

A root `docker-compose.yml` is present for multi-service orchestration. Before production/local usage, ensure service definitions and environment values are aligned with the current codebase and available folders.

---

## 🤝 Team

- Paritosh
- Omshree
- Prajakta
