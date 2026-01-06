# Respondent ID Implementation Guide

## Overview
This guide adds unique respondent identifiers to track survey takers across sessions and responses. Each respondent gets a unique ID that persists across their browser sessions.

## Step-by-Step Implementation

### Step 1: Update Database Models
1. Replace `backend/app/models.py` with the updated version
2. Key changes:
   - Added `respondent_id` to `Session` table
   - Added `respondent_id` to `Response` table (denormalized for easy querying)
   - Added `respondent_id` to `ConversationTurn` table

### Step 2: Create Migration
1. Create new file: `backend/alembic/versions/002_add_respondent_id.py`
2. Run the migration:
   ```bash
   cd backend
   alembic upgrade head
   ```
3. This will:
   - Add `respondent_id` columns to all relevant tables
   - Backfill existing data with legacy IDs
   - Create indexes for fast querying

### Step 3: Update Schemas
1. Replace `backend/app/schemas.py` with updated version
2. Changes:
   - `SessionCreate` now accepts optional `respondent_id`
   - All response models include `respondent_id`

### Step 4: Update Session Service
1. Update `backend/app/services/session_service.py`
2. Key functions added:
   - `generate_respondent_id()`: Creates UUID-based IDs
   - `get_sessions_by_respondent()`: Query sessions by respondent
   - `get_all_responses_by_respondent()`: Query all responses

### Step 5: Add API Endpoints
1. Create new file: `backend/app/api/respondents.py` (use the artifact)
2. New endpoints:
   - `GET /respondents/{respondent_id}/sessions`: Get all sessions
   - `GET /respondents/{respondent_id}/responses`: Get all responses
   - `GET /respondents/{respondent_id}/conversation`: Get conversation history
   - `GET /respondents/{respondent_id}/summary`: Get activity summary

### Step 6: Update Main.py
1. Add import: `from .api import respondents`
2. Add router: `app.include_router(respondents.router)`

### Step 7: Update Frontend
1. Update `frontend/js/survey.js` with respondent ID functions
2. The system will:
   - Generate a unique ID when first visiting
   - Store it in localStorage
   - Include it in all API calls
   - Persist across page refreshes

3. Update `frontend/index.html` to display the respondent code
4. Add CSS from the artifact to `frontend/css/main.css`

### Step 8: Test the Implementation

#### Test 1: Create New Session
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"survey_id": 1}'
```
Expected: Response includes auto-generated `respondent_id`

#### Test 2: Query Respondent Data
```bash
curl http://localhost:8000/respondents/{respondent_id}/summary
```
Expected: Summary of all activity for that respondent

#### Test 3: Frontend Flow
1. Open survey in browser
2. Check console for "Created new respondent ID"
3. Complete survey
4. Refresh page
5. Check console for "Using existing respondent ID"

## Data Analysis Benefits

With respondent IDs, you can now easily:

### SQL Queries
```sql
-- Get all responses from a specific respondent
SELECT * FROM responses WHERE respondent_id = 'resp_xxx';

-- Count responses per respondent
SELECT respondent_id, COUNT(*) 
FROM responses 
GROUP BY respondent_id;

-- Find respondents who completed multiple sessions
SELECT respondent_id, COUNT(DISTINCT session_id) as session_count
FROM responses
GROUP BY respondent_id
HAVING COUNT(DISTINCT session_id) > 1;

-- Get conversation history for analysis
SELECT ct.respondent_id, ct.speaker, ct.message, ct.timestamp
FROM conversation_turns ct
ORDER BY ct.respondent_id, ct.timestamp;
```

### Python Analysis
```python
import pandas as pd

# Load all responses
df = pd.read_sql("SELECT * FROM responses", engine)

# Group by respondent
respondent_groups = df.groupby('respondent_id')

# Analyze response patterns
avg_responses = respondent_groups.size().mean()
completion_rates = respondent_groups['session_id'].nunique()
```

## Optional: Manual Respondent ID Entry

If you want users to enter their own code (instead of auto-generation):

```javascript
// Add to survey.js
function promptForRespondentId() {
    const existingId = localStorage.getItem('polling_survey_respondent_id');
    
    if (existingId) {
        return existingId;
    }
    
    const userInput = prompt('Enter your survey code (or leave blank for new):');
    
    if (userInput && userInput.trim()) {
        const respondentId = userInput.trim();
        localStorage.setItem('polling_survey_respondent_id', respondentId);
        return respondentId;
    }
    
    return generateRespondentId();
}

// Use in startSurvey
const respondentId = promptForRespondentId();
```

## Troubleshooting

### Migration Fails
- Ensure you're in the `backend` directory
- Check database connection in `.env`
- Try: `alembic downgrade -1` then `alembic upgrade head`

### Respondent ID Not Showing
- Check browser console for errors
- Verify localStorage is enabled
- Check that `displayRespondentId()` is called

### API Returns 404
- Verify respondent ID format
- Check database has data: `SELECT * FROM sessions LIMIT 5;`
- Ensure migration ran successfully

## Next Steps

1. Add export functionality that groups by respondent_id
2. Create admin dashboard to view respondent-level statistics
3. Implement respondent ID verification for returning users
4. Add data anonymization for privacy compliance