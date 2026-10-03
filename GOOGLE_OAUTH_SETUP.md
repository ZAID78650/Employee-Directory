# Google Cloud OAuth 2.0 Setup Guide

This guide walks you through setting up real, production-ready Google Authentication for the **Employee Directory** application.

---

## 1. Create / Select Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown at the top and select **New Project** (e.g. `Employee-Directory-Auth`).

---

## 2. Configure OAuth Consent Screen
1. Navigate to **APIs & Services** &rarr; **OAuth consent screen**.
2. Select **External** (or **Internal** if using Google Workspace organization).
3. Fill in:
   - **App name:** `Employee Directory`
   - **User support email:** Your email address
   - **Developer contact information:** Your email address
4. Under **Scopes**, ensure the minimum OpenID Connect identity scopes are added:
   - `.../auth/userinfo.email` (`email`)
   - `.../auth/userinfo.profile` (`profile`)
   - `openid`
5. If the app is in **Testing** status, add your Google account (e.g., `szaid8364@gmail.com`) under **Test Users**.

---

## 3. Create Web Application OAuth 2.0 Credentials
1. Navigate to **APIs & Services** &rarr; **Credentials**.
2. Click **+ CREATE CREDENTIALS** &rarr; **OAuth client ID**.
3. Set **Application type:** `Web application`.
4. Set **Name:** `Employee Directory Web Client`.
5. Under **Authorized JavaScript origins**:
   - `http://localhost:5001`
6. Under **Authorized redirect URIs**:
   - `http://localhost:5001/auth/google/callback`
7. Click **Create**.
8. Copy the **Client ID** and **Client Secret**.

---

## 4. Configure Application Environment
1. Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
2. Paste your Google credentials into `.env`:
   ```env
   PORT=5001
   SECRET_KEY=your-secure-random-secret-key
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:5001/auth/google/callback
   GOOGLE_SCOPES=openid profile email
   ```

---

## 5. Run & Test Real Google Login
1. Start the server:
   ```bash
   python3 app.py
   ```
2. Open **[http://localhost:5001/login](http://localhost:5001/login)**.
3. Click **Continue with Google**.
4. The browser will redirect directly to Google's official account authorization page.
5. Upon consent, Google redirects back to `http://localhost:5001/auth/google/callback`, creating your authenticated session and directing you to the dashboard.
