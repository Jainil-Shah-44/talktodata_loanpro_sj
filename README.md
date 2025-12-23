# TalkToData LoanPro

Loan Portfolio Validation and Analysis System

## Architecture

- **Backend**: FastAPI with PostgreSQL
- **Frontend**: Next.js with Mantine UI
- **Database**: PostgreSQL with SQLAlchemy ORM

## Key Features

1. Data Upload and Processing
2. Validation Rules Engine
3. Dynamic Summary Generation
4. Interactive Dashboard

## Database Schema

- Users: Authentication and authorization
- Datasets: Uploaded loan portfolio files
- Loan Records: Individual loan details
- Validation Results: Validation run outcomes
- Summary Configs: User-defined bucket configurations

## Development Setup

1. Set up PostgreSQL database
2. Configure environment variables
3. Run backend: `uvicorn app.main:app --reload`
4. Run frontend: `npm run dev`