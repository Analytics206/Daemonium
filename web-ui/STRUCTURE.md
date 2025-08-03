# Daemonium Web UI - Project Structure

## 📁 Complete Folder Structure

```
web-ui/
├── public/                          # Static assets
│   ├── images/                      # Images and icons
│   ├── icons/                       # App icons and favicons
│   └── og-image.jpg                 # Open Graph image
├── src/
│   ├── app/                         # Next.js 15 App Router
│   │   ├── (auth)/                  # Authentication route group
│   │   │   ├── login/
│   │   │   │   └── page.tsx         # Login page
│   │   │   └── register/
│   │   │       └── page.tsx         # Registration page
│   │   ├── (dashboard)/             # Protected dashboard routes
│   │   │   ├── layout.tsx           # Dashboard layout
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx         # Main dashboard
│   │   │   ├── philosophers/
│   │   │   │   └── page.tsx         # Philosopher selection
│   │   │   ├── chat/
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx     # Chat interface
│   │   │   ├── profile/
│   │   │   │   └── page.tsx         # User profile
│   │   │   └── settings/
│   │   │       └── page.tsx         # User settings
│   │   ├── api/                     # API routes (proxy to backend)
│   │   │   ├── auth/
│   │   │   │   └── [...nextauth]/
│   │   │   │       └── route.ts     # NextAuth configuration
│   │   │   ├── philosophers/
│   │   │   │   └── route.ts         # Philosophers API proxy
│   │   │   └── chat/
│   │   │       └── route.ts         # Chat API proxy
│   │   ├── globals.css              # Global styles and Tailwind
│   │   ├── layout.tsx               # Root layout
│   │   └── page.tsx                 # Home page
│   ├── components/                  # React components
│   │   ├── ui/                      # Base UI components (Radix + Tailwind)
│   │   │   ├── button.tsx           # Button component
│   │   │   ├── card.tsx             # Card components
│   │   │   ├── input.tsx            # Input component
│   │   │   ├── dialog.tsx           # Modal dialogs
│   │   │   ├── dropdown-menu.tsx    # Dropdown menus
│   │   │   ├── avatar.tsx           # Avatar component
│   │   │   ├── badge.tsx            # Badge component
│   │   │   ├── tabs.tsx             # Tab components
│   │   │   ├── toast.tsx            # Toast notifications
│   │   │   └── toaster.tsx          # Toast container
│   │   ├── auth/                    # Authentication components
│   │   │   ├── auth-layout.tsx      # Auth page layout
│   │   │   ├── login-form.tsx       # Login form
│   │   │   ├── register-form.tsx    # Registration form
│   │   │   └── oauth-buttons.tsx    # Social login buttons
│   │   ├── chat/                    # Chat interface components
│   │   │   ├── chat-interface.tsx   # Main chat container
│   │   │   ├── chat-header.tsx      # Chat header with philosopher info
│   │   │   ├── message-list.tsx     # Message history
│   │   │   ├── message-bubble.tsx   # Individual message
│   │   │   ├── message-input.tsx    # Message input field
│   │   │   ├── typing-indicator.tsx # Typing animation
│   │   │   └── voice-controls.tsx   # Voice chat controls
│   │   ├── philosophers/            # Philosopher selection components
│   │   │   ├── philosopher-grid.tsx # Grid of philosopher cards
│   │   │   ├── philosopher-card.tsx # Individual philosopher card
│   │   │   ├── philosopher-filters.tsx # Era/school filters
│   │   │   ├── philosopher-search.tsx # Search input
│   │   │   └── philosopher-modal.tsx # Philosopher details modal
│   │   ├── dashboard/               # Dashboard components
│   │   │   ├── dashboard-stats.tsx  # Usage statistics
│   │   │   ├── recent-conversations.tsx # Recent chat list
│   │   │   ├── favorite-philosophers.tsx # Favorite philosophers
│   │   │   └── usage-overview.tsx   # Usage limits display
│   │   ├── layout/                  # Layout components
│   │   │   ├── dashboard-header.tsx # Dashboard header
│   │   │   ├── dashboard-sidebar.tsx # Dashboard sidebar
│   │   │   ├── main-nav.tsx         # Main navigation
│   │   │   └── user-nav.tsx         # User menu
│   │   ├── providers/               # Context providers
│   │   │   ├── theme-provider.tsx   # Theme context
│   │   │   ├── auth-provider.tsx    # Authentication context
│   │   │   └── query-provider.tsx   # React Query provider
│   │   └── sections/                # Page sections
│   │       ├── hero-section.tsx     # Landing page hero
│   │       ├── featured-philosophers.tsx # Featured philosophers
│   │       ├── feature-highlights.tsx # Feature showcase
│   │       ├── testimonials-section.tsx # User testimonials
│   │       └── cta-section.tsx      # Call-to-action
│   ├── types/                       # TypeScript type definitions
│   │   ├── philosopher.ts           # Philosopher-related types
│   │   ├── chat.ts                  # Chat and conversation types
│   │   ├── user.ts                  # User and subscription types
│   │   └── api.ts                   # API response types
│   ├── utils/                       # Utility functions
│   │   ├── api-client.ts            # Backend API client
│   │   ├── cn.ts                    # Class name utility
│   │   ├── auth.ts                  # Authentication utilities
│   │   ├── date.ts                  # Date formatting utilities
│   │   └── constants.ts             # App constants
│   ├── hooks/                       # Custom React hooks
│   │   ├── use-philosophers.ts      # Philosopher data hooks
│   │   ├── use-chat.ts              # Chat functionality hooks
│   │   ├── use-auth.ts              # Authentication hooks
│   │   └── use-debounce.ts          # Debounce hook
│   ├── stores/                      # Zustand state stores
│   │   ├── auth-store.ts            # Authentication state
│   │   ├── chat-store.ts            # Chat state
│   │   ├── philosopher-store.ts     # Philosopher selection state
│   │   └── ui-store.ts              # UI state (modals, etc.)
│   └── config/                      # Configuration files
│       ├── auth.ts                  # NextAuth configuration
│       ├── database.ts              # Database configuration
│       └── constants.ts             # App-wide constants
├── .env.example                     # Environment variables template
├── .eslintrc.json                   # ESLint configuration
├── .gitignore                       # Git ignore rules
├── .prettierrc                      # Prettier configuration
├── next.config.js                   # Next.js configuration
├── package.json                     # Dependencies and scripts
├── postcss.config.js                # PostCSS configuration
├── README.md                        # Project documentation
├── STRUCTURE.md                     # This file
├── tailwind.config.ts               # Tailwind CSS configuration
└── tsconfig.json                    # TypeScript configuration
```

## 🏗️ Architecture Decisions

### 1. Next.js 15 App Router
- **Route Groups**: `(auth)` and `(dashboard)` for logical organization
- **Server Components**: Default for better performance
- **Client Components**: Only when needed for interactivity

### 2. Component Organization
- **UI Components**: Reusable, unstyled base components
- **Feature Components**: Domain-specific components (chat, philosophers)
- **Layout Components**: Navigation and page structure
- **Provider Components**: Context and state management

### 3. State Management
- **Zustand**: Lightweight state management for client state
- **React Query**: Server state management and caching
- **NextAuth**: Authentication state

### 4. Styling Strategy
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Unstyled, accessible component primitives
- **CSS Variables**: Theme system for dark/light mode
- **Custom Classes**: Philosopher-themed styles

### 5. Backend Integration
- **API Client**: Centralized backend communication
- **Proxy Routes**: Next.js API routes proxy to FastAPI backend
- **Type Safety**: Shared types between frontend and backend

## 🔄 Data Flow

```
User Interaction
    ↓
React Component
    ↓
Custom Hook (if needed)
    ↓
Zustand Store (client state) / React Query (server state)
    ↓
API Client (utils/api-client.ts)
    ↓
Next.js API Route (proxy)
    ↓
FastAPI Backend
    ↓
MongoDB Database
```

## 🎯 Key Features by Directory

### `/components/ui/`
- Reusable base components
- Consistent design system
- Accessibility built-in

### `/components/chat/`
- Real-time messaging interface
- Voice chat capabilities
- Message persistence

### `/components/philosophers/`
- Interactive philosopher selection
- Search and filtering
- Detailed philosopher profiles

### `/utils/api-client.ts`
- Centralized backend communication
- Type-safe API calls
- Error handling and retry logic

### `/stores/`
- Client-side state management
- Persistent user preferences
- Real-time chat state

## 🚀 Getting Started

1. **Install Dependencies**: `npm install`
2. **Environment Setup**: Copy `.env.example` to `.env.local`
3. **Start Development**: `npm run dev`
4. **Backend Connection**: Ensure backend is running on `http://localhost:8000`

## 📋 Next Steps

1. **Install Dependencies**: Run `npm install` to install all packages
2. **Create Missing Components**: Implement remaining UI components
3. **Set Up Authentication**: Configure NextAuth with providers
4. **Implement Chat Logic**: Connect to backend chat API
5. **Add Testing**: Set up Jest and React Testing Library
6. **Deploy**: Configure Vercel or preferred hosting platform
