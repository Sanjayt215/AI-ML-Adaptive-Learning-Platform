# AutoLearn KT-RL Phase 6 System Acceptance & Operational Guide

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Date:** October 2026  

---

## 1. System Requirements & Prerequisites

- **Operating System:** Windows 10/11, Linux (Ubuntu 20.04+), or macOS
- **Python Environment:** Python 3.10 to 3.13 (Virtual environment in `autolearn_fullstack/.venv`)
  - Key Libraries: `torch` (PyTorch 2.1+), `gymnasium` (0.29+), `numpy`, `flask` (3.0+), `requests`
- **Node.js Environment:** Node.js 18+ and npm 9+
- **Database:** SQLite 3 (self-contained files: `autolearn.db` and `learner_events.db`)

---

## 2. Environment Variables & Safety Configuration

Before starting any services, verify feature flag configurations:

| Variable | Recommended Value | Purpose |
| :--- | :---: | :--- |
| `KT_RL_EXPERIMENT_ENABLED` | `0` | **Production Safety Invariant.** Strictly disables experimental neural DQN execution in production routes. |
| `PORT` | `5001` | Backend HTTP listening port. Must match frontend `"proxy": "http://localhost:5001"`. |
| `PYTHONPATH` | Project root | Enables clean package imports across tests and services. |
| `FLASK_ENV` | `development` | Runtime environment. |

---

## 3. Step-by-Step Startup Sequence

### Step 3.1: Start Python Backend (Terminal 1)
Open PowerShell or your shell in the workspace root:
```powershell
# Navigate to fullstack directory
cd autolearn_fullstack

# Ensure safety feature gate is set
$env:KT_RL_EXPERIMENT_ENABLED="0"
$env:PORT="5001"

# Launch Flask server
.\.venv\Scripts\python.exe app.py
```
*Expected Output:*
```
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5001
```

### Step 3.2: Start React Frontend (Terminal 2)
In a separate terminal:
```powershell
cd autolearn_fullstack\frontend
npm start
```
*Expected Behavior:*
Browser opens automatically at `http://localhost:3000` (or `http://localhost:5173`).

### Step 3.3: Verify System Status
In a third terminal:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5001/api/status" -Method GET
```
*Expected Output:*
```json
{
  "engine": "baseline_automl",
  "ok": true,
  "real_data_used": true,
  "rows": 33637
}
```

---

## 4. Test & Verification Execution

### 4.1 Run Full Automated Test Suite (59 Tests)
Run from the workspace root:
```powershell
$env:PYTHONPATH="C:\Users\sanja\Downloads\autolearn_llm_ml_upgrade_ready"
.\autolearn_fullstack\.venv\Scripts\python.exe -m unittest discover -s autolearn_fullstack/tests -p "test_*.py" -v
```
*Expected Result:*
```
Ran 59 tests in ~7.4s
OK
```

### 4.2 Run Live End-to-End API Acceptance Tests
With the backend running on port 5001:
```powershell
.\autolearn_fullstack\.venv\Scripts\python.exe autolearn_fullstack\tests\live_system_acceptance.py
```
*Expected Result:*
```
[PASS] 1. /api/status OK
[PASS] 2. /api/learning/items OK (52 items verified)
[PASS] 3. /api/learning/sessions OK
...
[PASS] 11. /api/experimental/recommendation safely fell back
[PASS] 12. Session completion OK
ALL LIVE ACCEPTANCE TESTS PASSED SUCCESSFULLY!
```

### 4.3 Run 9-Policy Research Benchmark & Reproducibility Harness
```powershell
$env:PYTHONPATH="C:\Users\sanja\Downloads\autolearn_llm_ml_upgrade_ready"
.\autolearn_fullstack\.venv\Scripts\python.exe autolearn_fullstack\services\evaluate_all_9_policies.py
```
*Expected Result:*
Executes 180 simulated episodes across all 4 learner archetypes and saves results to `reports/phase6_reproducibility_results.json`.

### 4.4 Build React Frontend
```powershell
cd autolearn_fullstack\frontend
npm run build
```
*Expected Result:*
`Compiled successfully.`

---

## 5. Troubleshooting Common Issues

1. **Port Conflict (`Address already in use`):**
   - Check if port 5001 is already bound:
     ```powershell
     Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue
     ```
   - Stop any existing python processes:
     ```powershell
     Stop-Process -Name python -Force
     ```

2. **ModuleNotFoundError (`No module named 'services'` or `'autolearn_fullstack'`):**
   - Set the `PYTHONPATH` environment variable to the root folder:
     ```powershell
     $env:PYTHONPATH="C:\Users\sanja\Downloads\autolearn_llm_ml_upgrade_ready"
     ```

3. **Frontend API Connection Issues (`CORS` or `Network Error`):**
   - Ensure the backend is running on `127.0.0.1:5001`.
   - Verify `autolearn_fullstack/frontend/package.json` contains `"proxy": "http://localhost:5001"`.

---

## 6. Safe Shutdown Instructions

When testing or demonstration is concluded:
1. Stop the React development server: Press `Ctrl + C` in the frontend terminal.
2. Stop the Flask backend server: Press `Ctrl + C` in the backend terminal.
3. Clean temporary session cache if desired:
   ```powershell
   # Session data is preserved in autolearn.db and learner_events
   # To reset test user states without touching core platform tables:
   .\.venv\Scripts\python.exe -c "from services.learning_store import init_db; print('DB ready')"
   ```
