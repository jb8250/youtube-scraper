Based on my analysis of the notebook, here's a detailed plan to fix both issues:

## Fix Plan for YouTube_Search_Scraper.ipynb

### **Issue 1: Missing `Options` Import**
**Problem**: Line 325 uses `Options()` but the import is missing from Cell 3
**Location**: Cell 3 (Import Libraries section, lines 183-207)
**Fix**: Add `from selenium.webdriver.chrome.options import Options` after line 202

### **Issue 2: No Validation to Stop Execution Without Search Term**
**Problem**: Cell 7 (Run the Scraper) executes immediately even when no search term is set
**Location**: Cell 7 (lines 947-993)
**Fix**: Add validation at the start of Cell 7 that raises `SystemExit` if search term not configured

### **Issue 3: Missing 'configured' Key**
**Problem**: SEARCH_CONFIG dictionary missing the 'configured' flag that's set by the button
**Location**: Cell 2 (lines 67-73)
**Fix**: Add `'configured': False` to SEARCH_CONFIG dictionary

## Detailed Implementation Steps:

### Step 1: Fix SEARCH_CONFIG Dictionary (Cell 2, Line 67-73)
```python
# Current:
SEARCH_CONFIG = {
    'term': '',
    'title_filter': True,
}

# Change to:
SEARCH_CONFIG = {
    'term': '',
    'title_filter': True,
    'configured': False,  # Track if user has set search term
}
```

### Step 2: Add Options Import (Cell 3, After Line 202)
```python
# Current imports end at line 203
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Add this line:
from selenium.webdriver.chrome.options import Options
```

### Step 3: Add Validation to Cell 7 (Before Line 947)
```python
# Add at the very beginning of Cell 7, before any other code:
# Check if search term has been configured
if not SEARCH_CONFIG.get('configured', False):
    print("❌ ERROR: No search term configured!")
    print("   Go back to Cell 2, enter a search term, and click 'Set Search Term'.")
    print("   Then run this cell again.")
    raise SystemExit("Execution stopped: Search term required")

if not SEARCH_CONFIG['term'].strip():
    print("❌ ERROR: Search term is empty!")
    print("   Go back to Cell 2 and enter a valid search term.")
    raise SystemExit("Execution stopped: Empty search term")

# Then continue with existing code:
# Initialize scraper and formatter
print(f"🚀 Initializing YouTube Search Scraper for '{SEARCH_CONFIG['term']}'...")
...
```

### Step 4: Update Configuration Print (Cell 4, Line 281)
```python
# Current:
print(f"📊 Will search for up to {CONFIG['max_videos']} videos matching: '{SEARCH_CONFIG['term']}'")

# Change to:
if SEARCH_CONFIG.get('configured', False) and SEARCH_CONFIG['term'].strip():
    print(f"📊 Will search for up to {CONFIG['max_videos']} videos matching: '{SEARCH_CONFIG['term']}'")
else:
    print("📊 Search term not configured yet. Set it in Cell 2 before running the scraper.")
```

## Why These Changes Fix the Issues:

1. **Options Import**: Adding the import resolves the `NameError: name 'Options' is not defined`
2. **Validation Logic**: The `SystemExit` exception will completely stop notebook execution, preventing cells from running without a search term
3. **configured Flag**: Tracks whether user has clicked the "Set Search Term" button

## Expected Behavior After Fixes:

1. User runs Cell 1 (Install Dependencies) ✅
2. User runs Cell 2 (Configure Search) - widget appears ✅
3. User enters search term and clicks button - sets `configured = True` ✅
4. User runs Cell 3 (Import Libraries) - Options import works ✅
5. User runs Cell 4 (Configuration) - shows status ✅
6. User runs Cells 5-6 (Class definitions) ✅
7. User runs Cell 7 (Run Scraper):
   - **If search term not configured**: Shows error and stops ❌
   - **If search term configured**: Runs successfully ✅

This ensures the workflow is enforced and the `Options` import error is resolved.