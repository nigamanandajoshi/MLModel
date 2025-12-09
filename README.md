# ML Job Matching API

Production-ready REST API for semantic job matching using ML embeddings.

## Features

- 🤖 ML-powered job matching using sentence-transformers
- 📍 Location-based sorting with geopy
- 🚀 REST API with Flask
- ☁️ Optimized for Render free tier (512MB RAM)
- 🌐 CORS-enabled for frontend integration
- 📝 Works with form data (no resume upload required)

## Deployment

Deployed on Render: `https://your-app.onrender.com`

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions.

## API Endpoints

### `GET /api/health`
Health check - returns model status and job count

### `POST /api/match-jobs`
Match jobs based on user data (form or parsed resume)

**Request:**
```json
{
  "position": "Software Engineer",
  "skills": "Python, React",
  "qualification": "Bachelor's in CS",
  "experience": "3 years"
}
```

**Response:**
Returns top 20 matched jobs with scores

### `POST /api/match-jobs-with-location`
Match jobs and sort by distance from user location

**Request:**
```json
{
  "position": "Software Engineer",
  "skills": "Python, React",
  "location": "San Francisco, CA"
}
```

**Response:**
Returns top 10 jobs sorted by proximity

## Tech Stack

- **ML**: sentence-transformers (all-MiniLM-L6-v2)
- **API**: Flask + Flask-CORS
- **Location**: geopy + Nominatim
- **Data**: numpy

## Memory Optimization

This deployment is optimized for Render's 512MB free tier:
- ✅ No OCR/PDF parsing libraries
- ✅ Uses lightweight sentence-transformers
- ✅ Pre-computed job embeddings
- ✅ Minimal dependencies
