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
- **Authentication**: NextAuth.js
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

Copy `.env.example` to `.env.local` and configure:

```env
# Backend API
BACKEND_API_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key

# Database (if using local auth)
MONGODB_URI=mongodb://localhost:27017/daemonium
```

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
