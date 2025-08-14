#!/usr/bin/env python3
"""
Master Uploader Script

This script runs all MongoDB uploader scripts in the build_metadata directory
in a logical order to populate the Daemonium database.

Author: Daemonium Project
Date: 2025-07-27
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MasterUploader:
    """Orchestrates the execution of all uploader scripts."""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.stats = {
            'total_scripts': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'execution_times': {}
        }
        
        # Define the order of script execution (dependencies first)
        self.script_order = [
            'upload_philosophy_schools_to_mongodb.py',      # Philosophy schools (foundational)
            'upload_philosophers_to_mongodb.py',            # Philosophers data
            'upload_philosophy_keywords_to_mongodb.py',     # Philosophy keywords (foundational concepts)
            'upload_books_to_mongodb.py',                    # Core books data
            'upload_book_summaries_to_mongodb.py',           # Book summaries
            'upload_philosopher_bios_to_mongodb.py',         # Philosopher biographies
            'upload_philosopher_summaries_to_mongodb.py',    # Philosopher summaries
            'upload_bibliography_to_mongodb.py',            # Bibliography data
            'upload_aphorisms_to_mongodb.py',               # Aphorisms
            'upload_philosophy_themes_to_mongodb.py',        # Philosophy themes
            'upload_philosophy_concepts_to_mongodb.py',     # Philosophy concepts
            'upload_top_10_ideas_to_mongodb.py',            # Top ideas
            'upload_idea_summaries_to_mongodb.py',          # Idea summaries
            'upload_modern_adaptations_to_mongodb.py',      # Modern adaptations
            'upload_persona_cores_to_mongodb.py',           # Persona cores
            'upload_philosopher_bots_to_mongodb.py',        # Philosopher bots
            'upload_chat_blueprints_to_mongodb.py',         # Chat blueprints
            'upload_conversation_logic_to_mongodb.py',      # Conversation logic
            'upload_discussion_hooks_to_mongodb.py'         # Discussion hooks
        ]
    
    def get_available_scripts(self) -> List[str]:
        """Get list of available uploader scripts."""
        scripts = []
        for script_name in self.script_order:
            script_path = self.script_dir / script_name
            if script_path.exists():
                scripts.append(script_name)
            else:
                logger.warning(f"Script not found: {script_name}")
                self.stats['skipped'] += 1
        
        return scripts
    
    def run_script(self, script_name: str) -> bool:
        """Run a single uploader script."""
        script_path = self.script_dir / script_name
        
        if not script_path.exists():
            logger.error(f"Script not found: {script_name}")
            return False
        
        logger.info(f"Starting execution of: {script_name}")
        start_time = time.time()
        
        try:
            # Run the script using subprocess
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.script_dir.parent,  # Run from project root
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout per script
            )
            
            execution_time = time.time() - start_time
            self.stats['execution_times'][script_name] = execution_time
            
            if result.returncode == 0:
                logger.info(f"[SUCCESS] Successfully completed: {script_name} (took {execution_time:.2f}s)")
                
                # Log any important output
                if result.stdout:
                    # Only log summary lines to avoid spam
                    output_lines = result.stdout.strip().split('\n')
                    for line in output_lines:
                        if any(keyword in line.lower() for keyword in 
                              ['summary', 'total', 'successful', 'failed', 'processed']):
                            logger.info(f"  {script_name}: {line}")
                
                return True
            else:
                logger.error(f"[FAILED] Failed to execute: {script_name} (exit code: {result.returncode})")
                
                # Log error output
                if result.stderr:
                    logger.error(f"Error output from {script_name}:")
                    for line in result.stderr.strip().split('\n')[:10]:  # Limit error lines
                        logger.error(f"  {line}")
                
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"[TIMEOUT] Timeout executing: {script_name} (exceeded 10 minutes)")
            return False
        except Exception as e:
            execution_time = time.time() - start_time
            self.stats['execution_times'][script_name] = execution_time
            logger.error(f"[ERROR] Exception executing {script_name}: {e}")
            return False
    
    def run_all_scripts(self, continue_on_error: bool = True) -> Dict[str, Any]:
        """Run all uploader scripts in order."""
        logger.info("=" * 60)
        logger.info("STARTING MASTER UPLOADER - DAEMONIUM DATABASE POPULATION")
        logger.info("=" * 60)
        
        scripts = self.get_available_scripts()
        self.stats['total_scripts'] = len(scripts)
        
        if not scripts:
            logger.error("No uploader scripts found!")
            return self.stats
        
        logger.info(f"Found {len(scripts)} uploader scripts to execute")
        logger.info(f"Execution order: {', '.join(scripts)}")
        logger.info("")
        
        failed_scripts = []
        
        for i, script_name in enumerate(scripts, 1):
            logger.info(f"[{i}/{len(scripts)}] Executing: {script_name}")
            
            success = self.run_script(script_name)
            
            if success:
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1
                failed_scripts.append(script_name)
                
                if not continue_on_error:
                    logger.error(f"Stopping execution due to failure in: {script_name}")
                    break
            
            # Add a small delay between scripts
            if i < len(scripts):
                logger.info("Waiting 2 seconds before next script...")
                time.sleep(2)
            
            logger.info("")
        
        # Print final summary
        self.print_summary(failed_scripts)
        return self.stats
    
    def print_summary(self, failed_scripts: List[str]):
        """Print execution summary."""
        total_time = sum(self.stats['execution_times'].values())
        
        logger.info("=" * 60)
        logger.info("MASTER UPLOADER EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total scripts: {self.stats['total_scripts']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"Total execution time: {total_time:.2f} seconds")
        logger.info("")
        
        if self.stats['execution_times']:
            logger.info("Execution times by script:")
            for script, exec_time in self.stats['execution_times'].items():
                status = "[OK]" if script not in failed_scripts else "[FAIL]"
                logger.info(f"  {status} {script}: {exec_time:.2f}s")
            logger.info("")
        
        if failed_scripts:
            logger.error("Failed scripts:")
            for script in failed_scripts:
                logger.error(f"  [FAIL] {script}")
            logger.info("")
            logger.info("You may want to check the individual script logs for detailed error information.")
        else:
            logger.info("[SUCCESS] All scripts executed successfully!")
        
        logger.info("=" * 60)


def main():
    """Main function to run all uploaders."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run all MongoDB uploader scripts')
    parser.add_argument(
        '--stop-on-error', 
        action='store_true',
        help='Stop execution if any script fails (default: continue on error)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show which scripts would be executed without running them'
    )
    
    args = parser.parse_args()
    
    uploader = MasterUploader()
    
    if args.dry_run:
        scripts = uploader.get_available_scripts()
        logger.info("DRY RUN - Scripts that would be executed:")
        for i, script in enumerate(scripts, 1):
            logger.info(f"  {i}. {script}")
        logger.info(f"\nTotal: {len(scripts)} scripts")
        return
    
    try:
        stats = uploader.run_all_scripts(continue_on_error=not args.stop_on_error)
        
        # Exit with error code if any scripts failed
        if stats['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("\nExecution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
