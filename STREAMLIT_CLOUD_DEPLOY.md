# 🚀 Streamlit Cloud Deployment Guide

## ✅ **Why Streamlit Cloud?**
- 100% Free
- Made specifically for Streamlit apps
- Easy GitHub integration
- Automatic HTTPS
- No server management

---

## 📋 **Step-by-Step Deployment:**

### **Step 1: Prepare Your Repository**

1. **Create `.gitignore` file** (to exclude sensitive files):
   ```
   .env
   __pycache__/
   *.pyc
   chroma_store/
   .streamlit/secrets.toml
   ```

2. **Create `.streamlit/config.toml`** (for production settings):
   ```toml
   [server]
   headless = true
   port = 8501
   enableCORS = false
   
   [theme]
   primaryColor = "#667eea"
   backgroundColor = "#ffffff"
   secondaryBackgroundColor = "#f0f2f6"
   textColor = "#262730"
   ```

### **Step 2: Push to GitHub**

```bash
cd "c:\Users\DELL\Downloads\Manuals-Automation-Chatbot-main\Manuals-Automation-Chatbot-main"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Waystar Manuals Intelligence"

# Create repository on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/waystar-manuals-chatbot.git
git branch -M main
git push -u origin main
```

### **Step 3: Deploy on Streamlit Cloud**

1. **Go to:** https://streamlit.io/cloud

2. **Sign in with GitHub**

3. **Click "New app"**

4. **Fill in details:**
   - Repository: `YOUR_USERNAME/waystar-manuals-chatbot`
   - Branch: `main`
   - Main file path: `app/main.py`

5. **Add Secrets (API Keys):**
   Click "Advanced settings" → "Secrets"
   
   Paste this:
   ```toml
   OPENAI_API_KEY = "sk-proj-your-key-here"
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```

6. **Click "Deploy"**

7. **Wait 2-3 minutes** for deployment

8. **Get your URL:** `https://your-app-name.streamlit.app`

---

## 🔒 **Security Notes:**

### **What to NEVER commit to GitHub:**
- ❌ `.env` file (contains API keys)
- ❌ `chroma_store/` (vector database - will rebuild)
- ❌ Any files with secrets

### **What WILL be public:**
- ✅ Your code
- ✅ PDF manuals (in `manuals/` folder)
- ✅ Configuration files

---

## 📁 **Files Needed for Deployment:**

### **1. requirements.txt** (already exists)
Make sure it has all dependencies

### **2. .streamlit/config.toml** (I'll create this)
Production configuration

### **3. .gitignore** (I'll create this)
Exclude sensitive files

### **4. packages.txt** (optional)
System dependencies if needed

---

## 🐛 **Troubleshooting:**

### **Issue: "Module not found"**
**Solution:** Make sure all packages are in `requirements.txt`

### **Issue: "API key not found"**
**Solution:** Add secrets in Streamlit Cloud dashboard

### **Issue: "Out of memory"**
**Solution:** 
- Reduce chunk size in config
- Use smaller embedding model
- Streamlit Cloud has 1GB RAM limit

### **Issue: "Slow first load"**
**Solution:** Normal - it's indexing PDFs. Subsequent loads are fast.

---

## 💡 **Pro Tips:**

1. **Use Streamlit Secrets** instead of `.env`:
   ```python
   # In your code, replace:
   os.getenv("OPENAI_API_KEY")
   
   # With:
   st.secrets["OPENAI_API_KEY"]
   ```

2. **Cache vector store** to avoid re-indexing:
   ```python
   @st.cache_resource
   def load_vectorstore():
       # Your loading code
   ```

3. **Add a loading message**:
   ```python
   with st.spinner("Loading manuals... (first time may take 1-2 minutes)"):
       # Indexing code
   ```

---

## 🎯 **After Deployment:**

Your app will be available at:
```
https://your-app-name.streamlit.app
```

**Share this URL with anyone!** 🎉

---

## 🔄 **Updating Your App:**

Just push to GitHub:
```bash
git add .
git commit -m "Update"
git push
```

Streamlit Cloud will auto-deploy! ✨

---

## 📊 **Streamlit Cloud Limits (Free Tier):**

| Resource | Limit |
|----------|-------|
| RAM | 1 GB |
| CPU | Shared |
| Apps | 1 public app |
| Uptime | Community (may sleep) |

**Need more?** Upgrade to paid plan ($20/month for 3 apps)

---

## 🆚 **Why Not Vercel?**

Vercel is great for:
- ✅ Next.js apps
- ✅ React apps
- ✅ Static sites

But NOT for:
- ❌ Python Streamlit apps
- ❌ Long-running processes
- ❌ Stateful applications

**Streamlit Cloud is purpose-built for Streamlit!**

---

**Ready to deploy? Let me know and I'll help you through each step!**
