# Finance App

A comprehensive financial management application for tracking investments, monitoring stock markets, managing portfolios, and receiving alerts on market conditions. The application consists of a FastAPI backend with PostgreSQL database and a Vue.js frontend.

## Features

### Portfolio Management
- Track investment positions with purchase and sale records
- Calculate realized and unrealized profit and loss (P&L)
- View current market prices for portfolio holdings
- Organize positions by active and sold status
- Detailed position tracking with dates and prices

### Watchlist
- Monitor stocks and assets of interest
- Add and remove tickers from watchlist
- Quick access to market analysis for watched assets

### Market Analysis
- Historical price data visualization
- Technical indicators including:
  - MACD (Moving Average Convergence Divergence)
  - RSI (Relative Strength Index)
  - Stochastic Oscillator
  - Bollinger Bands
  - ATR (Average True Range)
  - OBV (On-Balance Volume)
- Interactive charts for price, volume, and indicators
- Fundamental data display

### Alerts
- Configure alerts for technical indicators
- Support for multiple indicator types (MACD, RSI, Stochastic, Bollinger Bands)
- Multiple condition types (cross above, cross below, greater than, less than)
- Active/inactive alert management
- Automatic alert triggering

### Dashboard
- Portfolio overview with key metrics
- Visual charts for P&L distribution
- Portfolio allocation visualization
- Top performers analysis
- Recent positions, watchlist items, and alerts summary

## Technology Stack

### Backend
- FastAPI - Modern Python web framework
- PostgreSQL - Relational database
- SQLAlchemy - ORM for database operations
- Celery - Asynchronous task queue
- Redis - Message broker for Celery
- yfinance - Market data fetching
- pandas & pandas-ta - Data analysis and technical indicators
- JWT - Authentication tokens
- bcrypt - Password hashing

### Frontend
- Vue.js 3 - Progressive JavaScript framework
- TypeScript - Type-safe JavaScript
- Vue Router - Client-side routing
- Pinia - State management
- Chart.js & Vue-ChartJS - Data visualization
- Axios - HTTP client
- Lucide Vue - Icon library
- Vite - Build tool and dev server

## Project Structure

```
finance_app/
├── finance_backend/          # Backend API
│   ├── app/
│   │   ├── core/            # Core business logic
│   │   │   ├── market/      # Market data and analysis
│   │   │   ├── config.py    # Configuration
│   │   │   └── security.py  # Authentication utilities
│   │   ├── db/              # Database models and connection
│   │   ├── routers/         # API route handlers
│   │   └── schemas/         # Pydantic schemas
│   ├── tests/               # Test suite
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
└── finance_frontend/         # Frontend application
    ├── src/
    │   ├── components/      # Vue components
    │   ├── views/           # Page views
    │   ├── services/        # API service layer
    │   ├── stores/          # Pinia stores
    │   └── router/          # Route configuration
    ├── package.json
    └── vite.config.ts
```

## Prerequisites

- Docker and Docker Compose
- Node.js 20.19.0 or >= 22.12.0 (for local frontend development)
- Python 3.12+ (for local backend development)

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd finance_app
```

2. Navigate to the backend directory:
```bash
cd finance_backend
```

3. Create a `.env` file (optional, defaults are provided):
```bash
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=finances_db
DB_PORT=5432
SECRET_KEY=your-secret-key-change-in-production
DEBUG=true
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

4. Start the services:
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- Redis on port 6379
- FastAPI backend on port 8000
- Celery worker for background tasks
- Celery beat for scheduled tasks

5. Navigate to the frontend directory:
```bash
cd ../finance_frontend
```

6. Install dependencies:
```bash
npm install
```

7. Create a `.env` file for frontend:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

8. Start the frontend development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Local Development (Without Docker)

#### Backend Setup

1. Navigate to backend directory:
```bash
cd finance_backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL database and update connection settings in `app/core/config.py`

5. Run database migrations (tables are created automatically on startup):
```bash
python -m app.main
```

6. Start the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

7. Start Celery worker (in a separate terminal):
```bash
celery -A app.celery_worker worker -l info
```

8. Start Celery beat (in a separate terminal):
```bash
celery -A app.celery_worker beat -l info
```

#### Frontend Setup

1. Navigate to frontend directory:
```bash
cd finance_frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

4. Start development server:
```bash
npm run dev
```

## Usage

### Accessing the Application

1. Open your browser and navigate to `http://localhost:5173`
2. Register a new account or login with existing credentials
3. Start by adding positions to your portfolio or tickers to your watchlist

### API Documentation

Once the backend is running, API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Running Tests

#### Backend Tests

Using Docker:
```bash
cd finance_backend
docker-compose --profile test up test
```

Or locally:
```bash
cd finance_backend
pytest
```

#### Frontend Tests

Unit tests:
```bash
cd finance_frontend
npm run test:unit
```

End-to-end tests:
```bash
cd finance_frontend
npm run test:e2e
```

### Building for Production

#### Frontend

```bash
cd finance_frontend
npm run build
```

The production build will be in the `dist/` directory.

#### Backend

The backend is ready for production when running in Docker. For standalone deployment, ensure:
- Environment variables are properly configured
- Database is properly set up
- Celery workers and beat are running
- SECRET_KEY is changed to a secure value

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and receive JWT token
- `GET /auth/me` - Get current user information

### Portfolio
- `GET /portfolio` - Get portfolio summary
- `POST /portfolio` - Add new position
- `GET /portfolio/{item_id}` - Get specific position
- `PATCH /portfolio/{item_id}/sell` - Mark position as sold
- `DELETE /portfolio/{item_id}` - Delete position

### Watchlist
- `GET /watchlist` - Get user watchlist
- `POST /watchlist` - Add ticker to watchlist
- `DELETE /watchlist/{ticker}` - Remove ticker from watchlist

### Stocks
- `POST /stocks/historical-data` - Get historical price data
- `POST /stocks/analysis` - Get technical analysis
- `GET /stocks/fundamentals/{ticker}` - Get fundamental data

### Alerts
- `GET /alerts` - Get user alerts
- `POST /alerts` - Create new alert
- `GET /alerts/{alert_id}` - Get specific alert
- `PATCH /alerts/{alert_id}/toggle` - Toggle alert active status
- `DELETE /alerts/{alert_id}` - Delete alert

## Environment Variables

### Backend

- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: finances_db)
- `DB_USER` - Database user (default: postgres)
- `DB_PASSWORD` - Database password (default: postgres)
- `SECRET_KEY` - Secret key for JWT tokens
- `DEBUG` - Debug mode (default: true)
- `CELERY_BROKER_URL` - Redis broker URL
- `CELERY_RESULT_BACKEND` - Redis result backend URL

### Frontend

- `VITE_API_BASE_URL` - Backend API base URL (default: http://localhost:8000)

## License

This project is private and proprietary.

