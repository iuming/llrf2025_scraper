#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLRF2025 Conference Web Scraper

Author: Ming Liu
Date: October 27, 2025
Description: A comprehensive web scraper for LLRF2025 conference contributions and presentations.
             Extracts contribution information from Indico platform, downloads attachments, and exports
             data in multiple formats (JSON, CSV, TXT).

Website: https://indico.jlab.org/event/939/
Features:
- Contribution-based data extraction via Indico API
- Attachment download (presentations, papers, etc.)
- Multi-format data export
- Robust error handling and retry mechanisms
- Comprehensive logging
"""

import requests
from bs4 import BeautifulSoup
import os
import json
import time
import re
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
from datetime import datetime

class LLRF2025Scraper:
    """
    Web scraper for LLRF2025 conference using Indico API.
    
    This scraper extracts contribution information from the LLRF2025 conference website,
    organizing data by sessions and downloading available attachments.
    """
    
    def __init__(self, event_id: str = "939", base_url: str = "https://indico.jlab.org", output_dir: str = "LLRF2025_Data"):
        """
        Initialize the LLRF2025 scraper.
        
        Args:
            event_id: Indico event ID
            base_url: Base URL of the Indico server
            output_dir: Directory to store scraped data and files
        """
        self.event_id = event_id
        self.base_url = base_url
        self.api_url = f"{base_url}/export/event/{event_id}.json?detail=contributions"
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('llrf2025_scraper.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize directories and statistics
        self.create_directories()
        self.stats = {
            'total_contributions': 0,
            'oral_presentations': 0,
            'posters': 0,
            'downloaded_files': 0,
            'errors': 0,
            'sessions_processed': 0
        }
        
        # Event data
        self.event_data = None
        self.contributions = []
    
    def create_directories(self):
        """Create necessary directory structure for output files."""
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "Attachments").mkdir(exist_ok=True)
        (self.output_dir / "Oral_Presentations").mkdir(exist_ok=True)
        (self.output_dir / "Posters").mkdir(exist_ok=True)
        (self.output_dir / "Sessions").mkdir(exist_ok=True)
        (self.output_dir / "By_Date").mkdir(exist_ok=True)
        self.logger.info(f"Created output directory: {self.output_dir}")
    
    def safe_filename(self, filename: str, max_length: int = 180) -> str:
        """
        Convert filename to safe filesystem name.
        
        Args:
            filename: Original filename
            max_length: Maximum allowed filename length
            
        Returns:
            Safe filename string
        """
        if not filename:
            return "unknown"
        
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*\r\n]', '_', filename)
        filename = re.sub(r'\s+', ' ', filename)
        filename = filename.strip(' ._')
        
        # Truncate if too long
        if len(filename) > max_length:
            filename = filename[:max_length].rsplit(' ', 1)[0]
        
        return filename or "unknown"
    
    def fetch_event_data(self) -> bool:
        """
        Fetch event data from Indico API.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Fetching event data from: {self.api_url}")
            response = self.session.get(self.api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('count', 0) > 0 and 'results' in data:
                self.event_data = data['results'][0]
                self.contributions = self.event_data.get('contributions', [])
                
                self.logger.info(f"Successfully fetched event data")
                self.logger.info(f"Event: {self.event_data.get('title', 'Unknown')}")
                self.logger.info(f"Total contributions: {len(self.contributions)}")
                
                return True
            else:
                self.logger.error("No event data found in API response")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to fetch event data: {e}")
            self.stats['errors'] += 1
            return False
    
    def parse_contribution(self, contrib: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single contribution from API data.
        
        Args:
            contrib: Raw contribution data from API
            
        Returns:
            Parsed contribution dictionary
        """
        # Extract basic information
        start_date_obj = contrib.get('startDate') or {}
        end_date_obj = contrib.get('endDate') or {}
        
        contribution_info = {
            'id': contrib.get('id', ''),
            'db_id': contrib.get('db_id', ''),
            'friendly_id': contrib.get('friendly_id', ''),
            'title': contrib.get('title', ''),
            'type': contrib.get('type', ''),
            'description': contrib.get('description', ''),
            'start_date': start_date_obj.get('date', ''),
            'start_time': start_date_obj.get('time', ''),
            'end_date': end_date_obj.get('date', ''),
            'end_time': end_date_obj.get('time', ''),
            'duration': contrib.get('duration', 0),
            'location': contrib.get('location', ''),
            'room': contrib.get('room', ''),
            'url': contrib.get('url', ''),
            'session': str(contrib.get('session', '')) if contrib.get('session') else '',
            'track': str(contrib.get('track', '')) if contrib.get('track') else '',
            'board_number': contrib.get('board_number', ''),
            'code': contrib.get('code', ''),
        }
        
        # Extract speakers
        speakers = []
        for speaker in contrib.get('speakers', []):
            speakers.append({
                'name': speaker.get('fullName', ''),
                'first_name': speaker.get('first_name', ''),
                'last_name': speaker.get('last_name', ''),
                'affiliation': speaker.get('affiliation', ''),
                'id': speaker.get('id', '')
            })
        contribution_info['speakers'] = speakers
        
        # Extract primary authors
        primary_authors = []
        for author in contrib.get('primaryauthors', []):
            primary_authors.append({
                'name': author.get('fullName', ''),
                'first_name': author.get('first_name', ''),
                'last_name': author.get('last_name', ''),
                'affiliation': author.get('affiliation', ''),
                'id': author.get('id', '')
            })
        contribution_info['primary_authors'] = primary_authors
        
        # Extract co-authors
        coauthors = []
        for author in contrib.get('coauthors', []):
            coauthors.append({
                'name': author.get('fullName', ''),
                'first_name': author.get('first_name', ''),
                'last_name': author.get('last_name', ''),
                'affiliation': author.get('affiliation', ''),
                'id': author.get('id', '')
            })
        contribution_info['coauthors'] = coauthors
        
        # Extract attachments
        attachments = []
        for folder in contrib.get('folders', []):
            for attachment in folder.get('attachments', []):
                attachments.append({
                    'id': attachment.get('id', ''),
                    'title': attachment.get('title', ''),
                    'filename': attachment.get('filename', ''),
                    'download_url': attachment.get('download_url', ''),
                    'content_type': attachment.get('content_type', ''),
                    'size': attachment.get('size', 0),
                    'modified_dt': attachment.get('modified_dt', ''),
                    'is_protected': attachment.get('is_protected', False)
                })
        contribution_info['attachments'] = attachments
        contribution_info['attachment_count'] = len(attachments)
        
        # Keywords
        contribution_info['keywords'] = contrib.get('keywords', [])
        
        return contribution_info
    
    def download_attachment(self, attachment: Dict[str, Any], contrib_info: Dict[str, Any], category_folder: str) -> bool:
        """
        Download a single attachment file.
        
        Args:
            attachment: Attachment information dictionary
            contrib_info: Contribution information dictionary
            category_folder: Category folder name (e.g., "Oral_Presentations")
            
        Returns:
            True if download successful
        """
        try:
            download_url = attachment['download_url']
            
            # Create contribution folder
            contrib_id = contrib_info.get('friendly_id', contrib_info.get('id', 'unknown'))
            safe_title = self.safe_filename(contrib_info['title'])
            folder_name = f"{contrib_id} - {safe_title}"
            
            target_dir = self.output_dir / category_folder / folder_name
            target_dir.mkdir(exist_ok=True, parents=True)
            
            # Get filename
            original_filename = attachment.get('filename', attachment.get('title', 'attachment'))
            safe_name = self.safe_filename(original_filename)
            
            filepath = target_dir / safe_name
            
            if filepath.exists():
                self.logger.info(f"File already exists, skipping: {safe_name}")
                return True
            
            # Download file
            self.logger.info(f"Downloading: {safe_name}")
            response = self.session.get(download_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = filepath.stat().st_size
            self.logger.info(f"✅ Downloaded: {safe_name} ({file_size} bytes)")
            self.stats['downloaded_files'] += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download {attachment.get('filename', 'attachment')}: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_contributions(self):
        """Process all contributions and download attachments."""
        self.logger.info(f"\nProcessing {len(self.contributions)} contributions...")
        
        # Group contributions by type
        oral_contributions = []
        poster_contributions = []
        other_contributions = []
        
        try:
            for contrib in self.contributions:
                parsed = self.parse_contribution(contrib)
                
                contrib_type = (parsed.get('type') or '').lower()
                if 'oral' in contrib_type or 'talk' in contrib_type:
                    oral_contributions.append(parsed)
                    self.stats['oral_presentations'] += 1
                elif 'poster' in contrib_type:
                    poster_contributions.append(parsed)
                    self.stats['posters'] += 1
                else:
                    other_contributions.append(parsed)
                
                self.stats['total_contributions'] += 1
        except Exception as e:
            self.logger.error(f"Error parsing contributions: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        self.logger.info(f"Oral presentations: {len(oral_contributions)}")
        self.logger.info(f"Posters: {len(poster_contributions)}")
        self.logger.info(f"Others: {len(other_contributions)}")
        
        # Process each category
        self._process_contribution_list(oral_contributions, "Oral_Presentations")
        self._process_contribution_list(poster_contributions, "Posters")
        self._process_contribution_list(other_contributions, "Attachments")
        
        # Save all contributions data
        self.save_all_contributions_data(oral_contributions, poster_contributions, other_contributions)
        
        # Group by date
        self.save_by_date(oral_contributions + poster_contributions + other_contributions)
    
    def _process_contribution_list(self, contributions: List[Dict[str, Any]], category_folder: str):
        """Process a list of contributions and download their attachments."""
        self.logger.info(f"\nProcessing {len(contributions)} contributions in {category_folder}...")
        
        for i, contrib in enumerate(contributions, 1):
            contrib_id = contrib.get('friendly_id', contrib.get('id', 'unknown'))
            title = contrib['title'][:60] + '...' if len(contrib['title']) > 60 else contrib['title']
            
            self.logger.info(f"  [{i}/{len(contributions)}] {contrib_id}: {title}")
            
            # Download attachments
            for attachment in contrib.get('attachments', []):
                self.download_attachment(attachment, contrib, category_folder)
                time.sleep(0.5)  # Avoid too frequent requests
    
    def save_all_contributions_data(self, oral: List[Dict], posters: List[Dict], others: List[Dict]):
        """Save all contributions data in various formats."""
        all_contributions = oral + posters + others
        
        # JSON format
        json_file = self.output_dir / "LLRF2025_All_Contributions.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'event_info': {
                    'title': self.event_data.get('title', ''),
                    'id': self.event_data.get('id', ''),
                    'start_date': self.event_data.get('startDate', {}),
                    'end_date': self.event_data.get('endDate', {}),
                    'location': self.event_data.get('location', ''),
                    'url': self.event_data.get('url', ''),
                },
                'statistics': {
                    'total_contributions': len(all_contributions),
                    'oral_presentations': len(oral),
                    'posters': len(posters),
                    'others': len(others)
                },
                'contributions': {
                    'oral_presentations': oral,
                    'posters': posters,
                    'others': others
                },
                'scrape_time': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved JSON data: {json_file}")
        
        # CSV format
        self.save_contributions_csv(all_contributions)
        
        # Text summary
        self.save_text_summary(oral, posters, others)
    
    def save_contributions_csv(self, contributions: List[Dict[str, Any]]):
        """Save contributions in CSV format."""
        import csv
        
        csv_file = self.output_dir / "LLRF2025_All_Contributions.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = [
                'id', 'friendly_id', 'title', 'type', 'start_date', 'start_time',
                'duration', 'speakers', 'primary_authors', 'coauthors', 'affiliations',
                'description', 'attachment_count', 'url', 'session', 'location', 'room'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for contrib in contributions:
                # Format speakers
                speakers = '; '.join([s['name'] for s in contrib.get('speakers', [])])
                primary_authors = '; '.join([a['name'] for a in contrib.get('primary_authors', [])])
                coauthors = '; '.join([a['name'] for a in contrib.get('coauthors', [])])
                
                # Get all affiliations
                all_affiliations = set()
                for person_list in [contrib.get('speakers', []), contrib.get('primary_authors', []), contrib.get('coauthors', [])]:
                    for person in person_list:
                        if person.get('affiliation'):
                            all_affiliations.add(person['affiliation'])
                
                row = {
                    'id': contrib.get('id', ''),
                    'friendly_id': contrib.get('friendly_id', ''),
                    'title': contrib.get('title', ''),
                    'type': contrib.get('type', ''),
                    'start_date': contrib.get('start_date', ''),
                    'start_time': contrib.get('start_time', ''),
                    'duration': contrib.get('duration', ''),
                    'speakers': speakers,
                    'primary_authors': primary_authors,
                    'coauthors': coauthors,
                    'affiliations': '; '.join(sorted(all_affiliations)),
                    'description': contrib.get('description', '')[:500],  # Truncate long descriptions
                    'attachment_count': contrib.get('attachment_count', 0),
                    'url': contrib.get('url', ''),
                    'session': contrib.get('session', ''),
                    'location': contrib.get('location', ''),
                    'room': contrib.get('room', '')
                }
                writer.writerow(row)
        
        self.logger.info(f"Saved CSV data: {csv_file}")
    
    def save_text_summary(self, oral: List[Dict], posters: List[Dict], others: List[Dict]):
        """Save text summary report."""
        txt_file = self.output_dir / "LLRF2025_Summary.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("LLRF2025 Conference Complete Scraping Report\n")
            f.write("=" * 80 + "\n")
            f.write(f"Event: {self.event_data.get('title', '')}\n")
            f.write(f"Event ID: {self.event_data.get('id', '')}\n")
            f.write(f"URL: {self.event_data.get('url', '')}\n")
            f.write(f"Scrape time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Statistics:\n")
            f.write(f"  Total contributions: {len(oral) + len(posters) + len(others)}\n")
            f.write(f"  Oral presentations: {len(oral)}\n")
            f.write(f"  Posters: {len(posters)}\n")
            f.write(f"  Others: {len(others)}\n")
            f.write(f"  Downloaded files: {self.stats['downloaded_files']}\n")
            f.write(f"  Errors: {self.stats['errors']}\n")
            f.write("=" * 80 + "\n\n")
            
            # Oral presentations
            if oral:
                f.write("ORAL PRESENTATIONS\n")
                f.write("-" * 80 + "\n")
                for i, contrib in enumerate(oral, 1):
                    self._write_contribution_summary(f, contrib, i)
                f.write("\n")
            
            # Posters
            if posters:
                f.write("POSTERS\n")
                f.write("-" * 80 + "\n")
                for i, contrib in enumerate(posters, 1):
                    self._write_contribution_summary(f, contrib, i)
                f.write("\n")
            
            # Others
            if others:
                f.write("OTHER CONTRIBUTIONS\n")
                f.write("-" * 80 + "\n")
                for i, contrib in enumerate(others, 1):
                    self._write_contribution_summary(f, contrib, i)
        
        self.logger.info(f"Saved text summary: {txt_file}")
    
    def _write_contribution_summary(self, f, contrib: Dict[str, Any], index: int):
        """Write a single contribution summary to file."""
        f.write(f"{index}. [{contrib.get('friendly_id', contrib.get('id', 'N/A'))}] {contrib['title']}\n")
        f.write(f"   Type: {contrib.get('type', 'N/A')}\n")
        f.write(f"   Date/Time: {contrib.get('start_date', '')} {contrib.get('start_time', '')} ({contrib.get('duration', 0)} min)\n")
        
        if contrib.get('speakers'):
            speakers = ', '.join([s['name'] for s in contrib['speakers']])
            f.write(f"   Speakers: {speakers}\n")
        
        if contrib.get('primary_authors'):
            authors = ', '.join([a['name'] for a in contrib['primary_authors']])
            f.write(f"   Primary Authors: {authors}\n")
        
        if contrib.get('coauthors'):
            coauthors = ', '.join([a['name'] for a in contrib['coauthors']])
            f.write(f"   Co-authors: {coauthors}\n")
        
        if contrib.get('attachments'):
            f.write(f"   Attachments ({len(contrib['attachments'])}):\n")
            for att in contrib['attachments']:
                f.write(f"     - {att['filename']} ({att.get('size', 0)} bytes)\n")
        
        f.write(f"   URL: {contrib.get('url', '')}\n")
        
        if contrib.get('description'):
            desc = contrib['description'][:200] + '...' if len(contrib['description']) > 200 else contrib['description']
            f.write(f"   Description: {desc}\n")
        
        f.write("\n")
    
    def save_by_date(self, contributions: List[Dict[str, Any]]):
        """Group and save contributions by date."""
        self.logger.info("\nGrouping contributions by date...")
        
        # Group by date
        by_date = {}
        for contrib in contributions:
            date = contrib.get('start_date', 'Unknown')
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(contrib)
        
        # Save each date
        for date, date_contribs in sorted(by_date.items()):
            date_str = date.replace('/', '-')
            date_dir = self.output_dir / "By_Date" / date_str
            date_dir.mkdir(exist_ok=True, parents=True)
            
            # JSON
            json_file = date_dir / f"{date_str}_contributions.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'date': date,
                    'count': len(date_contribs),
                    'contributions': date_contribs
                }, f, ensure_ascii=False, indent=2)
            
            # Text summary
            txt_file = date_dir / f"{date_str}_summary.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"LLRF2025 - Contributions on {date}\n")
                f.write("=" * 80 + "\n")
                f.write(f"Total contributions: {len(date_contribs)}\n\n")
                
                for i, contrib in enumerate(date_contribs, 1):
                    self._write_contribution_summary(f, contrib, i)
            
            self.logger.info(f"  {date}: {len(date_contribs)} contributions")
    
    def run(self):
        """Run the main scraping process."""
        self.logger.info("Starting LLRF2025 conference data scraping")
        self.logger.info(f"Event URL: https://indico.jlab.org/event/{self.event_id}/")
        start_time = time.time()
        
        try:
            # Fetch event data
            if not self.fetch_event_data():
                self.logger.error("Failed to fetch event data. Exiting.")
                return False
            
            # Process contributions
            self.process_contributions()
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"\n🎉 Scraping completed! Time elapsed: {elapsed_time:.2f} seconds")
            self.logger.info(f"📊 Final statistics:")
            self.logger.info(f"  ✅ Total contributions: {self.stats['total_contributions']}")
            self.logger.info(f"  🎤 Oral presentations: {self.stats['oral_presentations']}")
            self.logger.info(f"  📋 Posters: {self.stats['posters']}")
            self.logger.info(f"  📥 Downloaded files: {self.stats['downloaded_files']}")
            self.logger.info(f"  ❌ Errors: {self.stats['errors']}")
            self.logger.info(f"\n📁 Output directory: {self.output_dir.absolute()}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Critical error during scraping process: {e}")
            raise


def main():
    """Main function to run the LLRF2025 scraper."""
    print("LLRF2025 Conference Web Scraper")
    print("=" * 60)
    print("Comprehensive scraper for LLRF2025 conference (Indico)")
    print("Author: Ming Liu")
    print("Event: https://indico.jlab.org/event/939/")
    print()
    
    scraper = LLRF2025Scraper()
    
    try:
        success = scraper.run()
        
        if success:
            print("\n" + "="*60)
            print("Scraping completed successfully!")
            print(f"Output directory: {scraper.output_dir.absolute()}")
            print("\nMain output files:")
            print("  📊 LLRF2025_Summary.txt - Complete scraping report")
            print("  📈 LLRF2025_All_Contributions.csv - All contributions Excel table")
            print("  🗂️ LLRF2025_All_Contributions.json - Complete data in JSON")
            print("  📁 Oral_Presentations/ - Downloaded oral presentation files")
            print("  📁 Posters/ - Downloaded poster files")
            print("  📁 Attachments/ - Other downloaded attachments")
            print("  📁 By_Date/ - Contributions grouped by date")
        
    except KeyboardInterrupt:
        print("\n⏹️ User interrupted scraping")
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")


if __name__ == "__main__":
    main()
