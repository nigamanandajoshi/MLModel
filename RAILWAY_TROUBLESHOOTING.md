# Railway Build Troubleshooting

## Common Railway Build Failures & Fixes

### Issue 1: Python Version Not Detected
**Error**: "Could not detect Python version"

**Fix**: Add `runtime.txt`:
```
python-3.11.0
```

### Issue 2: Dependencies Installation Failed
**Error**: "pip install failed" or "Could not install requirements"

**Fix**: Check `requirements.txt` - remove or update problematic packages

### Issue 3: File Too Large
**Error**: "File exceeds size limit"

**Fix**: Railway handles large files better than Render, but if issue persists:
- The 6.7MB `job_embeddings.json` should be fine
- Check if it's in `.gitignore` (it shouldn't be)

### Issue 4: Build Timeout
**Error**: "Build exceeded time limit"

**Fix**: Railway has generous build times, but if timeout occurs:
- Check if model is being downloaded during build
- Our lazy loading should prevent this

### Issue 5: Start Command Failed
**Error**: "Application failed to start"

**Fix**: Make sure `app.py` has:
```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

---

## Quick Fixes to Try

### 1. Add Procfile
I just created `Procfile` with:
```
web: python app.py
```

### 2. Add runtime.txt
Specifies Python version:
```
python-3.11.0
```

### 3. Verify requirements.txt
Make sure all packages are compatible:
```
sentence-transformers
numpy
pandas
geopy
flask
flask-cors
tqdm
torch
```

### 4. Check Railway Settings
In Railway dashboard:
- Build command: (leave empty, auto-detected)
- Start command: `python app.py` or leave empty
- Environment: Select Python

---

## Debug Steps

1. **Check Railway Logs**:
   - Go to your Railway project
   - Click "Deployments"
   - Click the failed deployment
   - Check "Build Logs" tab
   - Share the error message with me!

2. **Common Error Messages**:
   - "ModuleNotFoundError" - Missing dependencies
   - "MemoryError" - File too large (unlikely on Railway)
   - "SyntaxError" - Code issue
   - "Port binding failed" - Port config issue

3. **Quick Test Locally**:
   ```bash
   # Make sure it works locally first
   python app.py
   ```

---

## What Error Are You Seeing?

Please share:
1. The error message from Railway logs
2. At what stage did it fail? (Build or Deploy)
3. Any specific package mentioned in error

Then I can give you the exact fix!

---

## Alternative: Use Nixpacks Config

Create `nixpacks.toml`:
```toml
[phases.setup]
nixPkgs = ["python311"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "python app.py"
```
