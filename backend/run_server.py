#!/usr/bin/env python
"""
Debug script to run the backend server with detailed error reporting
"""
import sys
import traceback

try:
    print("Python path:", sys.path)
    print("Attempting to import app.main...")
    from app.main import app
    import uvicorn
    
    print("Successfully imported app.main")
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
except Exception as e:
    print("ERROR: Failed to start server")
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception message: {str(e)}")
    print("Traceback:")
    traceback.print_exc()
    
    print("\nChecking for common issues:")
    
    # Check for database connection
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        print("Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful!")
    except Exception as db_error:
        print(f"Database connection failed: {str(db_error)}")
    
    # Check for missing packages
    missing_packages = []
    for package in ["fastapi", "sqlalchemy", "uvicorn", "pydantic", "passlib", "python-jose"]:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Try installing them with: pip install " + " ".join(missing_packages))
