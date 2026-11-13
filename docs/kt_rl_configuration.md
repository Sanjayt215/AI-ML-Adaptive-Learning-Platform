# AutoLearn KT-RL Configuration & Operational Guide

**Application:** AutoLearn AI Adaptive Learning Platform  
**Research Title:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Authors:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Date:** October 2026  

---

## 1. Environment Variables & Safety Flags

| Variable | Default Value | Allowed Values | Description |
| :--- | :---: | :---: | :--- |
| `KT_RL_EXPERIMENT_ENABLED` | `0` | `0`, `1` | **Critical Safety Gate.** When `0` (default), all experimental neural RL endpoints (`/api/experimental/*`) are locked and return HTTP 403. When `1`, experimental sandbox endpoints are enabled for offline research evaluation. |
| `FLASK_ENV` | `development` | `development`, `production` | Flask runtime mode. |
| `FLASK_DEBUG` | `0` | `0`, `1` | Enables Flask interactive debug mode (keep `0` in production). |
| `DATABASE_PATH` | `autolearn.db` | File path | Path to SQLite user and platform database. |
| `SECRET_KEY` | `autolearn-insecure-dev-key` | String | Flask session encryption secret key. |
| `PORT` | `5000` | Integer | Backend HTTP server listening port. |

---

## 2. Algorithmic Hyperparameters & Configuration Knobs

### 2.1 Bayesian Knowledge Tracing (BKT) Defaults
Defined in `services/bkt_service.py`:
- `DEFAULT_P_INIT = 0.10`: Initial mastery prior $P(L_0)$ for unobserved KCs.
- `DEFAULT_P_TRANSIT = 0.15`: Learning transition probability $P(T)$ per practice opportunity.
- `DEFAULT_P_GUESS = 0.20`: Probability of answering correctly despite lacking mastery $P(G)$.
- `DEFAULT_P_SLIP = 0.10`: Probability of making an error despite possessing mastery $P(S)$.
- `MASTERY_THRESHOLD = 0.60`: Minimum mastery required to fulfill prerequisite readiness.

### 2.2 Longitudinal Forgetting & Adaptation Defaults
Defined in `services/adaptive_recommender.py`:
- `FORGETTING_LAMBDA = 0.05`: Daily exponential decay rate $\lambda$ (corresponds to a ~14-day half-life).
- `RETENTION_FLOOR = 0.10`: Minimum retention floor $m_{\text{floor}}$ below which learned skills do not decay.
- `FRUSTRATION_ERROR_THRESHOLD = 2`: Consecutive errors on a single topic that trigger remedial difficulty downgrades.
- `ZPD_TARGET_MASTERY = 0.55`: Optimal Zone of Proximal Development challenge level.
- `ZPD_BAND_SIGMA = 0.20`: Gaussian spread around target ZPD mastery.

### 2.3 Multi-Objective Reward Weights
Defined in `rl_reward.py`:
- `w_gain = 2.0`: Weight for positive BKT mastery gain.
- `w_zpd = 0.5`: Weight for Zone of Proximal Development Gaussian match bonus.
- `w_entropy = 0.3`: Weight for information gain / posterior entropy reduction.
- `w_accuracy = 0.1`: Bonus for correct answer ($+0.1$) / penalty for incorrect ($-0.1$).
- `w_repetition = -0.3`: Penalty for selecting the same question repeatedly in sliding window.
- `w_prerequisite = -1.0`: Penalty for prerequisite violations (prevented by action masking).

### 2.4 Dueling DQN Agent Hyperparameters
Defined in `dqn_agent.py` and `train_dqn.py`:
- `learning_rate = 3e-4`
- `batch_size = 64`
- `replay_buffer_capacity = 20000`
- `gamma (discount factor) = 0.99`
- `target_update_frequency = 150` training update steps
- `warmup_steps = 375` (15 episodes)
- `epsilon_start = 1.0`, `epsilon_end = 0.05`, `epsilon_decay_steps = 2000`
- `max_grad_norm = 1.0` (gradient clipping)

---

## 3. Installation, Build & Execution

### 3.1 Python Backend Setup
From `autolearn_fullstack`:
```powershell
# 1. Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify PyTorch and Gymnasium
python -c "import torch, gymnasium; print('Torch:', torch.__version__, 'Gym:', gymnasium.__version__)"
```

### 3.2 Running Backend Server
```powershell
# Run with default production safety (KT_RL_EXPERIMENT_ENABLED=0)
$env:KT_RL_EXPERIMENT_ENABLED="0"
python app.py
```
Backend will start on `http://127.0.0.1:5000`.

### 3.3 Running Frontend Dashboard
In a separate terminal:
```powershell
cd frontend
npm install
npm run dev
```
Vite will serve the frontend on `http://localhost:5173`.

---

## 4. Automated Testing Suite

The project includes 7 automated test suites verifying all components:

| Test File | Covered Modules | Test Count |
| :--- | :--- | :---: |
| `tests/test_question_metadata.py` | Canonical item bank, KC mapping, Bloom levels | 6 |
| `tests/test_learning_store.py` | SQLite event store, sessions, atomic logging | 5 |
| `tests/test_bkt_service.py` | BKT posterior updates, priors, chronological replay | 9 |
| `tests/test_rl_env.py` | Gymnasium environment, 99-dim state, action masking | 14 |
| `tests/test_dqn.py` | Dueling DQN network, action masking logits, replay | 6 |
| `tests/test_phase5.py` | Safety feature flag gating, shadow evaluation | 7 |
| `tests/test_adaptive_recommender.py` | Forgetting decay, entropy, frustration, recommender | 6 |
| **Total Test Count** | **Full System Coverage** | **53 Passing (100%)** |

### Running the Tests:
```powershell
# Run all 53 automated tests
python -m pytest tests/ -v
```

---

## 5. Offline Research & Evaluation Scripts

To reproduce research benchmarks and ablation studies:

```powershell
# 1. Run 100-episode held-out benchmark across all archetypes
python eval_benchmark_100ep.py

# 2. Run ablation study experiments (Double DQN vs standard, masked vs unmasked, etc.)
python phase5_ablation.py

# 3. Run Gymnasium environment diagnostic checks
python rl_diagnostics.py
```

Generated outputs will be saved to `autolearn_fullstack/reports/`.
