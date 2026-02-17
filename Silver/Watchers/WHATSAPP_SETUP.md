# WhatsApp Watcher — Setup Guide (Silver Tier)

WhatsApp messages directly Silver/Inbox mein aayenge.
Twilio Sandbox bilkul free hai testing ke liye.

---

## Step 1 — Libraries install karo

```
cd "C:\Users\aasif\Documents\AI_Employee_Vault\Silver\Watchers"
pip install -r requirements.txt
```

---

## Step 2 — Twilio account banao (free)

1. Browser mein jao: https://www.twilio.com/try-twilio
2. Sign up karo (free — credit card nahi chahiye)
3. Email verify karo

---

## Step 3 — WhatsApp Sandbox activate karo

1. Twilio Console mein login karo
2. Left menu → **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Sandbox number dikhega — jaise: `+1 415 523 8886`
4. Apne phone se WhatsApp par yeh number save karo
5. Sandbox join karne ke liye message bhejo:
   ```
   join <sandbox-keyword>
   ```
   (keyword Twilio console mein dikhega — jaise `join silver-agent`)

---

## Step 4 — ngrok install aur chalao

ngrok aapke local server ko internet pe expose karta hai.

**Download:** https://ngrok.com/download

Terminal 1 mein chalao:
```
ngrok http 5000
```

Output mein kuch aisa dikhega:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
```

Yeh `https://abc123.ngrok.io` URL copy kar lo.

---

## Step 5 — Twilio Webhook set karo

1. Twilio Console → **Messaging** → **Try it out** → **WhatsApp**
2. **Sandbox Settings** pe click karo
3. "When a message comes in" wali field mein paste karo:
   ```
   https://abc123.ngrok.io/whatsapp
   ```
4. Method: **HTTP POST**
5. **Save** karo

---

## Step 6 — Watchers chalao (3 terminals)

**Terminal 1** — WhatsApp webhook server:
```
cd "C:\Users\aasif\Documents\AI_Employee_Vault\Silver\Watchers"
python whatsapp_watcher.py
```

**Terminal 2** — File watcher (Inbox monitor):
```
cd "C:\Users\aasif\Documents\AI_Employee_Vault\Silver\Watchers"
python file_watcher.py
```

**Terminal 3** — ngrok:
```
ngrok http 5000
```

---

## Test karo

Apne phone se sandbox number par WhatsApp message bhejo:
```
Test task — website ka login page kaam nahi kar raha
```

Obsidian mein dekho:
- `Silver/Inbox/` mein file aayegi
- `file_watcher` usse triage karega
- Risk level ke mutabiq `Needs_Action` ya `Awaiting_Approval` mein jaayegi
- Dashboard update hoga

---

## Auto-Reply band karna (optional)

`whatsapp_watcher.py` mein yeh line remove karo:
```python
resp.message("Aapka message receive ho gaya. Jald hi jawab milega.")
```

---

## Workflow (Silver + WhatsApp)

```
WhatsApp message
      ↓
Twilio receives
      ↓
ngrok forward → Flask webhook (port 5000)
      ↓
Silver/Inbox/WHATSAPP_xxx.md
      ↓
file_watcher.py detect karta hai
      ↓
triage_item() — risk classify karta hai
      ↓
Low/Medium risk → Needs_Action
High risk       → Awaiting_Approval
      ↓
(manually) complete_item → Done + Memory update
```
