#!/usr/bin/env python3
"""
This script checks the environment for proper configuration
and displays helpful information about the application setup.
"""

import os
import sys
import logging
from pprint import pformat

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("environment_check")

def check_directories():
    """Check if all required directories exist and have proper permissions"""
    directories = [
        "/app/app/static",
        "/app/app/static/pdfs",
        "/app/app/static/qrcodes",
        "/app/instance",
        "/app/data/simple_invites"
    ]
    
    logger.info("Checking directory structure...")
    
    for directory in directories:
        if os.path.exists(directory):
            is_writable = os.access(directory, os.W_OK)
            logger.info(f"{directory}: {'✅ Exists and writable' if is_writable else '❌ Exists but NOT writable'}")
        else:
            logger.warning(f"{directory}: ❌ Does not exist")
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"  Created directory: {directory}")
            except Exception as e:
                logger.error(f"  Failed to create directory: {e}")

def check_hostname():
    """Check if APP_HOSTNAME is set properly"""
    hostname = os.environ.get("APP_HOSTNAME", "")
    
    logger.info("\nChecking hostname configuration...")
    
    if not hostname:
        logger.error("❌ APP_HOSTNAME environment variable is not set!")
        logger.error("   This will cause incorrect URLs in PDFs and QR codes.")
        logger.error("   Set APP_HOSTNAME in your docker-compose.yml file.")
        logger.error("   Example: APP_HOSTNAME=https://your-production-domain.com")
    elif hostname == "http://localhost:5000":
        logger.warning("⚠️ APP_HOSTNAME is set to the default value: http://localhost:5000")
        logger.warning("   This may cause issues if your application is accessed from other devices.")
        logger.warning("   Consider setting it to your actual domain or IP address.")
    else:
        logger.info(f"✅ APP_HOSTNAME is set to: {hostname}")

def check_environment_variables():
    """Check all environment variables"""
    logger.info("\nChecking environment variables...")
    
    # List of environment variables to check (excluding sensitive ones)
    env_vars = {
        "APP_HOSTNAME": os.environ.get("APP_HOSTNAME", ""),
        "FLASK_APP": os.environ.get("FLASK_APP", ""),
        "FLASK_ENV": os.environ.get("FLASK_ENV", ""),
        "PDF_CLEANUP_MINUTES": os.environ.get("PDF_CLEANUP_MINUTES", "")
    }
    
    logger.info(pformat(env_vars))

def main():
    """Run all checks"""
    logger.info("=" * 80)
    logger.info("ENVIRONMENT CHECK")
    logger.info("=" * 80)
    
    check_directories()
    check_hostname()
    check_environment_variables()
    
    logger.info("=" * 80)
    logger.info("Environment check completed.")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
