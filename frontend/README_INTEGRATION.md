# AutoLearn React Frontend — Integration Guide

## Project Structure

```
autolearn_final_upgrade/          ← Your existing Flask project (unchanged)
autolearn_react_frontend/         ← New React frontend (drop alongside Flask)
  ├── public/
  │   └── index.html
  ├── src/
  │   ├── App.jsx
  │   ├── index.js
  │   ├── index.css
  │   ├── components/
  │   │   ├── Layout.jsx
  │   │   ├── StatCard.jsx
  │   │   ├── HeatmapGrid.jsx
  │   │   └── ProgressRing.jsx
  │   ├── pages/
  │   │   ├── HomePage.jsx
  │   │   ├── GoalSelectionPage.jsx
  │   │   ├── StartPage.jsx
  │   │   ├── QuizPage.jsx
  │   │   ├── DashboardPage.jsx
  │   │   ├── LearningPathPage.jsx
  │   │   ├── ResourcesPage.jsx
  │   │   └── TutorPage.jsx
  │   ├── hooks/
  │   │   └── useFlaskData.js
  │   └── utils/
  │       └── mockData.js
  ├── package.json
  └── tailwind.config.js
```

---

## Option A — Run as Standalone Dev (Recommended for development)

This uses mock data — no Flask needed. Perfect for UI development.

```bash
cd autolearn_react_frontend
npm install
npm start
# Opens at http://localhost:3000
```

The `proxy` in package.json points to `http://localhost:5000` so API calls
to `/start`, `/quiz`, `/tutor` etc. are forwarded to Flask when running.

---

## Option B — Full Integration with Flask (Production)

### Step 1 — Build the React app

```bash
cd autolearn_react_frontend
npm install
npm run build
# Creates: autolearn_react_frontend/build/
```

### Step 2 — Copy build into Flask static folder

```bash
cp -r autolearn_react_frontend/build/* autolearn_final_upgrade/static/react/
```

### Step 3 — Add a new Flask route to serve React

In `app.py`, add this route:

```python
from flask import send_from_directory

@app.route('/app')
@app.route('/app/<path:path>')
def react_app(path=''):
    return send_from_directory('static/react', 'index.html')

@app.route('/static/react/<path:filename>')
def react_static(filename):
    return send_from_directory('static/react', filename)
```

Now visit `http://localhost:5000/app` to see the React UI.

---

## Option C — Inject Flask data into React (Hybrid)

Keep all existing Flask routes + Jinja2 templates. Add a `<script>` block
to your existing `base.html` BEFORE the closing `</body>` tag:

```html
<!-- In templates/base.html, before </body> -->
<script>
  // Dashboard data
  {% if assessment is defined %}
  window.__ASSESSMENT__      = {{ assessment | tojson | safe }};
  window.__PROFILE__         = {{ profile | tojson | safe }};
  window.__MODEL_SCORES__    = {{ model_scores | tojson | safe }};
  window.__DATA_INFO__       = {{ dataset_summary | tojson | safe }};
  window.__MODERN_FEATURES__ = {{ modern_features | tojson | safe }};
  window.__MODEL_NAME__      = {{ model_name | tojson | safe }};
  window.__AUTOML_ENGINE__   = {{ automl_engine | tojson | safe }};
  window.__YOUTUBE_LIVE__    = {{ youtube_live | tojson | safe }};
  {% endif %}

  // Learning Path data
  {% if steps is defined %}
  window.__LEARNING_PATH__   = {{ steps | tojson | safe }};
  {% endif %}

  // Resources data
  {% if resource_cards is defined %}
  window.__RESOURCES__       = {{ resource_cards | tojson | safe }};
  {% endif %}

  // Quiz data
  {% if quiz_items is defined %}
  window.__QUIZ_ITEMS__      = {{ quiz_items | tojson | safe }};
  {% endif %}
</script>
```

Then include the React bundle in `base.html`:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='react/static/css/main.css') }}">
<!-- at end of body: -->
<script src="{{ url_for('static', filename='react/static/js/main.js') }}"></script>
```

---

## How Data Flows

```
Flask session data
      │
      ▼
Jinja2 template renders window.__* globals into <script> tags
      │
      ▼
React reads via useFlaskData() hook
      │
      ├── If window.__ASSESSMENT__ exists → use real data
      └── If not → fall back to mockData.js (for dev)
```

---

## Page → Flask Route Mapping

| React Page          | Flask Route     | Form Action  |
|---------------------|-----------------|--------------|
| StartPage           | /start          | POST /start  |
| QuizPage            | /quiz           | POST /quiz   |
| DashboardPage       | /dashboard      | —            |
| LearningPathPage    | /path           | —            |
| ResourcesPage       | /resources      | GET filters  |
| TutorPage           | /tutor          | POST /tutor  |

---

## Dependencies

```
react + react-dom       18.x    — UI framework
react-router-dom        6.x     — Client-side routing
recharts                2.x     — Charts (LineChart, RadarChart, BarChart)
lucide-react            0.363   — Icon library
axios                   1.x     — HTTP (optional, forms use native POST)
tailwindcss             3.x     — Utility CSS
```

Install all:
```bash
npm install
```

---

## Quick Checklist

- [ ] `npm install` done
- [ ] `npm start` works with mock data
- [ ] Flask running on port 5000
- [ ] `package.json` proxy set to `http://localhost:5000`
- [ ] `window.__*__` injected in `base.html` (Option C)
- [ ] Forms posting to correct Flask endpoints

---

## Known Notes

- **Forms** in StartPage and QuizPage use native HTML `method="post"` to submit
  directly to Flask. This is intentional — it keeps your Flask session logic intact.
- **TutorPage** in standalone mode simulates AI responses locally. In production,
  hook up the POST to `/tutor` and render the Flask response.
- **Resources filter** in standalone mode filters mock data. For Flask integration,
  pass filter values as query params to `/resources?topic=...&level=...`.
