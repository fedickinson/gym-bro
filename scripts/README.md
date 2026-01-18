# Scripts Directory

Utility scripts for database setup, migration, and testing.

---

## Files

### `schema.sql`
**Purpose**: Database schema definition for Supabase (Postgres)

**Usage**:
1. Copy entire contents
2. Paste into Supabase → SQL Editor → New query
3. Click Run

**Creates**:
- `workout_logs` table (with indexes)
- `templates` table
- `weekly_split` table
- `exercises` table
- Triggers for `updated_at` timestamps

**Run**: Once per Supabase project (during initial setup)

---

### `migrate_json_to_supabase.py`
**Purpose**: One-time migration from local JSON files to Supabase

**Usage**:
```bash
# Preview migration (safe)
python scripts/migrate_json_to_supabase.py --dry-run

# Execute migration (writes to database)
python scripts/migrate_json_to_supabase.py --execute
```

**Migrates**:
- `data/workout_logs.json` → `workout_logs` table
- `data/templates.json` → `templates` table
- `data/weekly_split.json` → `weekly_split` table
- `data/exercises.json` → `exercises` table (if exists)

**Features**:
- Batch inserts (100 rows at a time)
- Progress reporting
- Error handling
- Dry-run mode for testing

**Run**: Once per migration (after database schema is created)

---

### `test_supabase_connection.py`
**Purpose**: Verify Supabase connection and basic database operations

**Usage**:
```bash
python scripts/test_supabase_connection.py
```

**Tests**:
1. Connection to Supabase
2. Table access (all 4 tables)
3. Read operations (get_all_logs, get_all_templates)
4. Write operations (add_log, delete_log_permanent)

**Output**:
- ✅ All tests passed → ready to migrate
- ❌ Tests failed → shows error and troubleshooting steps

**Run**:
- After setting up `.env` file
- Before running migration
- Anytime to verify database health

---

## Execution Order

1. **`schema.sql`** - Run first (in Supabase SQL Editor)
2. **`test_supabase_connection.py`** - Run second (verify setup)
3. **`migrate_json_to_supabase.py`** - Run last (migrate data)

---

## Requirements

All scripts require:
- `.env` file with `SUPABASE_URL` and `SUPABASE_KEY`
- Dependencies installed: `pip install -r requirements.txt`
- Run from project root (not from `scripts/` folder)

---

## Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in project root
cd /path/to/gym-bro

# Run script
python scripts/test_supabase_connection.py
```

### "Missing credentials" errors
```bash
# Check .env file exists
cat .env

# Should contain:
# SUPABASE_URL=https://xxx.supabase.co
# SUPABASE_KEY=eyJ...
```

### Migration fails
```bash
# 1. Verify schema ran successfully
#    → Supabase → Table Editor → should see 4 tables

# 2. Test connection first
python scripts/test_supabase_connection.py

# 3. Try dry-run
python scripts/migrate_json_to_supabase.py --dry-run
```

---

## Additional Scripts (Future)

Potential future scripts:
- `backup_database.py` - Export Supabase data to JSON
- `cleanup_old_logs.py` - Remove old deleted logs
- `sync_exercises.py` - Update exercise definitions
- `verify_data_integrity.py` - Check for data issues

---

## Notes

- All scripts use `src/database.py` for connection management
- Scripts are idempotent where possible (safe to re-run)
- Migration script does NOT delete local JSON files (manual cleanup)
- Test script creates/deletes a temporary workout (safe)

---

For detailed migration instructions, see:
- [SUPABASE_SETUP.md](../SUPABASE_SETUP.md) - Quick start
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Comprehensive guide
- [MIGRATION_CHECKLIST.md](../MIGRATION_CHECKLIST.md) - Step-by-step
