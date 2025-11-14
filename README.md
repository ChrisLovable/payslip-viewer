# Payslip Viewer

Simple mobile-optimized web application to upload a PDF with multiple payslips and allow employees to view their payslip by entering their ID number. **Optimized for mobile devices - can be installed as a mobile app!**

## Quick Start

1. **Install Python 3.8+** (if not already installed)

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```
   python app.py
   ```

4. **Open browser to:** `http://localhost:5000`

5. **Upload your PDF** via the web interface - any filename is fine (e.g., `payslips_january_2024.pdf`)

## How It Works

1. Upload a PDF file containing multiple payslips (one per page)
2. The system automatically extracts ID numbers from each page
3. Employees enter their ID number to view only their payslip

## PDF Requirements

- **Format:** Standard PDF file
- **ID Number:** Each page must contain a 13-digit ID number (South African format)
- **Location:** ID can be anywhere on the page - the system will find it
- **Filename:** **Any name is fine!** The system doesn't care about the filename - you select the month when uploading
  - Examples: `payslips.pdf`, `january_payslips.pdf`, `payslip_2024.pdf`, etc.
  - **The month is selected via the month picker in the upload form, not from the filename**

## Deployment Options

### Option 1: Render.com (Recommended - Free Tier Available)

1. Create account at [render.com](https://render.com)
2. Create new **Web Service**
3. Connect your GitHub repository (or upload files)
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
5. Deploy!

### Option 2: Railway.app

1. Create account at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Auto-detects Python and deploys automatically

### Option 3: PythonAnywhere

1. Upload files via web interface
2. Run in web app console
3. Configure WSGI file

### Option 4: Heroku

1. Create `Procfile` with: `web: python app.py`
2. Deploy via Heroku CLI or GitHub integration

## Mobile App Installation

Employees can install this as a mobile app:
- **Android/Chrome**: Open the link, tap the menu (⋮), select "Add to Home Screen"
- **iPhone/Safari**: Open the link, tap Share button, select "Add to Home Screen"
- The app will work like a native mobile app!

## Sharing the Link

Once deployed, share the public URL with your employees. They can:
1. Open the link on their mobile device
2. Select the month
3. Enter their ID number
4. View their payslip instantly (with pinch-to-zoom support)

## Notes

- The system stores the PDF in the `uploads` folder
- ID numbers are extracted automatically from each page
- Only the matching page is displayed to employees
- No database needed - everything works in memory

