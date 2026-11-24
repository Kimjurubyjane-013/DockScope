# Developer Guide & Workflow

## Local Development Environment

You can run DockScope either natively on your workstation or inside Docker Compose.

### Backend Development

1. Create a Python virtual environment:
   ```bash
   python -m venv backend/venv
   source backend/venv/bin/activate  # On Windows: & backend/venv/Scripts/Activate.ps1
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run the development API server:
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Run tests:
   ```bash
   pytest backend/tests -v
   ```

### Frontend Development

1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```

3. Type-checking & tests:
   ```bash
   npm run type-check
   npm run test:unit
   ```

4. Build production distribution:
   ```bash
   npm run build
   ```
