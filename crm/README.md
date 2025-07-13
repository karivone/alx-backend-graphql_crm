CRM Celery Setup Guide
This guide explains how to set up and run Celery with Redis for the CRM application's background tasks and scheduled reports.

Prerequisites
Python 3.8+
Django 4.2+
Redis server
Installation Steps
1. Install Redis
Ubuntu/Debian:

sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
macOS (using Homebrew):

brew install redis
brew services start redis
Windows: Download and install Redis from the official website or use WSL.

2. Verify Redis Installation
