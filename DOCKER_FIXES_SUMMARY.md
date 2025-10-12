# Docker Issues Fix Summary

## 🔍 **Root Cause Analysis**

The errors you're experiencing are caused by two main issues:

### 1. **Missing ODBC Driver in Container**
```
ImportError: libodbc.so.2: cannot open shared object file: No such file or directory
```
- The Docker container doesn't have the Microsoft ODBC driver installed
- `pyodbc` requires this driver to connect to SQL Server
- This causes the 500 Server Error when trying to add connections

### 2. **Python Import Path Issues**
```
⚠️ Direct integration not available. Using API mode only.
```
- Streamlit container can't import project modules (`adapters`, `rag`, `core`)
- `PYTHONPATH` not properly set in container environment
- Falls back to API mode instead of direct integration

## ✅ **Fixes Applied**

### 1. **Updated Dockerfile**
- Added Microsoft ODBC driver installation
- Installed `msodbcsql18` and `mssql-tools18`
- Added proper Microsoft repository configuration

### 2. **Updated docker-compose.yml**
- Added `PYTHONPATH=/app` to both app and streamlit services
- Added `PYTHONUNBUFFERED=1` for better logging
- Added `VECTOR_STORE_PATH` for streamlit service

### 3. **Updated requirements.txt**
- Added `requests>=2.31.0` for API communication

## 🚀 **How to Apply the Fixes**

### Option 1: Use the PowerShell Script (Recommended)
```powershell
.\fix_docker_issues.ps1
```

### Option 2: Manual Commands
```bash
# Stop containers
docker-compose down

# Remove old images
docker-compose down --rmi all

# Rebuild with no cache
docker-compose build --no-cache

# Start containers
docker-compose up -d

# Check status
docker-compose ps
```

## 🔧 **What the Fixes Do**

1. **ODBC Driver Installation**:
   - Installs Microsoft ODBC Driver 18 for SQL Server
   - Provides `libodbc.so.2` that `pyodbc` needs
   - Enables SQL Server connections from the container

2. **Python Path Configuration**:
   - Sets `PYTHONPATH=/app` so Python can find project modules
   - Enables direct integration in Streamlit
   - Allows imports of `adapters`, `rag`, `core` modules

3. **Environment Variables**:
   - Ensures consistent environment across services
   - Proper logging configuration
   - Vector store path configuration

## 📋 **Expected Results After Fix**

### ✅ **Streamlit UI**
- No more "Direct integration not available" warning
- Can import and use `SQLServerAdapter` directly
- Puma connection should work without API calls

### ✅ **API Service**
- No more 500 errors when adding connections
- `pyodbc` can connect to SQL Server
- Connection management works properly

### ✅ **Database Connections**
- Puma SQL Server connection works
- Schema introspection functions
- NL→SQL generation available

## 🧪 **Testing the Fixes**

After applying the fixes, test:

1. **Streamlit UI**: http://localhost:8501
   - Should show no import warnings
   - Puma connection should work
   - Direct integration should be available

2. **API Health**: http://localhost:8000/health/
   - Should return 200 OK
   - No ODBC errors in logs

3. **Connection Test**:
   - Try connecting to Puma database
   - Should succeed without 500 errors

## 🔍 **Troubleshooting**

If issues persist:

1. **Check logs**:
   ```bash
   docker-compose logs -f
   ```

2. **Verify ODBC driver**:
   ```bash
   docker-compose exec app ls -la /opt/microsoft/msodbcsql18/lib64/
   ```

3. **Test Python imports**:
   ```bash
   docker-compose exec streamlit python -c "from adapters.sqlserver_adapter import SQLServerAdapter; print('Import successful')"
   ```

4. **Check environment**:
   ```bash
   docker-compose exec streamlit env | grep PYTHON
   ```

## 📝 **Notes**

- The rebuild process may take 5-10 minutes due to ODBC driver installation
- First startup might be slower as containers initialize
- All existing data will be preserved (volumes are not removed)
- The fixes are backward compatible with existing functionality
