# Frontend Pages Implementation Plan

Complete list of 13 critical pages needed for ASTRAEUS testing and launch.

---

## Design System Reference

**Colors**:
- Background: `bg-background-light dark:bg-background-dark` or `bg-[#1A1A1A]`
- Text: `text-white`, `text-white/80`, `text-white/60`
- Primary: `text-primary`, `bg-primary`
- Borders: `border-white/10`

**Components**:
- Buttons: `rounded h-10 px-4 bg-primary hover:opacity-90 text-white text-sm font-bold`
- Cards: `rounded border border-white/10 bg-[#1A1A1A] p-4`
- Inputs: Dark theme, white/10 borders
- Typography: `font-display`, `font-bold`, `tracking-[-0.015em]`

---

## 📋 Pages to Build

### Priority 1: Payments & Credits (3 pages)

#### 1. `/payments/purchase-credits`
**Purpose**: Buy credits with Stripe/PayPal
**Features**:
- Credit package selection ($10, $50, $100, $500)
- Payment provider choice (Stripe, PayPal)
- Current balance display
- Transaction confirmation
**API**: `POST /api/v1/payments/credits/purchase`

#### 2. `/payments/methods`
**Purpose**: Manage saved payment methods
**Features**:
- List saved cards/accounts
- Add new payment method
- Remove payment method
- Set default method
**API**: `GET/POST/DELETE /api/v1/payments/methods`

#### 3. `/credits/dashboard`
**Purpose**: Credit balance & transaction history
**Features**:
- Current balance (large display)
- Transaction history table
- Usage analytics charts
- Filter by type (purchase, usage, refund)
**API**: `GET /api/v1/payments/credits/balance`, `GET /api/v1/payments/credits/transactions`

---

### Priority 2: Contracts & Escrow (2 pages)

#### 4. `/contracts/[id]`
**Purpose**: Contract detail page
**Features**:
- Contract status badge (draft, active, completed, disputed)
- Escrow balance and release status
- Agent assignment
- Timeline/milestones
- Actions (award, complete, dispute)
**API**: `GET /api/v1/contracts/{id}`

#### 5. `/contracts/my-contracts`
**Purpose**: User's contract list
**Features**:
- Filter by status
- Search by title/agent
- Quick stats (total budget, completed, active)
- Create new contract button
**API**: `GET /api/v1/contracts`

---

### Priority 3: Multi-Agent Orchestration (3 pages)

#### 6. `/chat` (ENHANCED)
**Purpose**: Chat with orchestration indicators
**Features**:
- Show when orchestration is triggered
- Display execution plan preview
- Real-time agent coordination status
- WebSocket progress updates
**API**: Existing + orchestration data

#### 7. `/orchestration/history`
**Purpose**: Past orchestration executions
**Features**:
- List all orchestration runs
- Success/failure status
- Performance metrics (time, cost, quality)
- Replay/rerun functionality
**API**: `GET /api/v1/orchestration/plans`

#### 8. `/orchestration/plans/[id]`
**Purpose**: Execution plan detail
**Features**:
- DAG visualization of workflow
- Per-agent performance breakdown
- Token usage and cost analysis
- Quality scores for each step
**API**: `GET /api/v1/orchestration/plan/{id}`

---

### Priority 4: Agent Management (5 pages)

#### 9. `/my-agents`
**Purpose**: User's created agents dashboard
**Features**:
- Agent list with stats (calls, revenue, rating)
- Quick edit/disable/delete
- Performance overview charts
- Create new agent button
**API**: `GET /api/v1/agents/owned`

#### 10. `/my-agents/[id]/settings`
**Purpose**: Agent configuration
**Features**:
- Edit name, description, capabilities
- Set pricing (free, pay-per-use, subscription)
- Configure API endpoint
- Set rate limits and quotas
**API**: `PUT /api/v1/agents/{id}`

#### 11. `/my-agents/[id]/earnings`
**Purpose**: Agent earnings dashboard
**Features**:
- Revenue over time chart
- Transaction breakdown
- Top users/clients
- Payout history
**API**: `GET /api/v1/analytics/agent/{id}`

#### 12. `/my-agents/[id]/analytics`
**Purpose**: Agent performance analytics
**Features**:
- Call volume trends
- Success/failure rates
- Average response time
- User ratings and reviews
**API**: `GET /api/v1/analytics/agent/{id}`

#### 13. `/my-agents/create`
**Purpose**: Create new agent wizard
**Features**:
- Multi-step form (basic info, capabilities, API config, testing)
- Live API endpoint validation
- Publish to marketplace
**API**: `POST /api/v1/marketplace`

---

## Implementation Order

**Phase 1**: Credits & Payments (Pages 1-3)
- Essential for testing paid agents
- ~600 lines total

**Phase 2**: Contracts (Pages 4-5)
- Core escrow functionality
- ~400 lines total

**Phase 3**: Agent Management (Pages 9-13)
- Developer experience
- ~1,000 lines total

**Phase 4**: Orchestration (Pages 6-8)
- Advanced features
- ~600 lines total

**Total Estimated**: ~2,600 lines of frontend code

---

## Shared Components Needed

- `CreditBalanceCard` - Shows current balance
- `TransactionTable` - Lists credit transactions
- `PaymentMethodCard` - Displays saved payment method
- `ContractStatusBadge` - Status indicator
- `AgentCard` - Agent preview card
- `MetricsChart` - Line/bar charts for analytics
- `OrchestrationDAG` - Workflow visualization

---

## Testing Checklist

- [ ] All pages load without errors
- [ ] API integration works with test data
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Dark theme consistency
- [ ] Loading states for async operations
- [ ] Error handling and user feedback
- [ ] Navigation and routing
- [ ] Auth protection (require login)

---

**Next Step**: Build Phase 1 (Credits & Payments)
