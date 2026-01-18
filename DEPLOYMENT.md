# Gym Bro Deployment Guide: Supabase Migration

## Overview

This guide walks through migrating your Gym Bro app from local JSON files to Supabase for persistent cloud storage. After this migration, your workout data will persist across Streamlit Cloud redeployments.

## Prerequisites

- Git repository with Gym Bro app
- Existing workout data in `data/workout_logs.json`
- Streamlit Cloud account (or ready to create one)
- 15-30 minutes for initial setup

---

## Step 1: Create Supabase Account & Project

### 1.1 Sign Up
1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub (recommended) or email
4. No credit card required for free tier

### 1.2 Create Project
1. Click "New Project"
2. Fill in details:
   - **Name:** `gym-bro-prod`
   - **Database Password:** Generate a strong password (save this!)
   - **Region:** Choose closest to you
   - **Pricing Plan:** Free (500MB database, unlimited API requests)
3. Click "Create new project"
4. Wait 2-3 minutes for provisioning

---

## Step 2: Set Up Database Schema

### 2.1 Open SQL Editor
1. In your Supabase project dashboard, click "SQL Editor" in left sidebar
2. Click "New query"

### 2.2 Run Schema Script
1. Copy the entire contents of `scripts/schema.sql`
2. Paste into SQL Editor
3. Click "Run" (or Cmd/Ctrl + Enter)
4. Verify success: You should see "Success. No rows returned"

### 2.3 Verify Tables Created
1. Click "Table Editor" in left sidebar
2. You should see 4 tables:
   - `workout_logs`
   - `templates`
   - `weekly_split`
   - `exercises`

---

## Step 3: Get Supabase Credentials

### 3.1 Find Your API Keys
1. Click "Settings" (gear icon) in left sidebar
2. Click "API" under Project Settings
3. Copy these two values:
   - **Project URL:** `https://xxxxxxxxxxxxx.supabase.co`
   - **anon public key:** Long string starting with `eyJhbGc...`

### 3.2 Save Credentials Locally
Create or update `.env` file in your project root:

```bash
# Supabase
SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey...

# Anthropic (existing)
ANTHROPIC_API_KEY=sk-ant-...
```

**IMPORTANT:** Ensure `.env` is in your `.gitignore` (it should be already)

---

## Step 4: Install Dependencies & Migrate Data

### 4.1 Install Supabase Client
```bash
pip install -r requirements.txt
```

This installs `supabase>=2.0.0` along with other dependencies.

### 4.2 Dry Run Migration
Test the migration without writing to database:

```bash
python scripts/migrate_json_to_supabase.py --dry-run
```

Expected output:
```
GYM BRO: JSON → SUPABASE MIGRATION
Mode: DRY RUN (preview only)
✅ Connected to Supabase

MIGRATING WORKOUT LOGS
Found 137 workout logs
DRY RUN - Preview of first 3 logs:
  - 2024-01-15 | Push | 2024-01-15-001
  ...
```

### 4.3 Execute Migration
If dry run looks good, run the actual migration:

```bash
python scripts/migrate_json_to_supabase.py --execute
```

Expected output:
```
MIGRATION SUMMARY
Workout Logs:  137
Templates:     6
Weekly Split:  1
Exercises:     0 (or however many you have)

✅ MIGRATION COMPLETE
Verify data in Supabase dashboard → Table Editor
```

### 4.4 Verify Migration
1. Go to Supabase → Table Editor → `workout_logs`
2. You should see all 137 workout logs
3. Check a few recent workouts to ensure data looks correct
4. Verify `templates` table has your workout templates

---

## Step 5: Test Locally

### 5.1 Start Streamlit
```bash
streamlit run app.py
```

### 5.2 Test Read Operations
- Go to History page → should show all your workouts
- Filter by date range → should work
- Search for an exercise → should work
- View Progress charts → should render correctly

### 5.3 Test Write Operations
1. Go to Log Workout page
2. Log a test workout (mark it clearly as a test)
3. Verify it appears in History
4. Go to Supabase → Table Editor → Refresh
5. Verify the new workout appears in database

### 5.4 Test Delete/Restore
1. In History, delete your test workout
2. Go to Trash tab
3. Restore the workout
4. Verify it reappears in History

If all tests pass, you're ready to deploy!

---

## Step 6: Deploy to Streamlit Cloud

### 6.1 Push to GitHub
```bash
git add .
git commit -m "feat: Migrate to Supabase for persistent storage"
git push origin main
```

### 6.2 Deploy on Streamlit Cloud
1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click "New app"
4. Select:
   - **Repository:** your-username/gym-bro
   - **Branch:** main
   - **Main file path:** app.py
5. Click "Advanced settings"

### 6.3 Add Secrets
Paste your environment variables in TOML format:

```toml
SUPABASE_URL = "https://xxxxxxxxxxxxx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey..."
ANTHROPIC_API_KEY = "sk-ant-api03-..."
```

**IMPORTANT:**
- Use double quotes around values
- Match the exact format above (TOML, not .env format)
- Do NOT commit these to Git

### 6.4 Deploy
1. Click "Deploy"
2. Wait 2-3 minutes for build
3. Your app should load at `https://your-app-name.streamlit.app`

---

## Step 7: Verify Production

### 7.1 Test on Your iPhone
1. Open Safari on your iPhone
2. Navigate to `https://your-app-name.streamlit.app`
3. Add to Home Screen for easy access
4. Log a real workout
5. Close browser

### 7.2 Verify Persistence
1. Go to Streamlit Cloud → Your App → "Reboot app"
2. After reboot, refresh on your iPhone
3. **Success:** Your logged workout is still there! 🎉

### 7.3 Verify in Supabase
1. Go to Supabase → Table Editor → `workout_logs`
2. Your new workout from iPhone should be visible
3. This confirms data is truly persistent

---

## Rollback Plan (If Needed)

If something goes wrong, you can rollback:

### Option 1: Quick Rollback
```bash
git revert HEAD
git push origin main
```
This reverts to JSON-based storage. Your local `data/` files are still intact.

### Option 2: Keep Supabase, Re-Migrate
If data looks wrong in Supabase:

1. Go to Supabase → SQL Editor
2. Run:
   ```sql
   TRUNCATE workout_logs, templates, weekly_split, exercises RESTART IDENTITY CASCADE;
   ```
3. Re-run migration script:
   ```bash
   python scripts/migrate_json_to_supabase.py --execute
   ```

---

## Monitoring & Maintenance

### Check Database Usage
1. Go to Supabase → Settings → Usage
2. You're using ~0.06% of free tier (0.3MB / 500MB)
3. At current rate (7 workouts/week × 2.2KB/workout):
   - Monthly: ~61KB
   - Yearly: ~730KB
   - **You'll never hit the 500MB limit**

### Backup Strategy
Supabase automatically backs up your data:
- **Free tier:** 7 days of backups
- **Backups location:** Settings → Database → Backups

### Weekly Split Reset
The app automatically tracks weekly splits. No manual reset needed.

### Old Deleted Logs Cleanup
Logs deleted 30+ days ago can be permanently removed:

```python
from src.data import cleanup_old_deleted_logs
result = cleanup_old_deleted_logs(days_threshold=30)
print(f"Cleaned up {result['deleted_count']} old logs")
```

---

## Troubleshooting

### "Missing Supabase credentials" Error
- **Local:** Check `.env` file has `SUPABASE_URL` and `SUPABASE_KEY`
- **Production:** Check Streamlit Cloud → App Settings → Secrets

### Connection Timeout
- Verify Supabase project is not paused (free tier auto-pauses after 7 days inactivity)
- Go to Supabase Dashboard → should wake up automatically
- Wait 30 seconds and retry

### Data Not Showing Up
1. Check Supabase → Table Editor → `workout_logs`
2. If empty, re-run migration: `python scripts/migrate_json_to_supabase.py --execute`
3. If populated but not showing in app, check for errors in Streamlit logs

### Duplicate Workouts After Migration
This shouldn't happen, but if it does:
```sql
-- Run in Supabase SQL Editor
DELETE FROM workout_logs
WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY id ORDER BY created_at) as row_num
    FROM workout_logs
  ) t
  WHERE row_num > 1
);
```

---

## Next Steps

### Future Enhancements (Optional)

#### Multi-User Support
If you want family members to use the app:
1. Enable Row-Level Security in Supabase
2. Add `user_id` column to tables
3. Use Supabase Auth for login

#### Advanced Queries
Postgres enables powerful analytics:
```sql
-- Monthly workout trends
SELECT
  DATE_TRUNC('month', date) AS month,
  type,
  COUNT(*) as count
FROM workout_logs
WHERE deleted = FALSE
GROUP BY month, type
ORDER BY month DESC;
```

#### API Access
Your data is accessible via REST API:
```bash
curl 'https://xxxxx.supabase.co/rest/v1/workout_logs?select=*&limit=10' \
  -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Authorization: Bearer YOUR_SUPABASE_KEY"
```

---

## Support

### Resources
- **Supabase Docs:** https://supabase.com/docs
- **Streamlit Cloud Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **GitHub Issues:** Create issue in your repo for tracking

### Common Questions

**Q: Will my local JSON files still work?**
A: No, the app now reads from Supabase. Keep `data/` as a backup, but it won't be used.

**Q: Can I switch back to JSON?**
A: Yes, revert the Git commit. Your local files are intact.

**Q: What happens if Supabase goes down?**
A: App won't work temporarily. Supabase has 99.9% uptime. Your data is safe.

**Q: Can I export my data?**
A: Yes! Supabase → Table Editor → Export as CSV. Or use the migration script in reverse.

---

## Congratulations! 🎉

Your Gym Bro app now has:
- ✅ Persistent cloud storage
- ✅ Automatic backups (7 days)
- ✅ Accessible on iPhone without data loss
- ✅ Scalable for future growth
- ✅ Free tier for life at current usage

Happy lifting! 💪
