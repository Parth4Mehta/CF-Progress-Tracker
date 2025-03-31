# Codeforces Progress Tracker

A simple desktop widget to track your Codeforces problem-solving progress with an intuitive scoring system.

## Features
- **Automatic submission syncing** every 10 minutes
- **Full history sync & Manual sync option**
- **Manual problem entry** (for minor accounts)
- **Progress visualization**
- **Record management**

## Scoring Formula
Daily score = `(rating / base) ^ exponent`
- `base = your rating + 100`
- `exponent = 1 + (your rating / 2000)`

*ppd (personal problem difficulty) represents how difficult the problem is to 'you' specifically based on your virtualized rating.*

## Installation & Usage
### Windows
1. Install Python (if not already installed) from [python.org](https://www.python.org/).
2. Clone the repository:
   ```sh
   git clone https://github.com/Parth4Mehta/CF-Progress-Tracker.git
   ```
3. Navigate to the directory:
   ```sh
   cd CF-Progress-Tracker
   ```
4. Install dependencies (if required):
   ```sh
   pip install -r requirements.txt  # If dependencies exist
   ```
5. Run the widget using the batch file:
   ```sh
   start tracker.bat
   ```

### Mac/Linux
1. Install Python (if not already installed).
2. Clone the repository:
   ```sh
   git clone https://github.com/<your-username>/CF-Progress-Tracker.git
   ```
3. Navigate to the directory:
   ```sh
   cd CF-Progress-Tracker
   ```
4. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
5. Run the script directly:
   ```sh
   python codeforces_tracker.py
   ```

## Help
### Codeforces Progress Tracker Help
Hello bud, this widget tracks and scores your CF journey based on **ppd**.

- Enter your CF handle, 'sync' will collect all your 'accepted' submissions.
- Your virtualized rating represents the rating of problems slightly above your level.
- Enter your **very short-term rating goal** as your virtualized rating.

### Key Features:
- **Automatic submission syncing every 10 minutes**
- **Full history sync / Manual sync option**
- **Manual problem entry** (for minor accounts)
- **Progress visualization**
- **Record management**

## Contributions
Feel free to contribute! Submit a pull request or report issues in the [GitHub Issues](https://github.com/<your-username>/CF-Progress-Tracker/issues) section.

## License
This project is licensed under the **MIT License**.