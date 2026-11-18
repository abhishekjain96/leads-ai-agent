# 🚀 How to Host & Deploy Leads AI Agent Live (Zero Cost)
### Specially Designed for **Abhishek Jain | codube.com**

This guide explains how to host your **Leads AI Agent** live on the internet so that **any client or visitor can test it directly from their phone or browser without needing any setup or API keys**!

---

## 🌟 2 Deployment Options

| Feature | Option 1: Streamlit Community Cloud (⭐ **RECOMMENDED**) | Option 2: Render.com / Railway | Option 3: Vercel |
| :--- | :--- | :--- | :--- |
| **Cost** | **100% FREE Forever** | Free Tier available | Free Serverless |
| **Setup Time** | **2 Minutes** | 5 Minutes | 5 Minutes |
| **Streamlit WebSockets** | ✅ Supported natively | ✅ Supported | ⚠️ Not designed for stateful WebSockets |
| **Headless Chrome** | ✅ Auto-installed via `packages.txt` | ✅ Docker / Native | ❌ Not available (Must use Apify) |
| **Apify Cloud Scraper** | ✅ 100% Supported | ✅ 100% Supported | ✅ 100% Supported |
| **Custom Public URL** | `https://your-name.streamlit.app` | `https://your-app.onrender.com` | `https://your-app.vercel.app` |

---

## 🚀 OPTION 1: Streamlit Community Cloud (Best & 100% Free)

Streamlit Cloud is the official, easiest way to make your app live for clients with a public URL like:  
`https://abhishek-leads-ai.streamlit.app`

### Step 1: Push Code to GitHub
1. Create a new repository on your GitHub account (e.g. `leads-ai-agent`).
2. In your project folder, run in terminal:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Leads AI Agent"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/leads-ai-agent.git
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Cloud (2 Clicks)
1. Go to **[share.streamlit.io](https://share.streamlit.io/)** and sign in with GitHub.
2. Click **"New app"**.
3. Select your repository: `YOUR_USERNAME/leads-ai-agent`, branch: `main`, and main file: `app.py`.
4. (Optional) In **Advanced settings > Secrets**, you can paste your default keys:
   ```toml
   GEMINI_API_KEY = "your-gemini-key"
   APIFY_TOKEN = "your-apify-token"
   ADMIN_PASSWORD = "your-custom-password"
   SMTP_USER = "your-email@gmail.com"
   SMTP_PASS = "your-16-char-app-password"
   ```
5. Click **"Deploy!"** 🎈

Within 1-2 minutes, your agent is **LIVE WORLDWIDE**!

---

## ☁️ OPTION 2: Vercel Deployment

Vercel is serverless, so long-running WebSocket connections and local Chrome binaries are constrained. If you deploy on Vercel:
1. We have included `vercel.json` in this repository.
2. Link your GitHub repository in your **[Vercel Dashboard](https://vercel.com/)**.
3. In **Project Settings > Environment Variables**, add:
   - `GEMINI_API_KEY`
   - `APIFY_TOKEN` (Crucial: on Vercel, the agent automatically uses **Apify** for cloud scraping because serverless functions cannot run desktop Chrome).
4. Click **Deploy**.

---

## 👑 How Admin & Client Demo Mode Works

### 1. For Your Prospective Clients (Visitors)
- When a client opens your live link:
  - They **DO NOT need to enter any API keys or credentials**!
  - They see the **"🟢 Public Client Demo Mode"** banner with your name (**Abhishek Jain**) and agency (**codube.com**).
  - They can select a niche (e.g. *Dental Clinics*, *Digital Marketing Agencies*), choose a city, click **"🚀 Start Lead Hunter Agent"**, and watch the live agent acquire real verified leads!
  - They see your customized WhatsApp messages and cold emails with 1-click test buttons.
  - They can click **"💬 Chat with Abhishek"** to message you directly on WhatsApp to buy your services!

### 2. For You (Admin Settings Portal)
- On the left sidebar, open the **"🔒 Admin Portal"** expander.
- Enter your Admin Passcode (Default: `codube@admin`).
- Click **"Login as Admin"**.
- Now you can:
  - **Set Master Gemini API Key** (so your clients always have AI active for free).
  - **Set Master Apify Token ("apper")** (for lightning-fast cloud scraping).
  - **Set Gmail SMTP** for cold emailing with your poster.
  - **Update Agency Branding & WhatsApp number**.
  - **Clean or Clear test leads** anytime.
- Settings are saved securely into SQLite and remembered permanently!

---

## 📞 Support & Branding
- **Developer:** Abhishek Jain
- **Agency:** codube.com
- **Website:** [https://codube.com](https://codube.com)
