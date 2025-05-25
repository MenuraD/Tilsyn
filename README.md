# Tilsyn: Child Supervision Application

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## Introduction
In the digital age, children face risks like cyberbullying, predators, and inappropriate content while parents struggle with monitoring due to time constraints and technological complexity. Tilsyn addresses this gap by offering a balanced solution that respects privacy while providing essential oversight.

## Problem Definition & Research Gap
Existing parental tools often:
- Have complex interfaces
- Are overly invasive
- Lack privacy considerations
- Fail to foster parent-child communication

Tilsyn bridges this gap through:
- Transparent monitoring with consent
- Privacy-preserving features
- Educational resources
- User-friendly interface

## Project Description
A full-stack application for parental supervision of child online activities. Features real-time tracking of web usage, login attempts, screen time, and security alerts. Built with Flask (Python) for the backend and a cyberpunk-styled frontend.

---

## Key Features

### Frontend
- Cyberpunk aesthetic with neon effects
- Mobile-optimized layouts
- Security status indicators
- Interactive dashboards
- Activity tracking visualizations

### Backend
- **Role-based Authentication**: Separate parent/child accounts
- **Comprehensive Monitoring**:
  - Website visits (including incognito detection)
  - Login attempts tracking
  - Keyword monitoring (drugs, violence, etc.)
  - IP history with geolocation
- **Google Safe Browsing Integration**: Real-time URL safety checks
- **Screen Time Management**: Usage tracking 
- **Privacy Controls**: Child-controlled data visibility

## Objectives
1. Develop functional child safety application
2. Create intuitive user interface
3. Implement privacy-conscious monitoring
4. Foster parent-child digital safety discussions
5. Ensure GDPR/COPPA compliance
6. Maintain high system reliability 

## Tech Stack
- **Frontend**: HTML5, CSS3 (Cyberpunk theme), JavaScript
- **Backend**: Python/Flask
- **Database**: PostgreSQL
- **Extensions**: Chrome Manifest v3
- **APIs**: Google Safe Browsing, IP Geolocation

---

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL
- Google API Key

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/tilsyn.git
   cd tilsyn

2. Install Python dependencies
    ```bash
    pip install flask psycopg2-binary werkzeug python-dotenv ipaddress

3. Set up PostgreSQL database:
    ```sql
    CREATE DATABASE mydatabase;
    CREATE USER postgres WITH PASSWORD 'guyi2123';
    GRANT ALL PRIVILEGES ON DATABASE mydatabase TO postgres;

## Configuration

1. Add a .env file:
    ```env
    GOOGLE_API_KEY="your_google_api_key"
    DB_PASSWORD="guyi2123" 

2. Update database connection in app.py
    ```python
    # Modify get_db_connection() parameters
    host="localhost"
    port="5432"

## Database Schema

Key tables include:

- users: Stores child/parent accounts (flags: is_child, show_ip_history)
- adults: Links parent users to child accounts
- registrations/logins: Tracks email signups and authentication attempts
- visited_websites: Records browsing history with safety status
- keyword_alerts: Stores flagged sensitive content
- screen_time: Daily app usage duration

Run SQL queries from the Flask routes to auto-create tables on first use.

## API Endpoints

| Endpoint              | Method | Description                          |
|-----------------------|--------|--------------------------------------|
| /api/track-email      | POST   | Logs email registrations             |
| /api/track-login      | POST   | Records login attempts               |
| /api/track-visit      | POST   | Tracks website visits                |
| /api/track-activity   | POST   | Logs system/app usage                |
| /api/keyword-data     | GET    | Returns flaggeed keywords            |
| /api/screen-time-data | GET    | Provides daily screen time analytics |

## Usage

### Registration
- Register a child account (ages 12-17)
- Link a parent account (age ≥18)
    

### Parent Dashboard
- Real-time activity monitoring
- Screen time reports
- Incognito mode alerts
- Keyword alert notifications
- Monitor IP locations  
- Review login attempts  
- View screen time reports
    

### Child Account
- Automatic activity tracking    
- Real-time safety checks for visited URLs
- Privacy control toggles

## Chrome Extension

### Features
- Incognito mode detection
- Form submission tracking
- Real-time notifications
- Local data storage

## File Structure

tilsyn/
├── background_agent/
│   └── background_agent.py
├── extension/
│   ├── manifest.json
│   ├── background.js
│   └── content.js
├── templates/
│   ├── parents_dashboard.html
│   ├── login.html
│   └── ...(other templates)
├── static/
│   └── design/main.css
├── app.py
├── utils.py
└── requirements.txt

## Styles Overview
The styling is managed through `main.css` which features:

- Responsive design with desktop-first approach
- Glassmorphism effects
- Cyberpunk-inspired animations
- Google Fonts integration (Oswald + Rubik Vinyl)
- Interactive hover states and transitions
- Themed components for different pages

### Dependencies
```css
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@200..700&family=Rubik+Vinyl&display=swap');
```

### Code Structure
The CSS is organized into logical sections:
1. Base styles
2. Navigation
3. Page-specific styles (Home, Login, Registration, etc.)
4. Media queries
5. Animation keyframes

## Usage
Include the CSS stylesheet in your HTML head:
```html
<link rel="stylesheet" href="main.css">
```

## Preview
![Home Page Preview](screenshots/home-preview.jpg)
```