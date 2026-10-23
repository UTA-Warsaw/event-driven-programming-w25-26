# Task 1: Basic Alerting System

- **Student:** Tariel Saidinov 36489
- **Dashboard Link:** https://urban-rapid-alert-core.base44.app

## List of Emergency Events:
- `fire` (🔥 Fire)
- `flood` (🌊 Flood)
- `hurricane` (🌀 Hurricane)
- `earthquake` (🌋 Earthquake)
- `biohazard` (☣️ Biohazard)

## How It Works:
1. **Frontend UI:** The dashboard interface was created using Base44/Lovable and features interactive buttons for each emergency situation.
2. **Event Handling & Network Request:** Clicking any of the buttons triggers an event handler that sends an asynchronous HTTP `POST` request using the Fetch API.
3. **API Integration Details:**
   - **Endpoint:** `https://edp-alerts.codewithpeter.com/alerts`
   - **Method:** `POST`
   - **Header:** `Content-Type: application/json`
   - **Payload Format:**
     ```json
     {
       "event": "<event_name>",
       "student": "Tariel Saidinov 36489"
     }
     ```
4. **Live Board Verification:** All successful requests are transmitted to the server and displayed in real-time on the shared live alert board at `https://edp-alerts.codewithpeter.com`.
