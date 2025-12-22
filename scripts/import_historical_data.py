"""
Import Historical Workout Data from Markdown Files.

Parses phase_01.md through phase_10.md to extract logged workout sessions
and converts them to JSON format for workout_logs.json.
"""

import re
from datetime import datetime
from pathlib import Path
import json
from typing import Optional


def parse_date(date_str: str) -> str:
    """
    Convert '25 Jan 2024' to '2024-01-25' (ISO format).

    Args:
        date_str: Date string in format "DD MMM YYYY"

    Returns:
        ISO formatted date string
    """
    try:
        dt = datetime.strptime(date_str.strip(), "%d %b %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return None


def infer_workout_type(workout_name: str) -> str:
    """
    Infer workout type from template name.

    Examples:
        "1.1 Push" -> "Push"
        "2.3 Pull A" -> "Pull"
        "Lower Body" -> "Lower"

    Args:
        workout_name: Template name from markdown

    Returns:
        Workout type (Push/Pull/Legs/Upper/Lower/Other)
    """
    name_lower = workout_name.lower()

    if 'push' in name_lower:
        return 'Push'
    elif 'pull' in name_lower:
        return 'Pull'
    elif 'leg' in name_lower:
        return 'Legs'
    elif 'lower' in name_lower:
        return 'Lower'
    elif 'upper' in name_lower:
        return 'Upper'
    else:
        return 'Other'


def parse_set_string(set_str: str) -> Optional[dict]:
    """
    Parse set string like '10 × 40lbs' into {"reps": 10, "weight_lbs": 40}.

    Args:
        set_str: String like "10 × 40lbs" or "—" (empty)

    Returns:
        Dict with reps and weight_lbs, or None if empty
    """
    set_str = set_str.strip()

    # Handle empty sets
    if set_str in ['—', '-', '', 'N/A']:
        return None

    # Try to match: NUMBER × NUMBERlbs
    match = re.match(r'(\d+)\s*[×x]\s*(\d+\.?\d*)lbs', set_str)
    if match:
        return {
            "reps": int(match.group(1)),
            "weight_lbs": float(match.group(2))
        }

    # Try to match bodyweight (just reps, no weight)
    match = re.match(r'(\d+)\s*reps?', set_str, re.IGNORECASE)
    if match:
        return {
            "reps": int(match.group(1)),
            "weight_lbs": None
        }

    print(f"Warning: Could not parse set string: '{set_str}'")
    return None


def parse_jog_string(jog_str: str) -> Optional[dict]:
    """
    Parse jog data like '0.5 miles, 5:00, speed 6, incline 4, 80 cal'.

    Args:
        jog_str: Jog description string

    Returns:
        Dict with jog details, or None if not a jog
    """
    jog_str = jog_str.strip()

    if jog_str in ['—', '-', '']:
        return None

    # Check if this looks like jog data
    if 'miles' not in jog_str.lower() and 'jog' not in jog_str.lower():
        return None

    warmup = {"type": "jog"}

    # Extract distance (e.g., "0.5 miles")
    dist_match = re.search(r'([\d.]+)\s*miles?', jog_str, re.IGNORECASE)
    if dist_match:
        warmup["distance_miles"] = float(dist_match.group(1))

    # Extract time (e.g., "5:00" or "5 min")
    time_match = re.search(r'(\d+):(\d+)', jog_str)
    if time_match:
        minutes = int(time_match.group(1))
        seconds = int(time_match.group(2))
        warmup["duration_min"] = minutes + seconds / 60.0
    else:
        time_match = re.search(r'(\d+\.?\d*)\s*min', jog_str, re.IGNORECASE)
        if time_match:
            warmup["duration_min"] = float(time_match.group(1))

    # Extract speed
    speed_match = re.search(r'speed\s*(\d+)', jog_str, re.IGNORECASE)
    if speed_match:
        warmup["speed"] = int(speed_match.group(1))

    # Extract incline
    incline_match = re.search(r'incline\s*(\d+)', jog_str, re.IGNORECASE)
    if incline_match:
        warmup["incline"] = int(incline_match.group(1))

    # Extract calories
    cal_match = re.search(r'(\d+)\s*cal', jog_str, re.IGNORECASE)
    if cal_match:
        warmup["calories"] = int(cal_match.group(1))

    return warmup


def parse_workout_table(table_lines: list[str]) -> list[dict]:
    """
    Parse a markdown table of exercises.

    Expected format:
    | Exercise | Set 1 | Set 2 | Set 3 | Set 4 |
    |----------|-------|-------|-------|-------|
    | Dumbbell bench press | 10 × 40lbs | 10 × 40lbs | 10 × 40lbs | 8 × 40lbs |

    Args:
        table_lines: Lines of the markdown table

    Returns:
        List of exercise dictionaries
    """
    exercises = []

    # Skip header and separator
    data_lines = [line for line in table_lines if line.strip().startswith('|') and not line.strip().startswith('|---')]

    if len(data_lines) < 2:  # Need at least header + 1 data row
        return exercises

    # Process each exercise row (skip header)
    for line in data_lines[1:]:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last from split

        if not cells:
            continue

        exercise_name = cells[0].strip()

        # Check if this is a jog row
        if 'jog' in exercise_name.lower():
            # Don't add jog as an exercise (will be added as warmup separately)
            continue

        # Parse sets (remaining cells after exercise name)
        sets = []
        for set_str in cells[1:]:
            parsed_set = parse_set_string(set_str)
            if parsed_set:
                sets.append(parsed_set)

        if sets:  # Only add exercise if it has sets
            exercises.append({
                "name": exercise_name.title(),  # Capitalize properly
                "sets": sets
            })

    return exercises


def extract_warmup_from_table(table_lines: list[str]) -> Optional[dict]:
    """
    Extract jog warmup data from the workout table if present.

    Args:
        table_lines: Lines of the markdown table

    Returns:
        Warmup dict or None
    """
    # Look for a row starting with "Jog"
    for line in table_lines:
        if line.strip().startswith('|') and 'jog' in line.lower():
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if len(cells) >= 2:
                # Jog data is usually in the first set column
                jog_data = cells[1] if len(cells) > 1 else cells[0]
                warmup = parse_jog_string(jog_data)
                if warmup:
                    return warmup

    return None


def parse_logged_session(session_block: str) -> Optional[dict]:
    """
    Parse a single logged session block.

    Example:
    ### 25 Jan 2024
    **Workout:** 1.1 Push

    | Exercise | Set 1 | Set 2 | Set 3 | Set 4 |
    |----------|-------|-------|-------|-------|
    | Dumbbell bench press | 10 × 40lbs | 10 × 40lbs | 10 × 40lbs | 8 × 40lbs |

    Args:
        session_block: Text block for one workout session

    Returns:
        Workout log dictionary or None if parsing fails
    """
    lines = session_block.strip().split('\n')

    # Extract date (first line: "### 25 Jan 2024")
    date_line = lines[0].strip()
    date_match = re.search(r'###\s+(\d+\s+\w+\s+\d{4})', date_line)
    if not date_match:
        return None

    date_str = date_match.group(1)
    iso_date = parse_date(date_str)
    if not iso_date:
        return None

    # Extract workout name (second line: "**Workout:** 1.1 Push")
    workout_name = None
    for line in lines[1:5]:  # Check first few lines
        workout_match = re.search(r'\*\*Workout:\*\*\s*(.+)', line)
        if workout_match:
            workout_name = workout_match.group(1).strip()
            break

    if not workout_name:
        print(f"Warning: No workout name found for {iso_date}")
        workout_name = "Unknown"

    # Extract table
    table_lines = [line for line in lines if '|' in line]

    # Parse exercises
    exercises = parse_workout_table(table_lines)

    # Extract warmup if present
    warmup = extract_warmup_from_table(table_lines)

    # Build workout log
    workout_type = infer_workout_type(workout_name)

    # Generate unique ID: date + counter
    workout_id = f"{iso_date}-001"

    log = {
        "id": workout_id,
        "date": iso_date,
        "type": workout_type,
        "template_id": workout_name.lower().replace(' ', '_'),
        "exercises": exercises,
        "notes": f"Imported from historical data - {workout_name}",
        "completed": True,
        "created_at": f"{iso_date}T12:00:00Z"
    }

    if warmup:
        log["warmup"] = warmup

    return log


def parse_phase_file(phase_path: Path) -> list[dict]:
    """
    Parse a phase markdown file and extract all logged sessions.

    Args:
        phase_path: Path to phase_XX.md file

    Returns:
        List of workout log dictionaries
    """
    content = phase_path.read_text(encoding='utf-8')

    # Find "## Logged Sessions" section
    logged_section_match = re.search(r'##\s+Logged Sessions(.+)', content, re.DOTALL)
    if not logged_section_match:
        print(f"No 'Logged Sessions' section found in {phase_path.name}")
        return []

    logged_section = logged_section_match.group(1)

    # Split by "### DD MMM YYYY" to get individual sessions
    session_blocks = re.split(r'(?=###\s+\d+\s+\w+\s+\d{4})', logged_section)

    logs = []
    for block in session_blocks:
        if not block.strip():
            continue

        log = parse_logged_session(block)
        if log:
            logs.append(log)

    return logs


def import_all_phases():
    """
    Import all 10 phases and append to workout_logs.json.
    """
    print("=" * 60)
    print("HISTORICAL WORKOUT DATA IMPORT")
    print("=" * 60)

    all_logs = []

    # Parse each phase file
    for i in range(1, 11):
        phase_file = Path(f"data/raw/phase_{i:02d}.md")

        if not phase_file.exists():
            print(f"⚠️  {phase_file.name} not found, skipping...")
            continue

        print(f"\n📄 Parsing {phase_file.name}...")

        try:
            logs = parse_phase_file(phase_file)
            all_logs.extend(logs)
            print(f"   ✅ Found {len(logs)} workouts")
        except Exception as e:
            print(f"   ❌ Error parsing {phase_file.name}: {e}")

    print(f"\n{'=' * 60}")
    print(f"📊 Total workouts parsed: {len(all_logs)}")

    # Load existing logs
    logs_file = Path("data/workout_logs.json")
    if logs_file.exists():
        with open(logs_file, 'r') as f:
            existing_data = json.load(f)
        print(f"📁 Existing logs: {len(existing_data.get('logs', []))}")
    else:
        existing_data = {"logs": []}
        print("📁 No existing logs found, creating new file")

    # Avoid duplicates by checking dates
    existing_dates = {log['date'] for log in existing_data.get('logs', [])}
    new_logs = [log for log in all_logs if log['date'] not in existing_dates]

    # Fix duplicate IDs within the same date
    date_counters = {}
    for log in new_logs:
        date = log['date']
        date_counters[date] = date_counters.get(date, 0) + 1
        log['id'] = f"{date}-{date_counters[date]:03d}"

    existing_data['logs'].extend(new_logs)

    # Sort by date
    existing_data['logs'].sort(key=lambda x: x['date'])

    # Save
    with open(logs_file, 'w') as f:
        json.dump(existing_data, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"✅ Imported {len(new_logs)} new workouts")
    print(f"📊 Total workouts in database: {len(existing_data['logs'])}")
    print(f"💾 Saved to: {logs_file}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    import_all_phases()
