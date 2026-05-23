# 🛡️ EventTrust — Event Authenticity & Post-Payment Trust System

A production-ready full-stack platform for hosting and booking events with built-in fraud prevention, KYC verification, escrow payments, and a dynamic trust scoring engine.

---

## 🏗️ Architecture Overview

```
eventrust/
├── backend/                    # Node.js + Express + MongoDB
│   ├── server.js               # Entry point
│   ├── src/
│   │   ├── config/
│   │   │   └── database.js     # MongoDB connection
│   │   ├── middleware/
│   │   │   ├── auth.js         # JWT protect/authorize/requireKYC
│   │   │   ├── validation.js   # express-validator rules
│   │   │   └── errorHandler.js # Global error handler + asyncHandler
│   │   ├── models/
│   │   │   ├── User.js         # KYC docs, trust score, badges
│   │   │   ├── Event.js        # Trust factors, approval workflow
│   │   │   ├── Booking.js      # Escrow ref, refund tracking
│   │   │   ├── Escrow.js       # Transaction history, release conditions
│   │   │   └── FraudReport.js  # Investigation workflow, severity
│   │   ├── controllers/
│   │   │   ├── authController.js
│   │   │   ├── userController.js   # KYC submission
│   │   │   ├── eventController.js  # Create, approve, cancel, complete
│   │   │   ├── bookingController.js # Book, refund, rate
│   │   │   ├── escrowController.js  # Hold, release, freeze
│   │   │   ├── fraudController.js   # Report, investigate, resolve
│   │   │   └── adminController.js   # KYC review, event moderation
│   │   ├── routes/             # Express routers (6 modules)
│   │   ├── services/
│   │   │   ├── trustScoreService.js # 100-pt algorithm for users & events
│   │   │   └── escrowService.js     # Deposit, release, refund, freeze
│   │   └── seeds/
│   │       └── seedData.js     # 6 users, 5 events, 3 bookings, 2 escrows
│
└── frontend/                   # React 18 + Tailwind CSS
    └── src/
        ├── pages/
        │   ├── Login.jsx           # Demo accounts, split layout
        │   ├── Register.jsx        # Role selector (attendee/organizer)
        │   ├── Dashboard.jsx       # Trust gauge, escrow overview, stats
        │   ├── Events.jsx          # Filter by trust score, category, search
        │   ├── EventDetails.jsx    # Full trust analysis, fraud reporting
        │   ├── CreateEvent.jsx     # 4-step wizard with auto-approval logic
        │   ├── BookingFlow.jsx     # 3-step checkout with escrow info
        │   ├── MyBookings.jsx      # Refund requests, payment status
        │   ├── KYCUpload.jsx       # Document selection, trust impact preview
        │   └── AdminDashboard.jsx  # KYC review, event moderation
        ├── components/
        │   ├── TrustScore.jsx      # Gauge, Bar, Breakdown, Badge variants
        │   ├── VerificationBadge.jsx # Badges, KYC status pill
        │   ├── EventCard.jsx       # Trust tier glow, escrow badge
        │   └── Navbar.jsx          # Trust score in profile dropdown
        ├── context/
        │   └── AuthContext.jsx     # JWT management, role checks
        └── services/
            └── api.js              # Axios client, all API calls grouped
```

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- MongoDB 6+ (local or Atlas)
- npm or yarn

### 1. Clone & Install

```bash
# Backend
cd eventrust/backend
npm install

# Frontend
cd ../frontend
npm install
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env — set MONGODB_URI and JWT_SECRET
```

Minimum `.env`:
```
PORT=5000
MONGODB_URI=mongodb://localhost:27017/eventrust
JWT_SECRET=change_this_to_a_random_32_char_secret_key
NODE_ENV=development
```

### 3. Seed Demo Data

```bash
cd backend
npm run seed
```

Output:
```
✅ MongoDB connected for seeding
🗑️  Cleared existing data
👥 Users seeded
🎪 Events seeded
🎟️  Bookings seeded

🌱 Seed complete! Test accounts:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👑 Admin:     admin@eventrust.com      / Password123
🏢 Organizer: sarah@techevents.io      / Password123  (Trust: 87, Elite)
🎵 Organizer: marcus@creativeevents.co / Password123  (Trust: 64, Trusted)
📚 Organizer: priya@workshops.in       / Password123  (Trust: 22, KYC Pending)
🎫 Attendee:  james@example.com        / Password123
🎫 Attendee:  aisha@example.com        / Password123
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4. Run the App

**Terminal 1 – Backend:**
```bash
cd backend
npm run dev    # nodemon, auto-restart
# Server runs on http://localhost:5000
```

**Terminal 2 – Frontend:**
```bash
cd frontend
npm start      # CRA dev server with hot reload
# App runs on http://localhost:3000
```

---

## 📡 Complete API Reference

### Auth
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/auth/register` | Public | Register new user |
| POST | `/api/auth/login` | Public | Login, returns JWT |
| GET | `/api/auth/me` | Private | Get current user |
| POST | `/api/auth/refresh` | Private | Refresh JWT token |
| PUT | `/api/auth/password` | Private | Change password |

### Users
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/users` | Admin | List all users (paginated) |
| GET | `/api/users/:id` | Public | Get user public profile |
| PUT | `/api/users/profile` | Private | Update own profile |
| POST | `/api/users/kyc` | Private | Submit KYC documents |
| GET | `/api/users/:id/trust-score` | Public | Get trust score breakdown |
| PUT | `/api/users/:id/suspend` | Admin | Suspend/unsuspend user |

### Events
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/events` | Public | List approved events (filter/search/sort) |
| GET | `/api/events/:id` | Public | Get event details |
| POST | `/api/events` | Organizer | Create event (triggers trust scoring + approval) |
| PUT | `/api/events/:id` | Organizer | Update event |
| GET | `/api/events/my-events` | Organizer | Get own events |
| POST | `/api/events/:id/cancel` | Organizer/Admin | Cancel + auto-refund all |
| POST | `/api/events/:id/complete` | Organizer/Admin | Mark complete + trigger escrow release |

### Bookings
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/bookings` | Private | Create booking + escrow deposit |
| GET | `/api/bookings/my-bookings` | Private | Get own bookings |
| GET | `/api/bookings/:id` | Private | Get booking details |
| POST | `/api/bookings/:id/refund` | Attendee | Request refund (policy-aware) |
| POST | `/api/bookings/:id/cancel` | Attendee | Cancel booking |
| POST | `/api/bookings/:id/rate` | Attendee | Submit rating 1-5 |

### Escrow
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/escrow` | Admin | List all escrows with summary |
| GET | `/api/escrow/my-escrows` | Organizer | Own escrow accounts |
| GET | `/api/escrow/event/:eventId` | Organizer/Admin | Event escrow details |
| POST | `/api/escrow/:id/release` | Admin | Force-release or auto-release escrow |

### Fraud Reports
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| POST | `/api/fraud` | Private | Submit fraud report (auto-freezes escrow if severe) |
| GET | `/api/fraud` | Admin | List all reports |
| GET | `/api/fraud/my-reports` | Private | Own submitted reports |
| GET | `/api/fraud/:id` | Private | Get report details |
| PUT | `/api/fraud/:id/status` | Admin | Update status / resolve |

### Admin
| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/admin/dashboard` | Admin | Platform stats + pending queues |
| GET | `/api/admin/kyc/pending` | Admin | KYC submissions awaiting review |
| PUT | `/api/admin/kyc/:userId` | Admin | Approve or reject KYC |
| GET | `/api/admin/events/pending` | Admin | Events awaiting approval |
| PUT | `/api/admin/events/:eventId/review` | Admin | Approve or reject event |
| POST | `/api/admin/recalculate-trust` | Admin | Recalculate all trust scores |

---

## 🔐 Trust Score Algorithm

### User Trust Score (0–100 pts)
| Factor | Max | Logic |
|--------|-----|-------|
| KYC Verification | 25 | 25=approved, 5=pending, 0=not submitted |
| Email + Phone badges | +5 bonus | Included in KYC block |
| Events Hosted | 20 | Log scale: 1=5pts, 3=10, 6=15, 11+=20 |
| Completion Rate | 20 | (completed/created) × 20 |
| Refund Rate (inverted) | 15 | <2%=15, <5%=12, <10%=8, <20%=4 |
| Fraud Reports (inverted) | 10 | 0=10, 1=6, 2=3, 3+=0 |
| Account Age | 5 | 365d=5, 180d=4, 90d=3, 30d=2, 7d=1 |
| Attendee Ratings | 5 | 4.5+=5, 4.0+=4, 3.5+=3, 3.0+=2 |

**Tiers:** Elite(80+) › Trusted(60+) › Verified(40+) › Basic(20+) › Unverified

### Event Trust Score (0–100 pts)
| Factor | Max | Logic |
|--------|-----|-------|
| Organizer Trust Score | 40 | (organizer_score/100) × 40 |
| Description Quality | 15 | 500+ chars=8, images=4, tags=3 |
| Refund Policy | 15 | 30d=15, 14d=13, 7d=11, 48h=8, 24h=5, none=0 |
| Advance Notice | 10 | 30d+ ahead=10, 14d=7, 7d=5 |
| Price Reasonableness | 10 | Free=10, <$50=9, <$100=8, <$200=7 |
| Historical Completion | 10 | organizer_completion_rate × 10 |

### Auto-Approval Criteria
Events skip manual review if organizer has:
- ✅ KYC approved
- 📊 Trust score ≥ 70
- 🎪 Event trust score ≥ 60
- 🚫 Zero fraud reports
- 🏁 3+ completed events

---

## 💰 Escrow Flow

```
Attendee Books
     │
     ▼
Payment Captured ──► Escrow Account Created (per event)
     │                        │
     │                  5% Platform Fee deducted
     │
     ▼
Event Happens
     │
     ▼
Organizer marks Complete ──► Release Conditions Checked:
     │                        ✓ Event completed
     │                        ✓ No active fraud reports
     │                        ✓ 48h window passed
     │
     ▼
     ├── All met ──► Funds Released to Organizer
     │
     └── Fraud report filed ──► Escrow Frozen ──► Admin Investigation
          │
          ├── Fraud confirmed ──► Full Refund to All Attendees
          └── Report dismissed ──► Normal Release Flow
```

---

## 🛡️ Fraud Report Flow

1. **Submission** — Any authenticated user reports an event or organizer
2. **Auto-actions** (high/critical severity):
   - Escrow immediately frozen
   - Trust score penalty applied (-5 to -20 pts)
3. **Admin investigation** — Priority queue in admin dashboard
4. **Resolution outcomes:**
   - `fraud_confirmed` → Full trust penalty, potential suspension, escrow refunded
   - `false_report` → No action, mark resolved
   - `warning_issued` → Formal warning, partial penalty

---

## 🎨 Frontend Pages

| Route | Page | Auth |
|-------|------|------|
| `/` | Landing (features, trust tiers) | Public |
| `/login` | Login with demo account shortcuts | Public only |
| `/register` | Register as attendee or organizer | Public only |
| `/events` | Browse with filters (trust score, category, search) | Public |
| `/events/:id` | Full event page with trust analysis | Public |
| `/book/:eventId` | 3-step booking (tickets → details → payment) | Auth |
| `/dashboard` | Trust gauge, stats, escrow overview | Auth |
| `/my-bookings` | All bookings with refund actions | Auth |
| `/kyc` | Document submission + trust impact preview | Auth |
| `/create-event` | 4-step event wizard with live preview | Organizer |
| `/admin` | Moderation queues (KYC + Events) | Admin |

---

## 🧪 Testing Guide

### Scenario 1: Complete Booking Flow
1. Login as `james@example.com`
2. Browse events → click "TechConf 2025"
3. Click "Book Now" → select 1 General Admission
4. Fill details → Review & Pay
5. See booking confirmation with escrow protection notice

### Scenario 2: Organizer Creates Event (Auto-Approval)
1. Login as `sarah@techevents.io` (Trust: 87, Elite)
2. Go to Create Event
3. Fill all 4 steps
4. Submit → should be **auto-approved** instantly

### Scenario 3: KYC Review
1. Login as `admin@eventrust.com`
2. Go to Admin Dashboard → KYC Reviews tab
3. Approve Priya's pending KYC
4. Trust score updates automatically

### Scenario 4: Fraud Report
1. Login as `james@example.com`
2. Open any event → Report button at bottom
3. Fill report form with severity "high"
4. Check Admin Dashboard → Open Fraud Reports

### Scenario 5: Escrow Release
1. Login as `sarah@techevents.io`
2. Open one of her approved events
3. Click "Mark as Completed"
4. Login as admin → `/api/escrow` to see release status

---

## 🔧 Key Design Decisions

- **MVC architecture** — Controllers thin, logic in Services
- **asyncHandler wrapper** — No try-catch boilerplate in controllers
- **Trust scores recalculated** — On every relevant action (booking, fraud, KYC change)
- **Escrow per event** — One escrow account aggregates all booking payments
- **Platform fee (5%)** — Deducted at time of deposit, shown transparently
- **Refund policy engine** — Calculates full/partial/no refund based on event timing
- **Auto-approval** — Reduces admin load for high-trust organizers
- **JWT stateless auth** — No sessions, works across microservices

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Runtime | Node.js 18 |
| API Framework | Express 4 |
| Database | MongoDB + Mongoose |
| Auth | JWT (jsonwebtoken) |
| Validation | express-validator |
| Security | helmet, cors, express-rate-limit |
| Frontend | React 18 |
| Routing | React Router v6 |
| Styling | Tailwind CSS 3 |
| HTTP Client | Axios |
| Notifications | react-hot-toast |
| Date Handling | date-fns |
| Fonts | Syne (display) + DM Sans (body) |

---

## 📦 Production Checklist

- [ ] Set strong `JWT_SECRET` (32+ chars, random)
- [ ] Use MongoDB Atlas with proper auth
- [ ] Add real payment gateway (Stripe) instead of mock
- [ ] Add real file storage (S3) for KYC uploads
- [ ] Configure SMTP for email notifications
- [ ] Set `NODE_ENV=production`
- [ ] Add Redis for rate limiting at scale
- [ ] Set up cron job for scheduled escrow releases
- [ ] Add Sentry for error monitoring
- [ ] Deploy backend on Railway/Render, frontend on Vercel

---

*Built for EventTrust Hackathon — Production-grade implementation*
