# ML Job Matching API

Cloud-ready job matching system using sentence-transformers for semantic job-resume matching.

## Features

- 🤖 ML-powered job matching using sentence-transformers
- 📍 Location-based sorting with geopy
- 🚀 REST API with Flask
- ☁️ Deploy-ready for Render (free tier)
- 🌐 CORS-enabled for frontend integration

## Quick Start

### Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate Embeddings**
   ```bash
   python generate_embeddings.py
   ```

3. **Start API**
   ```bash
   python app.py
   ```

   API runs on `http://localhost:5000`

### Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/match-jobs` - Match jobs to resume
- `POST /api/match-jobs-with-location` - Match jobs with location sorting

## Tech Stack

- **ML**: sentence-transformers (all-MiniLM-L6-v2)
- **API**: Flask + Flask-CORS
- **Location**: geopy + Nominatim
- **Data**: pandas, numpy

## License

MIT
