# Daemonium Web UI

Modern web interface for conversing with AI-powered philosopher personas.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Start development server
npm run dev
```

Visit `http://localhost:3000` to see the application.

## 🪟 Windows 11 Setup (Local Dev)

Follow these steps if `npm install` fails on a fresh Windows machine or when developing from a OneDrive folder.

1) Install Node.js 20 LTS via nvm-windows

```powershell
# Install NVM for Windows (restart terminal after install)
winget install -e --id CoreyButler.NVMforWindows

# Install and use Node 20 (LTS)
nvm install 20
nvm use 20
node -v
npm -v
```

2) OneDrive and long path caveat (recommended)

- Prefer cloning the repo outside OneDrive (e.g., `C:\dev\daemonium`).
- If staying under OneDrive, enable Windows long paths to avoid nested module path issues:

```powershell
# Run PowerShell as Administrator
reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f
```

3) Clean install sequence

```powershell
# From the web-ui/ directory
Remove-Item -Recurse -Force node_modules,.next -ErrorAction SilentlyContinue
npm ci   # exact install from package-lock.json

# Copy env file (Windows PowerShell)
Copy-Item .env.example .env.local -Force

npm run dev
```

4) If you hit peer dependency conflicts

```powershell
npm install --legacy-peer-deps
```

5) Docker alternative for local dev (no Node install required)

```powershell
# From project root
docker compose build web-ui
docker compose up -d backend web-ui

# Health check
Invoke-RestMethod http://localhost:3000/api/health
```

## 🏗️ Project Structure

```
web-ui/
├── src/
│   ├── app/                    # Next.js 15 App Router
│   │   ├── (auth)/            # Authentication pages
│   │   ├── (dashboard)/       # Protected dashboard pages
│   │   ├── api/               # API routes (proxy to backend)
│   │   ├── globals.css        # Global styles
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Home page
│   ├── components/            # React components
│   │   ├── ui/               # Base UI components
│   │   ├── auth/             # Authentication components
│   │   ├── chat/             # Chat interface components
│   │   ├── philosophers/     # Philosopher selection components
│   │   ├── dashboard/        # Dashboard components
│   │   ├── layout/           # Layout components
│   │   ├── providers/        # Context providers
│   │   └── sections/         # Page sections
│   ├── types/                # TypeScript type definitions
│   │   ├── philosopher.ts    # Philosopher types
│   │   ├── chat.ts          # Chat and conversation types
│   │   └── user.ts          # User and subscription types
│   ├── utils/               # Utility functions
│   │   ├── api-client.ts    # Backend API client
│   │   └── cn.ts           # Class name utility
│   ├── hooks/              # Custom React hooks
│   ├── stores/             # Zustand state stores
│   └── config/             # Configuration files
├── public/                 # Static assets
├── package.json           # Dependencies and scripts
├── tailwind.config.ts     # Tailwind CSS configuration
├── tsconfig.json          # TypeScript configuration
└── next.config.js         # Next.js configuration
```

## 🛠️ Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Radix UI
- **State Management**: Zustand + React Query
- **Authentication**: Firebase Authentication (Google Sign-In) + NextAuth.js
- **UI Components**: Radix UI primitives
- **Animations**: Framer Motion
- **Backend Integration**: Custom API client

## 🔌 Backend Integration

The web UI integrates with the Daemonium FastAPI backend:

- **API Client**: `src/utils/api-client.ts` handles all backend communication
- **Proxy Routes**: Next.js API routes in `src/app/api/` proxy requests to backend
- **Environment**: Set `BACKEND_API_URL` to your backend URL

### Available API Endpoints

- **Philosophers**: Browse, search, and select philosophers
- **Chat**: Real-time conversations with philosopher personas
- **Books**: Access philosophical texts and summaries
- **Ideas**: Explore top philosophical ideas and concepts
- **Search**: Global search across all content

## 🎨 Design System

### Colors
- **Philosopher Eras**: Ancient (brown), Medieval (slate), Modern (blue), Contemporary (purple)
- **Wisdom Theme**: Custom color palette for philosophical content
- **Dark/Light Mode**: Full theme support

### Components
- **Base UI**: Button, Card, Input, etc. (Radix UI + Tailwind)
- **Philosopher Cards**: Interactive philosopher selection
- **Chat Interface**: Real-time messaging with typing indicators
- **Dashboard**: Analytics and conversation management

## 📱 Features

### MVP Features
- ✅ User authentication and profiles
- ✅ Philosopher browsing and selection
- ✅ Text-based conversations
- ✅ Conversation history and persistence
- ✅ Usage limits and subscription tiers
- ✅ Responsive design

### Advanced Features (Planned)
- 🔄 Voice chat capabilities
- 🔄 Multi-philosopher conversations
- 🔄 Learning paths and progress tracking
- 🔄 Community features
- 🔄 Mobile app

## 🔧 Development

### Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
npm run test         # Run tests
npm run format       # Format code with Prettier
```

### Environment Variables

Copy `.env.example` to `.env.local` and configure.

- Windows PowerShell: `Copy-Item .env.example .env.local -Force`
- macOS/Linux: `cp .env.example .env.local`

Then set values like the backend URL and Firebase keys. NextAuth is deprecated in this project; see `.env.example` where legacy NextAuth vars are commented out.

```env
# Backend API
BACKEND_API_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000

# Database (optional for local features)
MONGODB_URI=mongodb://localhost:27018/daemonium

# Firebase (Web UI Authentication)
NEXT_PUBLIC_FIREBASE_API_KEY=your-firebase-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=000000000000
NEXT_PUBLIC_FIREBASE_APP_ID=1:000000000000:web:abcdef1234567890
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
```

Note: Chat routes default to MCP-backed `src/app/api/chat/route.ts` with `/api/ollama` available as a fallback proxy to local Ollama.

#### Firebase (Web UI Authentication)

Add the following public variables (see `.env.example` for details):

```env
NEXT_PUBLIC_FIREBASE_API_KEY=your-firebase-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=000000000000
NEXT_PUBLIC_FIREBASE_APP_ID=1:000000000000:web:abcdef1234567890
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
```

If you encounter TypeScript errors related to Firebase:
- Ensure dependencies are installed: `npm install`
- Confirm `firebase` is present in `dependencies` (it is by default in `package.json`)
- Verify Node.js 18+ and TypeScript 5+
- Make sure the file using Firebase runs on the client (contains `'use client'`), e.g. `src/components/providers/firebase-auth-provider.tsx`

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Docker

```bash
# Build image
docker build -t daemonium-web-ui .

# Run container
docker run -p 3000:3000 daemonium-web-ui
```

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Use TypeScript strict mode
3. Add tests for new features
4. Update documentation as needed

## 📄 License

Part of the Daemonium project - see main project for license details.
