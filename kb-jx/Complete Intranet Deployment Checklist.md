Here is the complete English translation of the document, formatted in Markdown.

---

# kb-jx Intranet Deployment Complete Checklist

> **Generation Date:** 2025-11-13
>
> **Target Environment:** Windows Intranet Environment
>
> **Python Version:** 3.10+

---

## ✅ I. Dependency Package Check (Completed)

### 1.1 Python Offline Package Status

**Current Status**: ✅ 38 offline wheel packages packed

| Category | Package Name | Version | Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Core Framework** | fastapi | 0.104.1 | ✅ | Web Framework |
| | uvicorn | 0.24.0 | ✅ | ASGI Server |
| | starlette | 0.27.0 | ✅ | FastAPI Dependency |
| | pydantic | 2.12.4 | ✅ | Data Validation |
| | pydantic_core | 2.41.5 | ✅ | Pydantic Core |
| **Doc Processing** | python-docx | 1.1.0 | ✅ | Word Document Processing |
| | openpyxl | 3.1.2 | ✅ | Excel Processing |
| | python-pptx | 0.6.23 | ✅ | PPT Processing |
| | PyMuPDF | 1.23.8 | ✅ | PDF Processing |
| | PyMuPDFb | 1.23.7 | ✅ | PyMuPDF Binary |
| **Windows Support** | pywin32 | 311 | ✅ | Office COM Calls |
| **Deduplication** | redis | 7.0.1 | ✅ | Redis Client |
| | ftfy | 6.3.1 | ✅ | Text Normalization |
| | simhash | 2.1.2 | ✅ | Near-duplicate Detection |
| **Utilities** | aiofiles | 25.1.0 | ✅ | Async File I/O |
| | python-multipart | 0.0.6 | ✅ | File Upload |
| | lxml | 6.0.2 | ✅ | XML Processing |
| | Pillow | 12.0.0 | ✅ | Image Processing |
| | numpy | 2.2.6 | ✅ | Scientific Computing (ftfy dep) |
| **Other Deps** | python-dotenv | 1.2.1 | ✅ | Environment Variables |
| | pyyaml | 6.0.3 | ✅ | YAML Parsing |
| | click | 8.3.0 | ✅ | Command Line Tool |
| | httptools | 0.7.1 | ✅ | HTTP Parsing |
| | websockets | 15.0.1 | ✅ | WebSocket |
| | watchfiles | 1.1.1 | ✅ | File Monitoring |
| | wcwidth | 0.2.14 | ✅ | Terminal Width Calculation |
| | async_timeout | 5.0.1 | ✅ | Async Timeout |

**Total Size of Offline Packages**: Approx. 51 MB (Actual measurement: ~60 MB)

### 1.2 requirements.txt Integrity Check

**Current requirements.txt**:

```text
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-docx==1.1.0
openpyxl==3.1.2
python-pptx==0.6.23
PyMuPDF==1.23.8
aiofiles>=24.1.0
pywin32>=306; sys_platform == 'win32'
redis>=5.0.0
ftfy>=6.1.0
simhash>=2.1.0
```

⚠️ **Issue Found**: `requirements.txt` lacks indirect dependency declarations, but `offline_packages` already contains them. They will be resolved automatically during offline installation.

---

## ✅ II. LibreOffice Portable Check

### 2.1 Current Configuration

- **Path**: `D:\aigc1\kb-jx\tool\LibreOfficePortable\App\libreoffice\program\soffice.exe`
- **Status**: ✅ Built-in to the project
- **Size**: Approx. 400-600 MB (Need to confirm integrity)

### 2.2 Intranet Deployment Notes

✅ **Advantages**:
- No need to install LibreOffice on the target machine.
- The portable version can be copied and used directly.
- Path is already configured in `.env`.

⚠️ **Check Item**:

```bat
# Verify if LibreOffice is available
d:\aigc1\kb-jx\tool\LibreOfficePortable\App\libreoffice\program\soffice.exe --version
```

**Expected Output**:
```text
LibreOffice 7.x.x.x
```

### 2.3 Conversion Capabilities

| Feature | LibreOffice | pywin32 (Office COM) | Note |
| :--- | :--- | :--- | :--- |
| .doc → .docx | ✅ | ✅ | Prioritize LibreOffice |
| .xls → .xlsx | ✅ | ✅ | Prioritize LibreOffice |
| .ppt → .pptx | ✅ | ✅ | Prioritize LibreOffice |
| Cross-platform | ✅ | ❌ | LibreOffice supports Linux |
| No Office Install | ✅ | ❌ | LibreOffice is portable |

---

## ⚠️ III. Potential Issues & Solutions

### 3.1 [High Priority] Redis Dependency

**Issue Description**:
- The project relies on Redis for deduplication storage (document-level & paragraph-level).
- The intranet environment might not have a Redis service.

**Current Configuration** (`.env`):
```env
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=1
REDIS_PASSWORD=123456
REDIS_ENABLED=true
```

**Solutions**:

#### Option A: Deploy Redis (Recommended)
1. **Download Redis for Windows**:
   - GitHub: https://github.com/tporadowski/redis/releases
   - Download `Redis-x64-5.0.14.1.zip` (~5 MB)

2. **Pack into Project**:
   ```text
   kb-jx/
     tool/
       redis/
         redis-server.exe
         redis-cli.exe
         redis.windows.conf
   ```

3. **Startup Script** (Create `start_redis.bat`):
   ```bat
   @echo off
   cd /d %~dp0tool\redis
   start redis-server.exe redis.windows.conf
   echo Redis started on port 6379
   ```

#### Option B: Use Memory Mode (Implemented)
- The project supports automatically switching to memory mode when Redis is unavailable.
- Memory fallback is implemented in `utils/dedup_store.py`.
- **Limitation**: Deduplication records are lost after service restart.

**Configuration**:
```env
REDIS_ENABLED=false  # Disable Redis
```

#### Option C: Integrate Redis Python Server (Not Recommended)
- Use `fakeredis` library to simulate Redis.
- Requires packaging extra `fakeredis` dependencies.

**Recommendation**:
- **Production Environment**: Use Option A (Independent Redis Service).
- **Demo/Test**: Use Option B (Memory Mode).

---

### 3.2 [Medium Priority] Microsoft Office Dependency

**Issue Description**:
- `pywin32` requires Microsoft Office to be installed on the system to handle `.doc/.xls/.ppt`.
- Intranet machines might not have Office installed.

**Current Strategy**:
```python
# Fallback logic in converter.py
CONVERSION_BACKEND=auto  # Prioritize LibreOffice, failover to Office COM
```

**Solutions**:

#### ✅ Resolved (Using LibreOffice)
- The project includes LibreOffice Portable.
- Configured to `auto` mode, prioritizing LibreOffice.
- Can handle legacy formats even without Office installed.

**Verification Method**:
```python
# Test if legacy format conversion works
python -c "from services.converter import DocumentConverter; c = DocumentConverter(); print(c.libreoffice_path)"
```

**Expected Output**:
```text
D:\aigc1\kb-jx\tool\LibreOfficePortable\App\libreoffice\program\soffice.exe
```

---

### 3.3 [Low Priority] PyMuPDF Dependency

**Issue Description**:
- PyMuPDF is used for PDF text extraction.
- Depends on the `PyMuPDFb` binary package (~24 MB).

**Current Status**: ✅ Packed into `offline_packages`.

**Verification Method**:
```python
python -c "import fitz; print('PyMuPDF Version:', fitz.version)"
```

**Impact if Missing**:
- PDF files cannot be processed.
- System will return an "Unsupported format" error.

---

### 3.4 [Medium Priority] Chinese Paths & Encoding

**Potential Issues**:
1. LibreOffice command line might not support Chinese paths.
2. Windows system encoding might cause garbled filenames.

**Implemented Protection**:
- Use temporary directory `storage/temp` + UUID filenames.
- Rename back to original filename after conversion.
- File processing uses UTF-8 encoding.

**Suggestion**:
```python
# Ensure temp directory config in config.py
TEMP_DIR = "storage/temp"  # Avoid using Chinese paths
```

---

### 3.5 [High Priority] Firewall & Port Issues

**Issue Description**:
- Default port `8000` might be blocked by the firewall.
- Intranet might have port whitelist restrictions.

**Solutions**:

#### Check Port Usage
```bat
netstat -ano | findstr :8000
```

#### Modify Port (If needed)
Edit `main.py`:
```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8080,  # Change to allowed port
    log_level="info"
)
```
Or use environment variable:
```env
APP_PORT=8080
```

#### Firewall Rules (Admin Privileges)
```bat
# Allow inbound connection
netsh advfirewall firewall add rule name="kb-jx-service" dir=in action=allow protocol=TCP localport=8000
```

---

### 3.6 [Medium Priority] Disk Space Issues

**Space Estimation**:

| Item | Size | Note |
| :--- | :--- | :--- |
| Project Code | ~5 MB | Python Source |
| Offline Packages | ~60 MB | Wheel Files |
| LibreOffice Portable | ~500 MB | Full Package |
| Redis (Optional) | ~5 MB | Windows Version |
| **Total After Install** | **~570 MB** | |
| Runtime Temp Files | Dynamic | Depends on load |
| Log Files | Dynamic | ~10-50 MB/day |

**Storage Cleanup Strategy**:
```python
# config.py
STORAGE_CLEAN_KEEP_DAYS=7  # Keep task files for 7 days
```

**Manual Cleanup**:
```bat
# Clean files older than 7 days
clean_storage.bat
# Or manually execute
python clean_task.py --days 7
```

---

### 3.7 [Low Priority] Python Version Compatibility

**Requirement**: Python 3.10+

**Check Method**:
```bat
python --version
```

**If Version is Too Low**:
- Some type annotation syntax might be incompatible (e.g., `|` operator).
- `pydantic` 2.x requires Python 3.7+.
- Recommendation: Unify on Python 3.10 or 3.11.

**Packaging Suggestion**:
- Consider using Python embeddable package.
- Download: https://www.python.org/downloads/windows/
- Unzip and use, no installation required.

---

### 3.8 [Medium Priority] Temporary File Cleanup Mechanism

**Current Implementation**:
```python
# main.py - Auto-clean temp files older than 1 hour on startup
@app.on_event("startup")
async def startup_clean():
    # Clean temp directory
    deleted_count = 0
    for temp_file in temp_dir.glob("*"):
        if temp_file.is_file():
            file_age = current_time - temp_file.stat().st_mtime
            if file_age > 3600:  # 1 Hour
                temp_file.unlink()
                deleted_count += 1
```

**Potential Issue**:
- Long-running conversion tasks might be deleted by mistake.
- Suggest adding a file lock mechanism.

**Optimization Suggestion**:
```python
# Increase safety window
TEMP_FILE_MAX_AGE = 3600 * 24  # 24 Hours
```

---

### 3.9 [Low Priority] Frontend Static File Access

**Current Configuration**:
```python
# main.py
app.mount("/static", StaticFiles(directory="static"), name="static")
```

**Potential Issue**:
- If `static/upload.html` contains external CDN references (e.g., jQuery, Bootstrap).
- Intranet might not be able to access public CDNs.

**Check File**: `static/upload.html`

**Solution**:
- Download CDN resources to local.
- Or confirm that the intranet can access public CDNs.

---

### 3.10 [High Priority] Count Inconsistency Issue (Fixed)

**Issue Description**:
- Frontend display of "Pure Text Cleaned Package + Rich Media Document Package" count did not match the total count.
- Cause: Total count included duplicates, temp lock files, unsupported formats, etc.

**Fixed**:
- Frontend changed to display `pureCount + richCount` as the downloadable total.
- Unique files are fetched from `data.progress.unique_pure_count/unique_rich_count`.

**Verification Method**:
- Upload 32 files (including duplicates, temp lock files).
- Check if the count in the download area is correct.

---

## ✅ IV. Pre-Deployment Checklist

### 4.1 File Integrity Check

```bat
@echo off
echo Checking project file integrity...
REM Core Files
if not exist "main.py" echo [Missing] main.py
if not exist "config.py" echo [Missing] config.py
if not exist "requirements.txt" echo [Missing] requirements.txt
if not exist ".env" echo [Missing] .env

REM API Modules
if not exist "api\v1\endpoints.py" echo [Missing] api\v1\endpoints.py

REM Service Modules
if not exist "services\converter.py" echo [Missing] services\converter.py
if not exist "services\detector.py" echo [Missing] services\detector.py
if not exist "services\text_pipeline.py" echo [Missing] services\text_pipeline.py
if not exist "services\zipper.py" echo [Missing] services\zipper.py

REM Utility Modules
if not exist "utils\logger.py" echo [Missing] utils\logger.py
if not exist "utils\dedup_store.py" echo [Missing] utils\dedup_store.py
if not exist "utils\file_handler.py" echo [Missing] utils\file_handler.py

REM Offline Packages
if not exist "offline_packages" echo [Missing] offline_packages directory
if not exist "tool\LibreOfficePortable" echo [Missing] LibreOffice Portable

echo Check complete!
```

### 4.2 Dependency Package Integrity Check

```bat
# Check number of offline packages
dir /b offline_packages\*.whl | find /c /v ""
```
**Expected**: 38 files

### 4.3 Environment Variable Check

```bat
# Print current config
python config.py
```
**Expected Output**: Display all config items without errors.

---

## ✅ V. Standard Deployment Process

### 5.1 Copy Files to Target Machine
```text
Copy the entire kb-jx directory to the target server (e.g., D:\deploy\kb-jx)
```

### 5.2 Install Python Dependencies

```bat
# Method A: Automatic Installation (Recommended)
Double-click: install_offline.bat

# Method B: Manual Installation
cd D:\deploy\kb-jx
python -m pip install --upgrade pip --no-index --find-links=offline_packages
pip install --no-index --find-links=offline_packages -r requirements.txt
```

### 5.3 Verify Installation

```bat
Double-click: verify_install.bat
```

**Expected Output**:
```text
[OK] Python environment normal
[OK] Core dependencies installed
[OK] Document processing libraries installed
[OK] Office COM available (or prompt unavailable, but LibreOffice present)
[OK] Key files complete
```

### 5.4 Configure Environment Variables (Optional)

Edit `.env`:
```env
# Redis Config (If no Redis service, set to false)
REDIS_ENABLED=false

# Port Config (If modification needed)
APP_PORT=8000

# LibreOffice Path (Verify correctness)
LIBREOFFICE_PATH=D:\deploy\kb-jx\tool\LibreOfficePortable\App\libreoffice\program\soffice.exe
```

### 5.5 Start Service

```bat
# Method A: Use Startup Script
Double-click: start.bat

# Method B: Manual Start
python main.py
```

### 5.6 Access Test

Open Browser:
- http://localhost:8000 - Home
- http://localhost:8000/upload - Upload Page
- http://localhost:8000/docs - API Docs
- http://localhost:8000/health - Health Check

---

## ✅ VI. Testing & Verification Plan

### 6.1 Functional Test List

| Test Item | Test File | Expected Result | Status |
| :--- | :--- | :--- | :--- |
| Pure Text Upload | test.txt | Convert to docx | ⬜ |
| Word New Format | test.docx | Clean & Dedup | ⬜ |
| Word Old Format | test.doc | Convert to docx | ⬜ |
| Excel New Format | test.xlsx | Identify Rich Media | ⬜ |
| Excel Old Format | test.xls | Convert to xlsx | ⬜ |
| PPT New Format | test.pptx | Identify Rich Media | ⬜ |
| PPT Old Format | test.ppt | Convert to pptx | ⬜ |
| PDF File | test.pdf | Extract Text | ⬜ |
| Batch Upload | 32 Mixed Files | Correct Classification | ⬜ |
| Dedup Feature | 3 Identical Files | Keep only 1 | ⬜ |
| Unique Copy Gen | Mixed Files | ZIP Correct | ⬜ |
| Temp Lock File | ~$test.docx | Auto Skip | ⬜ |

### 6.2 Performance Test

```python
# Run performance test
python test_api.py
```

### 6.3 Deduplication System Test

```python
# Test deduplication mechanism
python test_dedup_system.py
```

---

## ✅ VII. Packing List (Intranet Package)

### 7.1 Required Files

```text
kb-jx/
├── api/                         # API Modules
├── models/                      # Data Models
├── services/                    # Business Services
├── utils/                       # Utility Classes
├── static/                      # Static Files
│   └── upload.html
├── tool/                        # Tools & Software
│   ├── LibreOfficePortable/     # ✅ Required (500 MB)
│   └── redis/                   # ⚠️ Optional (5 MB)
├── offline_packages/            # ✅ Required (60 MB)
│   └── *.whl (38 files)
├── main.py                      # ✅ Main Program
├── config.py                    # ✅ Configuration
├── requirements.txt             # ✅ Dependency List
├── .env                         # ✅ Env Variables
├── install_offline.bat          # ✅ Install Script
├── verify_install.bat           # ✅ Verify Script
├── start.bat                    # ✅ Start Script
├── clean_storage.bat            # ⚠️ Optional
├── README_OFFLINE.txt           # ⚠️ Optional
└── DEPLOY_CHECKLIST.txt         # ⚠️ Optional
```

### 7.2 Optional Components

```text
kb-jx/
├── tool/redis/                  # Redis Service (If persistence needed)
│   ├── redis-server.exe
│   ├── redis-cli.exe
│   └── redis.windows.conf
├── logs/                        # Logs Directory (Auto-created at runtime)
├── storage/                     # Storage Directory (Auto-created at runtime)
└── test_files/                  # Test Files (Optional)
```

### 7.3 Packaging Command (If Repacking Needed)

```bat
# Use existing packing script
create_package.bat

# Or manual packing
pip download -r requirements.txt -d offline_packages --only-binary :all: --platform win_amd64 --python-version 310
```

---

## ⚠️ VIII. Common Deployment Issues & Troubleshooting

### 8.1 Service Start Failure
**Symptom**: Running `python main.py` errors out.
**Troubleshooting**:
1. Check Python version: `python --version` (Must be 3.10+).
2. Check dependencies: `pip list | findstr fastapi`.
3. Check port usage: `netstat -ano | findstr :8000`.
4. Check logs: `logs/app_*.log`.

### 8.2 File Conversion Failure
**Symptom**: "Conversion Failed" displayed after uploading.
**Troubleshooting**:
1. Check LibreOffice:
   ```bat
   tool\LibreOfficePortable\App\libreoffice\program\soffice.exe --version
   ```
2. Check file permissions: Ensure `storage/temp` is writable.
3. Check conversion logs: Look for "converter" related logs in `logs/app_*.log`.

### 8.3 Redis Connection Failure
**Symptom**: "WARNING: Redis connection failed" in logs.
**Solution**:
- Confirm Redis service is running: `netstat -ano | findstr :6379`.
- Or disable Redis: Set `REDIS_ENABLED=false` in `.env`.
- Check password: Verify `REDIS_PASSWORD` in `.env`.

### 8.4 Frontend Page Inaccessible
**Symptom**: Browser accessing http://localhost:8000 gives no response.
**Troubleshooting**:
1. Confirm service started: Console shows "Uvicorn running on http://0.0.0.0:8000".
2. Check firewall: Temporarily disable firewall to test.
3. Try 127.0.0.1: http://127.0.0.1:8000.
4. Check Local IP: `ipconfig`, try http://LocalIP:8000.

### 8.5 Garbled Chinese Filenames
**Symptom**: Filenames inside downloaded ZIP are garbled.
**Solution**:
- Confirm System Encoding: Control Panel -> Region -> Administrative -> Change system locale -> Check "Beta: Use Unicode UTF-8 for worldwide language support".
- Or enforce UTF-8 in code (Already implemented).

---

## ✅ IX. Production Optimization Suggestions

### 9.1 Performance Optimization
```python
# config.py - Adjust concurrency
MAX_CONCURRENT_TASKS=10  # Adjust based on CPU cores (Suggested: Cores x 2)

# Conversion Timeout
CONVERSION_TIMEOUT=120  # Large files may need more time
```

### 9.2 Security Hardening
```python
# Limit upload file size
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Limit concurrent connections (Uvicorn params)
uvicorn.run(app, workers=4, limit_concurrency=100)
```

### 9.3 Monitoring & Logging
```python
# config.py - Log Level
LOG_LEVEL=WARNING  # Reduce log volume in production

# Log Rotation
MAX_BYTES = 50 * 1024 * 1024  # 50 MB
BACKUP_COUNT = 10  # Keep 10 backups
```

### 9.4 Scheduled Cleanup Task
**Windows Task Scheduler**:
```bat
# Clean files older than 7 days every day at 2:00 AM
schtasks /create /tn "kb-jx-storage-clean" /tr "D:\deploy\kb-jx\clean_storage.bat" /sc daily /st 02:00
```

---

## ✅ X. Upgrade & Maintenance

### 10.1 Dependency Upgrade
```bat
# Re-download latest dependencies (Requires Internet)
pip download -r requirements.txt -d offline_packages_new --only-binary :all: --platform win_amd64 --python-version 310

# Compare new and old packages
dir /b offline_packages > old.txt
dir /b offline_packages_new > new.txt
fc old.txt new.txt
```

### 10.2 Data Backup
**Regular Backup**:
- `storage/batch/` - Task data (Keep as needed).
- `logs/` - Log files (Archive as needed).
- Redis Data (If enabled): `redis-cli save`.

### 10.3 Version Control
Suggest using Git to manage code, but ignore:
```gitignore
storage/
logs/
offline_packages/
tool/LibreOfficePortable/
.env
```

---

## ✅ XI. Emergency Handling

### 11.1 Service Auto-Restart
**Windows Service Wrapping** (Using NSSM):
```bat
# Download NSSM: https://nssm.cc/download
nssm install kb-jx "D:\deploy\kb-jx\start.bat"
nssm set kb-jx AppDirectory "D:\deploy\kb-jx"
nssm start kb-jx
```

### 11.2 Data Recovery
**Recover Deduplication Records**:
```bat
# If Redis data is lost, records will rebuild automatically when reprocessing tasks.
# Or recover from backup Redis dump.rdb.
```

### 11.3 Rollback Operation
```bat
# Keep code backup
xcopy /E /I kb-jx kb-jx_backup_20251113

# If rollback is needed
rd /S /Q kb-jx
ren kb-jx_backup_20251113 kb-jx
```

---

## ✅ XII. Final Checklist (Pre-Deployment)

- [ ] Python 3.10+ installed.
- [ ] All offline packages copied (38 wheel files).
- [ ] LibreOffice Portable copied (~500 MB).
- [ ] `.env` file configured (Especially LIBREOFFICE_PATH).
- [ ] Redis service deployed or disabled (REDIS_ENABLED=false).
- [ ] Ran `install_offline.bat` successfully.
- [ ] Ran `verify_install.bat` without errors.
- [ ] Ran `python main.py` service started normally.
- [ ] Browser access http://localhost:8000 works.
- [ ] Test file upload function works.
- [ ] Download ZIP package function works.
- [ ] Firewall rules added (If external access needed).
- [ ] Scheduled cleanup task set (Optional).
- [ ] Backup strategy defined (Optional).

---

## 📞 Technical Support

**System Info**:
- Version: 1.0.0
- Python: 3.10+
- Platform: Windows
- Dependencies: 38 packages
- Total Size: ~570 MB

**Key Contact**: [To be filled]
**Deployment Date**: [To be filled]
**Intranet Address**: [To be filled]

---

**Document Version**: v1.0
**Last Updated**: 2025-11-13
