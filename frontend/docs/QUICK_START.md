# 🚀 PyCalendar - Quick Start Guide

## ✅ Phase 2 Complete - Ready to Use!

---

## 📦 Installation (Already Done)

```bash
# Backend
cd PyCalendar/backend
pip install -r requirements.txt

# Frontend
cd PyCalendar/frontend
npm install
```

---

## 🏃 Running the Application

### Option 1: Two Terminals

**Terminal 1 - Backend:**
```bash
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar/backend
python main.py
```
✅ Backend running on: http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar/frontend
npm run dev
```
✅ Frontend running on: http://localhost:5176

---

### Option 2: Background Backend + Terminal Frontend

**Start Backend in Background:**
```bash
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar/backend
nohup python main.py > backend.log 2>&1 &
echo $! > backend.pid
```

**Start Frontend:**
```bash
cd /home/vincheetah/Documents/Travail/FFSU/PyCalendar/frontend
npm run dev
```

**Stop Backend Later:**
```bash
kill $(cat /home/vincheetah/Documents/Travail/FFSU/PyCalendar/backend/backend.pid)
rm /home/vincheetah/Documents/Travail/FFSU/PyCalendar/backend/backend.pid
```

---

## 🌐 Access the Application

Once both servers are running:

👉 **Open Browser**: http://localhost:5176

---

## 🎯 What You Can Do

### 1. Select a Project
- Click on the dropdown "Sélectionner un projet"
- Choose a project from the list
- See project metadata (sport, semaines, équipes, gymnases)

### 2. View Calendar
- See all matches displayed on the calendar
- Matches are color-coded:
  - 🔴 Red: Fixed matches (`est_fixe=true`)
  - 🟢 Green: Finished matches (`statut=termine`)
  - 🔵 Blue: Normal matches

### 3. Drag & Drop Matches
- Click and drag a match to move it to another day/time
- Only works for non-fixed matches (not red)
- Toast notification confirms success or shows error

### 4. Match Details & Actions
- Click on any match to open the details modal
- See: Teams, Venue, Week, Time
- Actions:
  - **Fix Match** (🔒): Lock the match in place
  - **Unfix Match** (🔓): Unlock a fixed match
  - **Delete Match** (🗑️): Remove the match (with confirmation)
- Toast notifications for all actions

### 5. Project Stats
- See 4 stat cards:
  - 👥 **Équipes**: Total teams
  - 🏢 **Gymnases**: Total venues
  - 📅 **Matchs planifiés**: Matches with schedule
  - ✅ **Matchs fixés**: Fixed matches

### 6. Navigation
- **Calendrier**: Calendar page (current)
- **Projets**: Projects page (placeholder - Phase 3)
- **Statistiques**: Stats page (placeholder - Phase 3)
- Responsive burger menu on mobile

---

## 🔍 API Endpoints Available

Base URL: `http://localhost:8000`

### Projects
- `GET /api/projets` - List all projects
- `GET /api/projets/{id}` - Get project by ID
- `GET /api/projets/{id}/stats` - Get project stats
- `POST /api/projets` - Create project
- `PUT /api/projets/{id}` - Update project
- `DELETE /api/projets/{id}` - Delete project

### Matches
- `GET /api/projets/{id}/matchs` - Get all matches for a project
- `PATCH /api/matchs/{id}/move` - Move match to new week/time
- `POST /api/matchs/{id}/fix` - Fix match
- `DELETE /api/matchs/{id}/fix` - Unfix match
- `DELETE /api/matchs/{id}` - Delete match

### Teams & Venues
- `GET /api/projets/{id}/equipes` - Get teams
- `GET /api/projets/{id}/gymnases` - Get venues

---

## 🧪 Testing

### Manual Tests

1. **Test Project Selection**
   ```
   ✅ Open app → Select project → Calendar displays
   ```

2. **Test Drag & Drop**
   ```
   ✅ Drag blue match → Drop → Toast success
   ✅ Drag red match → Cannot drag (fixed)
   ```

3. **Test Fix/Unfix**
   ```
   ✅ Click match → Fix → Match turns red → Toast
   ✅ Click red match → Unfix → Match turns blue → Toast
   ```

4. **Test Delete**
   ```
   ✅ Click match → Delete → Confirm → Match removed → Toast
   ```

5. **Test Error Handling**
   ```
   ✅ Stop backend → Drag match → Error toast
   ✅ Simulate error → ErrorBoundary catches
   ```

6. **Test Responsive**
   ```
   ✅ Resize to mobile → Burger menu appears
   ✅ Click burger → Navigation slides in
   ```

---

## 📊 Project Structure

```
PyCalendar/
├── backend/                    # FastAPI backend
│   ├── main.py                # Entry point
│   ├── database/              # SQLAlchemy models
│   ├── api/                   # API routes
│   └── requirements.txt       # Python deps
│
└── frontend/                  # React frontend
    ├── src/
    │   ├── components/        # React components
    │   │   ├── calendar/      # Calendar + Modal
    │   │   ├── Layout/        # Header + MainLayout
    │   │   ├── Project/       # ProjectSelector + Stats
    │   │   ├── ErrorBoundary.tsx
    │   │   ├── ErrorFallback.tsx
    │   │   └── Toaster.tsx
    │   ├── hooks/             # React Query hooks
    │   ├── lib/               # API client + toast helpers
    │   ├── pages/             # Pages (CalendarPage)
    │   ├── types/             # TypeScript types
    │   └── App.tsx            # Main app
    ├── docs/                  # Documentation
    │   ├── TASK_*.md          # Task summaries
    │   ├── PHASE_2_*.md       # Phase docs
    │   └── QUICK_START.md     # This file
    └── package.json           # Node deps
```

---

## 🔧 Troubleshooting

### Backend won't start
```bash
# Check port 8000
lsof -i :8000
# Kill if occupied
kill -9 $(lsof -t -i :8000)
# Restart
python main.py
```

### Frontend won't start
```bash
# Check port 5176
lsof -i :5176
# Kill if occupied
kill -9 $(lsof -t -i :5176)
# Restart
npm run dev
```

### TypeScript errors
```bash
cd frontend
npx tsc --noEmit
# Should show: ✅ 0 errors
```

### No projects in dropdown
- Check backend is running
- Check database has projects
- Open DevTools → Network tab → Check API calls

### Toast not showing
- Check `<Toaster />` is in App.tsx
- Check browser console for errors
- Try hard refresh (Ctrl+Shift+R)

---

## 📝 Important Files

### Frontend Config
- `vite.config.ts` - Vite config (port, alias)
- `tsconfig.json` - TypeScript config
- `tailwind.config.js` - Tailwind config
- `.eslintrc.cjs` - ESLint rules

### Backend Config
- `backend/config.py` - Database config
- `backend/main.py` - FastAPI app
- `backend/database/models.py` - SQLAlchemy models

---

## 🎨 Tech Stack

### Frontend
- **React** 19.1.1 - UI framework
- **TypeScript** 5.9.3 - Type safety
- **Vite** 5.4.20 - Build tool
- **Tailwind CSS** 4.1.14 - Styling
- **React Query** 5.90.2 - Data fetching
- **React Router** 6.28.0 - Routing
- **FullCalendar** 6.1.16 - Calendar
- **Headless UI** 2.2.9 - Accessible components
- **Heroicons** 2.2.0 - Icons
- **react-hot-toast** - Notifications

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **SQLite** - Database

---

## 🚀 Next Steps (Phase 3)

### Coming Soon:
1. **Projects Page** - Full CRUD operations
2. **Statistics Page** - Dashboard with charts
3. **Fixed Matches Management** - Dedicated interface
4. **Performance Optimization** - Code splitting, lazy loading
5. **E2E Tests** - Playwright/Cypress

---

## 📚 Documentation

Full documentation available in `frontend/docs/`:
- `PHASE_2_COMPLETE.md` - Complete Phase 2 summary
- `PHASE_2_SUCCESS.md` - Visual success recap
- `TASK_2.1_SUMMARY.md` to `TASK_2.11_SUMMARY.md` - Detailed task docs

---

## 🎉 Enjoy!

You now have a fully functional calendar management application!

**Questions?** Check the docs or ask for help.

**Found a bug?** Check ErrorBoundary fallback for details.

**Want to contribute?** Phase 3 awaits! 🚀

---

**Happy Coding!** 👨‍💻
