# Hermes Frontend

Modern, clean Next.js 14 frontend for Hermes AI orchestration platform.

## Stack

- **Next.js 14** - App Router, Server Components
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations
- **Zustand** - State management
- **Lucide React** - Clean, consistent icons
- **Axios** - API client

## Design System

### Colors
- **Primary**: Blue tones (professional, trustworthy)
- **Accent**: Purple tones (creative, innovative)
- **Success**: Green tones (positive feedback)

### Typography
- **Sans**: Inter (clean, modern, readable)
- **Mono**: JetBrains Mono (code blocks)

### Components
- Glass-morphism effects (backdrop-blur)
- Smooth animations (Framer Motion)
- Gradient backgrounds
- Rounded corners (xl, 2xl)
- Shadow hierarchy
- Hover states with scale transforms

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

Visit http://localhost:3000

## Features Built

### Landing Page (`/`)
- Hero section with gradient background
- Feature cards with icons
- Stats display
- Smooth animations
- CTA buttons to Chat and Marketplace

### Chat Interface (`/chat`)
- Real-time WebSocket streaming
- Message history
- Live event display
- Clean message bubbles
- Typing indicators
- Error handling

### API Integration (`/lib/api.ts`)
- Auth (register, login, getMe)
- Chat (send with WebSocket)
- Agents (list, search)
- Conversations (list, get)

### State Management (`/lib/store.ts`)
- Auth store (token, user, persist)
- Chat store (messages, events, streaming)

## TODO

The following files need to be created:

1. **Auth Pages**
   - `app/auth/login/page.tsx` - Login form
   - `app/auth/register/page.tsx` - Registration form

2. **Marketplace**
   - `app/marketplace/page.tsx` - Agent listing
   - Search bar, filters, agent cards

3. **Components** (reusable)
   - `components/AgentCard.tsx`
   - `components/EventTimeline.tsx`
   - `components/Header.tsx`
   - `components/Footer.tsx`

4. **Additional Features**
   - Conversation history sidebar
   - User profile page
   - Settings page
   - Dark mode toggle

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Build

```bash
npm run build
npm run start
```

## Styling Guidelines

- Use Tailwind utility classes
- Follow glass-morphism pattern
- Use predefined button styles
- Consistent spacing (gap-4, gap-6)
- Rounded corners (rounded-xl, rounded-2xl)
- Smooth transitions (transition-all duration-200)
- Hover states with scale-105
- Active states with scale-95

## Animation Patterns

```tsx
// Fade in
initial={{ opacity: 0 }}
animate={{ opacity: 1 }}

// Slide up
initial={{ opacity: 0, y: 20 }}
animate={{ opacity: 1, y: 0 }}

// Stagger children
<motion.div variants={containerVariants}>
  {items.map((item) => (
    <motion.div variants={itemVariants}>
      {item}
    </motion.div>
  ))}
</motion.div>
```

## Next Steps

1. Run `npm install` in frontend directory
2. Create remaining auth pages
3. Create marketplace page
4. Test WebSocket integration
5. Add dark mode
6. Deploy to Vercel

---

**Status**: Core infrastructure complete, auth and marketplace pages needed
