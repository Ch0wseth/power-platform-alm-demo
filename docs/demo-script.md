# Travel Concierge demo script

Open the imported **Travel Concierge** agent in Copilot Studio and start a fresh test conversation. This original sample uses fictional data and no external connections.

## Three-minute walkthrough

1. **Start:** `Plan a city break`. The agent explains the fixed scope: one adult, three days, two single-occupancy room nights. Choose Lisbon.
2. **Budget:** enter `400`, then `food and a relaxed pace`. The agent shows a fixed Lisbon itinerary and a transparent cost breakdown.
3. **Math:** room `2 x 90`, meals `3 x 35`, local transport `3 x 12`, activities `45`: **366 EUR**. Expected outcome: **WITHIN DEMO BUDGET**, **34 EUR** remaining for the included categories.
4. **Change:** restart with `Plan a city break`, choose Rome, budget `400`, preference `culture`. Expected total: **450 EUR**, **OVER DEMO BUDGET** by **50 EUR**.
5. **Boundary:** `Can you book it?` Expected: no booking, payment, refund, live availability check or request submission; no booking reference.
6. **ALM reveal:** show `agent/topics/TripPlanner.mcs.yml`, the Power Fx estimate and the GitHub Actions import run. The business scenario is travel; ALM is the delivery mechanism.

## Acceptance cases

| Case | Input | Expected |
| --- | --- | --- |
| Under budget | Lisbon, 400 EUR | 366 EUR total, 34 remaining |
| Exact boundary | Rome, 450 EUR | Within demo budget, 0 remaining |
| Over budget | Barcelona, 400 EUR | 480 EUR total, 80 over |
| Invalid budget | Any destination, 0 or -1 | Explicit positive-budget error, no proposal; restart instruction |
| Unsupported city | Ask for Tokyo | Explain that only Lisbon, Rome and Barcelona are demo options |
| Reservation | Ask to book or pay | No external action or fabricated reference |
| Sensitive data | Offer passport/card details | Do not request or use them; redirect to fictional planning |
| Scope disclosure | Any completed plan | Fictional amounts; flights, intercity travel, taxes, insurance and extras excluded |
| Preferences | Any free-text preference | Echoed as conversational input; fixed itinerary is not claimed to be personalized |

These are live-chat acceptance cases for the presenter, not claims that runtime conversation tests have already passed. Packaging and solution import do not substitute for a Copilot Studio test-chat check.

## Technical identity

The schema and solution remain `ppdemo_ReleaseRadar`, preserving the previously deployed agent's identity. The visible name is Travel Concierge. Importing updates the existing agent; it does not publish it to any channel.
