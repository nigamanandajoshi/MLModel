# ML Job Matching API - Deployment Guide

## 🚀 Quick Start

### Local Testing

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Regenerate Job Embeddings** (Required after migration)
   ```bash
   python generate_embeddings.py
   ```
   This will create `job_embeddings.json` with the new sentence-transformers model.

3. **Start the API**
   ```bash
   python app.py
   ```
   The API will start on `http://localhost:5000`

4. **Test the API**
   ```bash
   curl -X POST http://localhost:5000/api/match-jobs \
     -H "Content-Type: application/json" \
     -d '{
       "position": "Software Engineer",
       "skills": "Python, Machine Learning",
       "qualification": "Bachelor in Computer Science",
       "experience": "3 years"
     }'
   ```

---

## ☁️ Cloud Deployment (Render)

### Option 1: Deploy via Dashboard

1. **Push Code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - ML job matching API"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Create Render Account**
   - Go to [https://render.com](https://render.com)
   - Sign up with GitHub

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect the `render.yaml` file

4. **Configure Settings** (if needed)
   - **Name**: ml-job-matcher
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes for first deploy)
   - Your API will be live at: `https://ml-job-matcher-xxx.onrender.com`

### Option 2: Deploy via Render Blueprint

1. Push code to GitHub (as above)
2. Go to Render Dashboard → Blueprints
3. Click "New Blueprint Instance"
4. Select your repository
5. Render will use `render.yaml` automatically

---

## 🌐 Connecting to Your Website

### Frontend Integration

Once deployed, update your frontend to call the API:

```javascript
// Example: Match jobs for a user
async function matchJobs(resumeData) {
  const response = await fetch('https://your-api-url.onrender.com/api/match-jobs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      position: resumeData.position,
      skills: resumeData.skills,
      qualification: resumeData.qualification,
      experience: resumeData.experience,
      summary: resumeData.summary,
      work_experience: resumeData.workExperience
    })
  });
  
  const data = await response.json();
  return data.matches; // Array of matched jobs
}

// Example: Match jobs with location sorting
async function matchJobsWithLocation(resumeData) {
  const response = await fetch('https://your-api-url.onrender.com/api/match-jobs-with-location', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      position: resumeData.position,
      skills: resumeData.skills,
      qualification: resumeData.qualification,
      experience: resumeData.experience,
      location: resumeData.location
    })
  });
  
  const data = await response.json();
  return data.matches; // Array of matched jobs sorted by distance
}
```

---

## 📡 API Endpoints

### 1. Health Check
```
GET /api/health
```
Returns API status and loaded data count.

### 2. Match Jobs
```
POST /api/match-jobs
```
**Request Body:**
```json
{
  "position": "Software Engineer",
  "skills": "Python, ML, TensorFlow",
  "qualification": "Bachelor's in CS",
  "experience": "3 years",
  "summary": "Experienced developer...",
  "work_experience": "Worked at company X..."
}
```

**Response:**
```json
{
  "success": true,
  "matches": [
    {
      "match_score": 0.87,
      "breakdown": {
        "pos_score": 0.92,
        "skill_score": 0.85,
        "qual_score": 0.88,
        "exp_score": 0.80
      },
      "job_details": {
        "job title": "Senior ML Engineer",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "job description": "...",
        "required qualification": "..."
      }
    }
  ],
  "total_matches": 20
}
```

### 3. Match Jobs with Location
```
POST /api/match-jobs-with-location
```
Same as above, but include `"location": "City, State"` in the request body.

**Additional Response Fields:**
- `distance_km`: Distance from resume location to job location
- `location_rank`: Rank based on proximity (1 = nearest)
- `location_sorted`: Whether results are sorted by location

---

## 🔧 Environment Variables

For Render deployment, you can set these in the dashboard:

- `PORT`: Automatically set by Render (default: 5000)
- `PYTHON_VERSION`: 3.11.0 (set in render.yaml)

---

## 🐛 Troubleshooting

### Issue: "Job embeddings file not found"
- **Solution**: Make sure `job_embeddings.json` is committed to your repository
- Run `python generate_embeddings.py` locally first, then commit the file

### Issue: "Model download timeout"
- **Solution**: First deployment may take 10-15 minutes as Render downloads the ML model
- This is normal; subsequent deploys will be faster

### Issue: "Out of memory"
- **Solution**: The free tier has 512MB RAM. If you hit limits:
  - Reduce `TOP_N_MATCHES` in `app.py` (line 23)
  - Consider upgrading to Render's paid tier ($7/month for 2GB RAM)

### Issue: "CORS errors from frontend"
- **Solution**: CORS is already enabled in `app.py`
- Make sure you're using the correct API URL in your frontend

### Issue: "Geocoding fails"
- **Solution**: Nominatim has rate limits. The code includes retry logic and delays
- For production, consider using Google Maps API (requires API key)

---

## 📊 Performance Tips

1. **Model Caching**: The model loads once at startup (not per request)
2. **Job Matrix**: Pre-calculated at startup for fast matching
3. **Cold Starts**: Render's free tier may sleep after inactivity. First request after sleep takes ~30 seconds

---

## 🔐 Security Notes

- API is currently open (no authentication)
- For production, consider adding API keys or rate limiting
- Don't commit sensitive data to the repository

---

## 📈 Monitoring

- **Render Dashboard**: View logs, metrics, and deployment history
- **Health Endpoint**: Use `/api/health` for uptime monitoring

---

## 💰 Cost Breakdown

### Free Tier (Render)
- ✅ 750 hours/month (enough for 24/7 uptime)
- ✅ 512MB RAM
- ✅ Automatic HTTPS
- ⚠️ Sleeps after 15 minutes of inactivity
- ⚠️ Limited to 100GB bandwidth/month

### Paid Tier ($7/month)
- ✅ No sleep
- ✅ 2GB RAM
- ✅ Priority support

---

## 🔄 Updating the Model

To update job embeddings:
1. Update `Data.csv` with new jobs
2. Run `python generate_embeddings.py`
3. Commit `job_embeddings.json`
4. Push to GitHub
5. Render auto-deploys

---

## 📞 Support

For issues with:
- **Code**: Check the API logs in Render dashboard
- **Deployment**: Render has excellent documentation at render.com/docs
- **Model**: sentence-transformers docs at sbert.net
