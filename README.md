# LLRF2025 Conference Web Scraper

**Author: Ming Liu**

## Overview
This web scraper is designed to extract all contributions, sessions, and materials from the LLRF2025 workshop (https://indico.jlab.org/event/939/). The scraper creates folders organized by type (Oral Presentations, Posters, Sessions) and date, downloading contribution information and attachment files.

## File Description
- `llrf2025_scraper.py` - Main scraper script for LLRF2025 workshop
- `extract_sessions.py` - Session extraction and organization
- `requirements.txt` - Python dependencies list
- `README_LLRF2025.md` - This documentation

## Requirements
- Python 3.7+
- Stable internet connection

## Installation

1. Ensure Python 3.7 or higher is installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run the main scraper
```bash
python llrf2025_scraper.py
```

### Extract sessions (optional)
```bash
python extract_sessions.py
```

## Output Directory Structure

```
LLRF2025_Data/
├── Oral_Presentations/          # Oral presentations organized by contribution
│   ├── 82 - Anomaly Detection in the CERN.../
│   │   ├── contribution.json    # Detailed contribution data
│   │   └── LLRF25_Anomaly_Detection.pptx
│   └── ...
├── Posters/                     # Posters organized by contribution
│   ├── 13 - Reliable operation of PAL-XFEL LLRF/
│   │   ├── contribution.json
│   │   └── LLRFWS2025_Poster.pdf
│   └── ...
├── Sessions/                    # Session information
│   ├── session_xxx.json
│   └── ...
├── By_Date/                     # Contributions organized by date
│   ├── 2025-10-13/
│   │   ├── 2025-10-13_contributions.json
│   │   └── 2025-10-13_summary.txt
│   ├── 2025-10-14/
│   ├── 2025-10-15/
│   ├── 2025-10-16/
│   ├── _contributions.json      # All dated contributions
│   └── _summary.txt            # Summary of all dates
├── Attachments/                 # Deprecated: files now stored in contribution folders
├── LLRF2025_All_Contributions.json  # Complete contributions data
├── LLRF2025_All_Contributions.csv   # CSV format for Excel
└── LLRF2025_Summary.txt            # Human-readable summary report
```

## Features

### Data Extraction
- Contribution IDs and titles
- Speaker and author information
- Primary authors and co-authors
- Affiliation details
- Contribution descriptions/abstracts
- Attachment files (presentations, papers, etc.)
- Date and time information
- Duration and session information
- Contribution type (Oral, Poster, etc.)

### File Organization
- Automatic folder creation by contribution type
- Date-based organization
- Attachments stored with their contributions
- Multiple output formats (JSON, CSV, TXT)

### Error Handling
- Network request retry mechanism
- Progress indicators
- Statistics tracking for downloads

## Configuration Options

You can modify the following configurations in the script:

```python
# Event ID
EVENT_ID = 939

# Base URL
BASE_URL = f"https://indico.jlab.org/event/{EVENT_ID}"

# Output directory
OUTPUT_DIR = "LLRF2025_Data"

# Request delay (seconds)
time.sleep(0.5)  # Between requests

# Maximum contributions to process
# Set to None for all contributions
```

## Data Format

The scraper extracts the following information for each contribution:
- **id**: Contribution ID
- **friendly_id**: Human-readable ID
- **title**: Contribution title
- **type**: Contribution type (Oral, Poster, etc.)
- **start_date**: Start date (YYYY-MM-DD)
- **start_time**: Start time (HH:MM:SS)
- **duration**: Duration in minutes
- **speakers**: List of speakers
- **primary_authors**: Primary authors
- **coauthors**: Co-authors
- **affiliations**: Author affiliations
- **description**: Abstract/description
- **attachment_count**: Number of attachments
- **url**: Contribution URL
- **session**: Session name
- **location**: Venue location
- **room**: Room name

## Important Notes

1. **Network Stability**: Ensure stable internet connection, scraping process may take some time
2. **Storage Space**: Ensure sufficient disk space for attachment files
3. **Request Frequency**: Script includes appropriate delays to avoid server overload
4. **Filename Restrictions**: Filenames are automatically sanitized for compatibility

## FAQ

### Q: What if the scraping process is interrupted?
A: Re-run the script. Already downloaded files will be skipped, only new content will be downloaded.

### Q: Some attachment downloads fail?
A: Check the console output for detailed error information. Could be network issues or access restrictions.

### Q: How to scrape only specific contribution types?
A: Modify the script to filter contributions by the 'type' field.

### Q: Why are some attachments missing?
A: Some contributions may not have attachments, or they may require authentication to access.

## Statistics (Last Run)

- Total contributions: 100
- Oral presentations: 45
- Posters: 43
- Others: 12
- Downloaded files: 40
- Errors: 0

## Technical Support

If you encounter issues, please check:
1. Python version meets requirements
2. All dependencies are correctly installed
3. Network connection is stable
4. Target website is accessible

## Disclaimer

This script is for academic research purposes only. Please comply with relevant website terms of use and copyright regulations. Users are responsible for any consequences arising from using this script.

## Version History

### v1.0 (2025-10-27)
- Initial release for LLRF2025 workshop
- Indico platform support
- Contribution-based organization
- Attachment downloads
- Date-based categorization
- Multiple output formats (JSON, CSV, TXT)
