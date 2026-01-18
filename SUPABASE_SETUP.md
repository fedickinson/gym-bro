# Quick Start: Supabase Setup

## 🚀 You're 3 Steps Away from Persistent Storage!

Your code is ready. Now just set up the database and migrate your data.

---

## Step 1: Create Supabase Project (5 min)

1. Go to https://supabase.com → Sign up (free, no credit card)
2. Create new project: `gym-bro-prod`
3. Save your database password securely
4. Wait for project to provision (~2 min)

---

## Step 2: Run Database Schema (2 min)

1. In Supabase dashboard → **SQL Editor** → **New query**
2. Copy & paste entire contents of `scripts/schema.sql`
3. Click **Run** (Cmd/Ctrl + Enter)
4. Verify: "Success. No rows returned"
5. Check **Table Editor** → should see 4 tables created

---

## Step 3: Configure & Migrate (10 min)

### 3.1 Get Credentials
1. Supabase → **Settings** → **API**
2. Copy:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbG...` (long string)

### 3.2 Add to .env
```bash
# Add to your .env file
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3.3 Install & Migrate
```bash
# Install dependencies
pip install -r requirements.txt

# Test migration (dry run)
python scripts/migrate_json_to_supabase.py --dry-run

# Execute migration
python scripts/migrate_json_to_supabase.py --execute
```

### 3.4 Verify
```bash
# Start app
streamlit run app.py

# Test:
# - History page loads
# - Log a test workout
# - Check Supabase Table Editor
```

---

## Step 4: Deploy to Streamlit Cloud

```bash
# Push changes
git add .
git commit -m "feat: Add Supabase persistent storage"
git push origin main
```

Then in Streamlit Cloud:
1. Deploy app (or it auto-deploys)
2. **App Settings** → **Secrets** → Add:
   ```toml
   SUPABASE_URL = "https://xxxxx.supabase.co"
   SUPABASE_KEY = "eyJhbG..."
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
3. Wait for deployment
4. Test on your iPhone! 🎉

---

## Troubleshooting

### "Missing Supabase credentials"
- Check `.env` has both `SUPABASE_URL` and `SUPABASE_KEY`
- Verify no typos in variable names (case-sensitive)

### Migration fails
```bash
# Check connection
python -c "from src.database import get_supabase_client; print('Connected!' if get_supabase_client() else 'Failed')"
```

### Data not showing in app
1. Check Supabase → Table Editor → `workout_logs` (should see rows)
2. Restart Streamlit (Ctrl+C, then `streamlit run app.py`)
3. Check terminal for error messages

---

## Files Created

✅ **scripts/schema.sql** - Database tables definition
✅ **scripts/migrate_json_to_supabase.py** - One-time data migration
✅ **src/database.py** - Supabase connection manager
✅ **src/data.py** - Updated to use Supabase (API unchanged!)
✅ **requirements.txt** - Added `supabase>=2.0.0`
✅ **DEPLOYMENT.md** - Comprehensive deployment guide

---

## What Changed?

### Code Changes
- `src/data.py`: Replaced JSON file I/O with Supabase queries
- All 15 modules importing `data.py`: **No changes needed!** (API preserved)
- UI pages: **No changes needed!**
- Agents/tools: **No changes needed!**

### Data Flow (Before)
```
App → src/data.py → data/workout_logs.json (local file)
```

### Data Flow (After)
```
App → src/data.py → Supabase (cloud Postgres)
```

### What Stays the Same
- All function signatures in `src/data.py`
- All Pydantic models
- All UI components
- All business logic
- **Your existing code just works!**

---

## Next Steps After Setup

1. **Test thoroughly locally** (see DEPLOYMENT.md Step 5)
2. **Deploy to Streamlit Cloud** (see DEPLOYMENT.md Step 6)
3. **Test on iPhone** - this is the real test!
4. **Celebrate** 🎉 - your data is now persistent!

---

## Full Documentation

See **DEPLOYMENT.md** for:
- Detailed troubleshooting
- Rollback procedures
- Monitoring & maintenance
- Advanced queries
- Multi-user setup (future)

## Database Free Tier Limits

✅ **500MB storage** (you're using 0.3MB = 0.06%)
✅ **Unlimited API requests**
✅ **2GB bandwidth/month**
✅ **7-day backups**

**At current usage:** ~730KB/year = 685 years until limit 😄

---

## Questions?

- Check DEPLOYMENT.md for detailed troubleshooting
- Review Supabase docs: https://supabase.com/docs
- Check Streamlit Cloud docs: https://docs.streamlit.io/streamlit-community-cloud

---

**Time estimate:** 15-30 minutes total (including testing)

Let's make your workout tracking reliable! 💪
