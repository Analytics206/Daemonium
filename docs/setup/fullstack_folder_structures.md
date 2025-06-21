# Full-Stack Project Folder Structures

This document outlines the most common folder structures for modern full-stack development projects, with explanations for when and why to use each approach.

## 1. Monorepo Structure (Single Repository)

The monorepo approach keeps all related applications and shared code in a single repository, making it easier to share code, maintain consistency, and coordinate releases.

```
my-app/
├── apps/
│   ├── web/                 # Frontend (React, Vue, etc.)
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   └── README.md
│   ├── api/                 # Backend API
│   │   ├── src/
│   │   ├── tests/
│   │   ├── package.json
│   │   └── README.md
│   └── mobile/              # Mobile app (optional)
│       ├── src/
│       ├── package.json
│       └── README.md
├── packages/
│   ├── ui/                  # Shared UI components
│   │   ├── src/
│   │   └── package.json
│   ├── utils/               # Shared utilities
│   │   ├── src/
│   │   └── package.json
│   ├── types/               # Shared TypeScript types
│   │   ├── src/
│   │   └── package.json
│   └── database/            # Database schemas/migrations
│       ├── migrations/
│       ├── seeds/
│       └── package.json
├── tools/
│   ├── eslint-config/       # Shared linting config
│   └── tsconfig/            # Shared TypeScript config
├── docker-compose.yml
├── package.json
├── turbo.json               # If using Turborepo
├── nx.json                  # If using Nx
└── README.md
```

### Benefits:
- Shared code and dependencies
- Consistent tooling and configuration
- Easier refactoring across applications
- Single source of truth for types and utilities

### Tools: Nx, Turborepo, Lerna, Rush

## 2. Traditional Separated Structure

This approach keeps frontend and backend in separate folders within the same repository, or sometimes in completely separate repositories.

```
project-root/
├── client/                  # Frontend application
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── styles/
│   ├── public/
│   ├── tests/
│   ├── package.json
│   └── README.md
├── server/                  # Backend application
│   ├── src/
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── middleware/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── config/
│   ├── package.json
│   └── README.md
├── shared/                  # Shared code/types
│   ├── types/
│   ├── constants/
│   └── utils/
├── docs/
├── scripts/
├── docker-compose.yml
└── README.md
```

### Benefits:
- Clear separation of concerns
- Independent deployment pipelines
- Different teams can work on different parts
- Technology flexibility

## 3. Next.js Full-Stack Structure

Next.js applications can handle both frontend and backend in a single framework, leading to this integrated structure.

```
my-nextjs-app/
├── src/
│   ├── app/                 # App Router (Next.js 13+)
│   │   ├── api/             # API routes
│   │   │   ├── auth/
│   │   │   ├── users/
│   │   │   └── posts/
│   │   ├── (auth)/          # Route groups
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── dashboard/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/              # Reusable UI components
│   │   │   ├── button/
│   │   │   ├── input/
│   │   │   └── modal/
│   │   ├── forms/
│   │   └── layout/
│   ├── lib/                 # Utilities, configs
│   │   ├── db/              # Database connection
│   │   ├── auth/            # Authentication logic
│   │   ├── validations/     # Schema validations
│   │   └── utils/
│   ├── hooks/               # Custom React hooks
│   ├── store/               # State management
│   └── types/               # TypeScript definitions
├── public/
│   ├── images/
│   ├── icons/
│   └── favicon.ico
├── prisma/                  # Database schema (if using Prisma)
│   ├── migrations/
│   ├── seeds/
│   └── schema.prisma
├── tests/
│   ├── __mocks__/
│   ├── components/
│   └── api/
├── .env.local
├── .env.example
├── next.config.js
├── tailwind.config.js
├── package.json
└── README.md
```

### Benefits:
- Unified development experience
- Shared types between frontend and backend
- Optimized bundling and performance
- Built-in API routes

## 4. Microservices Structure

In microservices architecture, each service is essentially its own complete application with its own database and deployment pipeline.

```
project/
├── services/
│   ├── user-service/
│   │   ├── src/
│   │   │   ├── controllers/
│   │   │   ├── models/
│   │   │   ├── routes/
│   │   │   └── middleware/
│   │   ├── database/
│   │   │   ├── migrations/
│   │   │   └── seeds/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── README.md
│   ├── auth-service/
│   │   ├── src/
│   │   ├── redis/           # Session storage
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── README.md
│   ├── payment-service/
│   │   ├── src/
│   │   ├── database/        # MySQL for transactions
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── README.md
│   └── notification-service/
│       ├── src/
│       ├── mongodb/         # Message queues
│       ├── tests/
│       ├── Dockerfile
│       ├── package.json
│       └── README.md
├── web-app/                 # Frontend application
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── mobile-app/              # Mobile application
│   ├── src/
│   ├── package.json
│   └── README.md
├── shared/
│   ├── proto/               # Protocol buffers for service communication
│   ├── types/               # Shared TypeScript types
│   └── constants/           # Shared constants
├── infrastructure/
│   ├── docker/
│   │   └── docker-compose.yml
│   ├── k8s/                 # Kubernetes configurations
│   │   ├── deployments/
│   │   ├── services/
│   │   └── ingress/
│   └── terraform/           # Infrastructure as Code
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── gateway/                 # API Gateway
│   ├── src/
│   ├── config/
│   └── Dockerfile
├── docs/
│   ├── api/
│   ├── architecture/
│   └── deployment/
└── scripts/
    ├── deploy.sh
    └── setup.sh
```

### Why No Central Backend/Database Folders?

**Each Service IS a Backend**: Every microservice is a complete backend application with its own:
- API endpoints and business logic
- Database (following "database per service" pattern)
- Dependencies and deployment pipeline
- Technology stack (services can use different languages/frameworks)

**Database Per Service Pattern**: Services maintain their own databases to ensure:
- Data isolation and ownership
- Technology freedom (each service can choose optimal database)
- Independent scaling
- Fault tolerance

## 5. Framework-Specific Patterns

### T3 Stack (Next.js + tRPC + Prisma + NextAuth)

```
my-t3-app/
├── src/
│   ├── pages/
│   │   ├── api/
│   │   │   ├── auth/
│   │   │   └── trpc/
│   │   ├── _app.tsx
│   │   └── index.tsx
│   ├── server/
│   │   ├── api/
│   │   │   ├── routers/
│   │   │   ├── root.ts
│   │   │   └── trpc.ts
│   │   ├── auth.ts
│   │   └── db.ts
│   ├── utils/
│   │   ├── api.ts           # tRPC client
│   │   └── helpers/
│   ├── components/
│   ├── hooks/
│   └── styles/
├── prisma/
│   ├── migrations/
│   └── schema.prisma
├── public/
└── package.json
```

### MEAN/MERN Stack

```
my-mean-app/
├── client/                  # Angular/React frontend
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── services/
│   │   └── assets/
│   ├── package.json
│   └── README.md
├── server/                  # Express.js backend
│   ├── controllers/
│   ├── models/              # Mongoose models
│   ├── routes/
│   ├── middleware/
│   ├── config/
│   │   ├── database.js
│   │   └── auth.js
│   ├── utils/
│   ├── tests/
│   ├── app.js
│   └── package.json
├── shared/
│   ├── types/
│   └── constants/
└── package.json
```

### JAMstack (Gatsby/Nuxt + Headless CMS)

```
my-jamstack-app/
├── src/
│   ├── components/
│   ├── pages/
│   ├── templates/
│   ├── hooks/
│   ├── utils/
│   └── styles/
├── content/                 # Markdown content
├── static/                  # Static assets
├── functions/               # Serverless functions
│   ├── api/
│   └── webhooks/
├── cms/                     # CMS configuration
├── gatsby-config.js
└── package.json
```

## Choosing the Right Structure

### Use Monorepo When:
- Multiple related applications sharing code
- Need consistent tooling and dependencies
- Single team managing multiple apps
- Frequent cross-application changes

### Use Separated Structure When:
- Different teams own frontend/backend
- Different deployment schedules
- Different technology stacks
- Need clear separation of concerns

### Use Next.js Full-Stack When:
- Building React applications
- Want unified development experience
- Need SSR/SSG capabilities
- Prefer TypeScript end-to-end

### Use Microservices When:
- Large, complex applications
- Multiple teams with different expertise
- Need independent scaling
- Different parts have different requirements

## Tools and Considerations

### Monorepo Tools:
- **Nx**: Feature-rich with graph visualization
- **Turborepo**: Fast, simple, focused on performance
- **Lerna**: Mature, npm-focused
- **Rush**: Enterprise-focused, highly configurable

### Version Control:
- Single repo vs. multiple repos
- Branching strategies (Git Flow, GitHub Flow)
- Release management

### CI/CD Considerations:
- Build caching and optimization
- Deployment strategies
- Testing approaches
- Dependency management

The choice of folder structure significantly impacts development workflow, team collaboration, and deployment strategies. Consider your team size, project complexity, and long-term maintenance when choosing an approach.