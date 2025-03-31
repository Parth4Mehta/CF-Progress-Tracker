import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import sqlite3
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging
import requests
import json
import time

# Configure logging
logging.basicConfig(filename="tracker.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class CodeforcesTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Codeforces Progress Tracker")
        self.root.geometry("600x400")
        self.root.attributes('-topmost', True)  # Always on top
        
        # Apply Nordic theme colors
        self.colors = {
            "bg_dark": "#2E3440",
            "bg_medium": "#3B4252",
            "text_light": "#EFF1F6",
            "accent": "#88C0D0",
            "highlight": "#5E81AC"
        }
        
        # Configure the theme for the application
        self.root.configure(bg=self.colors["bg_dark"])
        self.style = ttk.Style()
        self.style.configure("TButton", background=self.colors["bg_medium"], foreground=self.colors["text_light"])
        self.style.configure("TProgressbar", background=self.colors["accent"], troughcolor=self.colors["bg_medium"])
        self.style.configure("TFrame", background=self.colors["bg_dark"])
        
        # Database setup
        self.conn = sqlite3.connect("codeforces_tracker.db")
        self.cursor = self.conn.cursor()
        self.create_table()

        # Initialize variables
        self.today = datetime.date.today()
        self.user_handle = self.get_user_handle()  # Get or prompt for user handle
        self.user_rating = self.get_user_rating()  # Get or prompt for user rating
        self.base = self.user_rating + 100  # base = rating + 100
        self.exp = 1 + (self.user_rating / 2000)  # exponent = 1 + rating/2000
        self.today_score = self.get_today_score()
        
        # Last checked submission time
        self.last_submission_time = self.get_last_submission_time()

        # UI Setup
        self.setup_ui()

    def create_table(self):
        """Create the database tables if they don't exist and add missing columns if needed."""
        # Create main tables if they don't exist
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS problems (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                date TEXT,
                                rating INTEGER,
                                problem_id TEXT,
                                submission_id INTEGER)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_rating (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                rating INTEGER)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_info (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                handle TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sync_info (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                last_submission_time INTEGER)''')

        # Check if problem_id column exists, add it if it doesn't
        try:
            self.cursor.execute("SELECT problem_id FROM problems LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            self.cursor.execute("ALTER TABLE problems ADD COLUMN problem_id TEXT")
            logging.info("Added missing problem_id column to problems table")

        # Check if submission_id column exists, add it if it doesn't
        try:
            self.cursor.execute("SELECT submission_id FROM problems LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            self.cursor.execute("ALTER TABLE problems ADD COLUMN submission_id INTEGER")
            logging.info("Added missing submission_id column to problems table")

        self.conn.commit()

    def get_user_handle(self):
        """Get the user's Codeforces handle from the database or prompt for it."""
        self.cursor.execute("SELECT handle FROM user_info ORDER BY id DESC LIMIT 1")
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            handle = simpledialog.askstring("Codeforces Handle", "Enter your Codeforces handle:")
            if handle:
                self.cursor.execute("INSERT INTO user_info (handle) VALUES (?)", (handle,))
                self.conn.commit()
                return handle
            else:
                messagebox.showerror("Error", "Please enter a valid Codeforces handle.")
                return self.get_user_handle()  # Retry until valid input

    def update_user_handle(self):
        """Update the user's Codeforces handle in the database."""
        new_handle = simpledialog.askstring("Update Handle", "Enter your new Codeforces handle:")
        if new_handle:
            self.cursor.execute("INSERT INTO user_info (handle) VALUES (?)", (new_handle,))
            self.conn.commit()
            self.user_handle = new_handle
            messagebox.showinfo("Success", "Handle updated successfully.")
        else:
            messagebox.showerror("Error", "Please enter a valid Codeforces handle.")

    def get_user_rating(self):
        """Get the user's rating from the database or prompt for it."""
        self.cursor.execute("SELECT rating FROM user_rating ORDER BY id DESC LIMIT 1")
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            rating = simpledialog.askinteger("Current Rating", "Enter your virtualized rating:")
            if rating is not None and 0 <= rating <= 4000:  # Validate rating range
                self.cursor.execute("INSERT INTO user_rating (rating) VALUES (?)", (rating,))
                self.conn.commit()
                return rating
            else:
                messagebox.showerror("Error", "Please enter a valid rating between 0 and 4000.")
                return self.get_user_rating()  # Retry until valid input

    def get_last_submission_time(self):
        """Get the timestamp of the last checked submission."""
        self.cursor.execute("SELECT last_submission_time FROM sync_info ORDER BY id DESC LIMIT 1")
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            # Default to a day ago if no previous sync
            yesterday = int(time.time()) - 86400
            self.cursor.execute("INSERT INTO sync_info (last_submission_time) VALUES (?)", (yesterday,))
            self.conn.commit()
            return yesterday

    def update_last_submission_time(self, timestamp):
        """Update the timestamp of the last checked submission."""
        self.cursor.execute("INSERT INTO sync_info (last_submission_time) VALUES (?)", (timestamp,))
        self.conn.commit()
        self.last_submission_time = timestamp

    def update_user_rating(self):
        """Update the user's rating in the database."""
        new_rating = simpledialog.askinteger("Update Rating", "Enter your new Codeforces rating:")
        if new_rating is not None and 0 <= new_rating <= 4000:  # Validate rating range
            self.cursor.execute("INSERT INTO user_rating (rating) VALUES (?)", (new_rating,))
            self.conn.commit()
            self.user_rating = new_rating
            self.base = self.user_rating + 100
            self.exp = 1 + (self.user_rating / 2000)
            messagebox.showinfo("Success", "Rating updated successfully.")
        else:
            messagebox.showerror("Error", "Please enter a valid rating between 0 and 4000.")

    def setup_ui(self):
        """Set up the user interface."""
        # Frame for user info
        info_frame = tk.Frame(self.root, bg=self.colors["bg_dark"])
        info_frame.pack(pady=5)

        tk.Label(info_frame, text=f"Handle: {self.user_handle}", 
                 bg=self.colors["bg_dark"], fg=self.colors["text_light"]).pack(side=tk.LEFT, padx=10)
        tk.Label(info_frame, text=f"Rating: {self.user_rating}", 
                 bg=self.colors["bg_dark"], fg=self.colors["text_light"]).pack(side=tk.LEFT, padx=10)

        # Frame for score and progress bar
        score_frame = tk.Frame(self.root, bg=self.colors["bg_dark"])
        score_frame.pack(pady=10)

        tk.Label(score_frame, text="Today's Score:", font=("Arial", 14), 
                 bg=self.colors["bg_dark"], fg=self.colors["text_light"]).pack()
        self.score_label = tk.Label(score_frame, text=f"{self.today_score:.2f}", 
                                    font=("Arial", 18, "bold"), 
                                    bg=self.colors["bg_dark"], fg=self.colors["accent"])
        self.score_label.pack()

        self.progress = ttk.Progressbar(score_frame, orient="horizontal", length=300, mode="determinate", 
                                       style="TProgressbar")
        self.progress.pack(pady=10)
        self.update_progress()

        # Frame for sync status
        sync_frame = tk.Frame(self.root, bg=self.colors["bg_dark"])
        sync_frame.pack(pady=5)

        self.sync_status = tk.Label(sync_frame, text="Last synced: Never", 
                                  bg=self.colors["bg_dark"], fg=self.colors["text_light"])
        self.sync_status.pack()

        sync_button = tk.Button(sync_frame, text="Sync New Submissions", command=self.sync_with_codeforces,
                              bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        sync_button.pack(pady=5, side=tk.LEFT, padx=5)

        full_sync_button = tk.Button(sync_frame, text="Sync Full History", 
                                   command=lambda: self.sync_with_codeforces(full_history=True),
                                   bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        full_sync_button.pack(pady=5, side=tk.LEFT, padx=5)

        # Frame for manual problem entry
        entry_frame = tk.Frame(self.root, bg=self.colors["bg_dark"])
        entry_frame.pack(pady=10)

        tk.Label(entry_frame, text="Manual entry - Problem rating:", 
                 bg=self.colors["bg_dark"], fg=self.colors["text_light"]).pack()
        self.rating_entry = tk.Entry(entry_frame, bg=self.colors["bg_medium"], fg=self.colors["text_light"],
                                   insertbackground=self.colors["text_light"])
        self.rating_entry.pack()

        self.submit_button = tk.Button(entry_frame, text="Submit", command=self.add_problem,
                                     bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        self.submit_button.pack(pady=5)

        # Frame for buttons
        button_frame = tk.Frame(self.root, bg=self.colors["bg_dark"])
        button_frame.pack(pady=10)

        self.history_button = tk.Button(button_frame, text="Show Progress Graph", command=self.show_graph,
                                      bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        self.history_button.pack(side=tk.LEFT, padx=5)

        self.manage_button = tk.Button(button_frame, text="Manage Records", command=self.manage_records,
                                     bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        self.manage_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = tk.Button(button_frame, text="Reset Database", command=self.reset_database,
                                    bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        self.reset_button.pack(side=tk.LEFT, padx=5)

        self.update_rating_button = tk.Button(button_frame, text="Update Rating", command=self.update_user_rating,
                                           bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        self.update_rating_button.pack(side=tk.LEFT, padx=5)

        self.update_handle_button = tk.Button(button_frame, text="Update Handle", command=self.update_user_handle,
                                           bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        self.update_handle_button.pack(side=tk.LEFT, padx=5)

        self.help_button = tk.Button(button_frame, text="Help", command=self.show_help,
                                  bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        self.help_button.pack(side=tk.LEFT, padx=5)

        # Auto-sync on startup - just recent submissions
        self.root.after(1000, self.sync_with_codeforces)

        # Ask if user wants to sync full history on first run
        self.check_first_run()

    def check_first_run(self):
        """Check if this is the first run and ask if user wants to sync full history."""
        self.cursor.execute("SELECT COUNT(*) FROM problems")
        count = self.cursor.fetchone()[0]
        if count == 0:
            response = messagebox.askyesno(
                "First Run Detected", 
                "It looks like this is your first run or the database is empty. " +
                "Would you like to sync your full submission history from Codeforces?"
            )
            if response:
                self.root.after(2000, lambda: self.sync_with_codeforces(full_history=True))

    def get_today_score(self):
        """Calculate today's score based on problems solved."""
        self.cursor.execute("SELECT rating FROM problems WHERE date = ?", (str(self.today),))
        ratings = self.cursor.fetchall()
        return sum((r[0] / self.base) ** self.exp for r in ratings) if ratings else 0

    def add_problem(self, date=None, rating=None, problem_id=None, submission_id=None):
        """Add a problem to the database."""
        try:
            if rating is None:
                rating = int(self.rating_entry.get())
            if date is None:
                date = str(self.today)

            if not self.validate_rating(rating):
                messagebox.showerror("Error", "Rating must be between 800 and 3500.")
                return

            # Check if problem already exists for today (if has problem_id)
            if problem_id:
                self.cursor.execute(
                    "SELECT id FROM problems WHERE date = ? AND problem_id = ?", 
                    (date, problem_id)
                )
                if self.cursor.fetchone():
                    return  # Skip if already added

            self.cursor.execute(
                "INSERT INTO problems (date, rating, problem_id, submission_id) VALUES (?, ?, ?, ?)", 
                (date, rating, problem_id, submission_id)
            )
            self.conn.commit()
            self.update_today_score()
            if not problem_id:  # Only clear entry field for manual entries
                self.rating_entry.delete(0, tk.END)
            logging.info(f"Added problem: date={date}, rating={rating}, problem_id={problem_id}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.")
            logging.error("Invalid input for rating.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")
            logging.error(f"Database error: {e}")

    def update_today_score(self):
        """Update the displayed score and progress bar."""
        self.today_score = self.get_today_score()
        self.score_label.config(text=f"{self.today_score:.2f}")
        self.update_progress()

    def update_progress(self):
        """Update the progress bar based on today's score."""
        self.progress["value"] = (self.today_score / 2) * 100

    def sync_with_codeforces(self, full_history=False):
        """
        Sync with Codeforces API to get submissions.
        
        Args:
            full_history (bool): If True, fetches all historical submissions regardless of last sync time
        """
        try:
            # Update UI to show sync in progress
            self.sync_status.config(text="Syncing with Codeforces...")
            self.root.update()
            
            # Initialize counters and trackers
            problems_added = 0
            latest_submission_time = self.last_submission_time
            
            # Keep fetching submissions in batches until we've got them all
            from_index = 1
            batch_size = 100
            more_submissions = True
            
            while more_submissions:
                # Get user submissions from Codeforces API
                response = requests.get(
                    f"https://codeforces.com/api/user.status?handle={self.user_handle}&from={from_index}&count={batch_size}"
                )
                
                if response.status_code != 200:
                    messagebox.showerror("API Error", f"Failed to fetch submissions: {response.status_code}")
                    self.sync_status.config(text=f"Last sync failed: {datetime.datetime.now().strftime('%H:%M:%S')}")
                    return
                    
                data = response.json()
                
                if data["status"] != "OK":
                    messagebox.showerror("API Error", f"API returned error: {data['comment']}")
                    self.sync_status.config(text=f"Last sync failed: {datetime.datetime.now().strftime('%H:%M:%S')}")
                    return
                
                submissions = data["result"]
                
                # If we received fewer submissions than batch_size, we've reached the end
                if len(submissions) < batch_size:
                    more_submissions = False
                else:
                    from_index += batch_size
                
                # Process submissions
                for submission in submissions:
                    # Skip if it's not a new submission and we're not doing full history
                    if not full_history and submission["creationTimeSeconds"] <= self.last_submission_time:
                        more_submissions = False  # We've reached already synced submissions, no need to fetch more
                        break
                        
                    # Check if it's an accepted solution
                    if submission["verdict"] == "OK":
                        problem = submission["problem"]
                        
                        # Skip if no rating available
                        if "rating" not in problem:
                            continue
                            
                        problem_id = f"{problem['contestId']}{problem['index']}"
                        submission_time = submission["creationTimeSeconds"]
                        submission_date = datetime.datetime.fromtimestamp(submission_time).date()
                        
                        # Add to database
                        self.add_problem(
                            date=str(submission_date),
                            rating=problem["rating"],
                            problem_id=problem_id,
                            submission_id=submission["id"]
                        )
                        problems_added += 1
                        
                    # Track latest submission time
                    if submission["creationTimeSeconds"] > latest_submission_time:
                        latest_submission_time = submission["creationTimeSeconds"]
                
                # Update UI during lengthy syncs
                self.sync_status.config(
                    text=f"Syncing: {problems_added} problems found so far..."
                )
                self.root.update()
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
            
            # Update last submission time
            if latest_submission_time > self.last_submission_time:
                self.update_last_submission_time(latest_submission_time)
                    
            # Update UI
            self.sync_status.config(
                text=f"Last sync: {datetime.datetime.now().strftime('%H:%M:%S')} - Added {problems_added} problems"
            )
            
            # Schedule next sync (every 10 minutes) - but only for incremental syncs
            if not full_history:
                self.root.after(600000, self.sync_with_codeforces)
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Failed to connect to Codeforces API: {e}")
            self.sync_status.config(text=f"Last sync failed: {datetime.datetime.now().strftime('%H:%M:%S')}")
            logging.error(f"Network error during sync: {e}")
            # Try again in 2 minutes if there was an error
            if not full_history:
                self.root.after(120000, self.sync_with_codeforces)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during sync: {e}")
            self.sync_status.config(text=f"Last sync failed: {datetime.datetime.now().strftime('%H:%M:%S')}")
            logging.error(f"Error during sync: {e}")
            # Try again in 2 minutes if there was an error
            if not full_history:
                self.root.after(120000, self.sync_with_codeforces)

    def show_graph(self):
        """Display a graph of progress over the last 30 days."""
        # Calculate date range for the last 30 days
        end_date = self.today
        start_date = end_date - datetime.timedelta(days=29)
        
        # Generate a complete list of dates for the last 30 days
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(str(current_date))
            current_date += datetime.timedelta(days=1)
        
        # Get actual problem data
        self.cursor.execute("SELECT date, rating FROM problems WHERE date BETWEEN ? AND ? ORDER BY date", 
                          (str(start_date), str(end_date)))
        data = self.cursor.fetchall()
        
        # Calculate scores for each date
        score_dict = {date: 0 for date in date_list}  # Initialize all dates with zero score
        for date, rating in data:
            # Add to existing score for this date
            score_dict[date] = score_dict.get(date, 0) + (rating / self.base) ** self.exp
        
        # Prepare data for plotting
        dates = list(score_dict.keys())
        scores = list(score_dict.values())
        
        # Create figure with the Nordic color scheme
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=self.colors["bg_dark"])
        ax.set_facecolor(self.colors["bg_medium"])
        
        # Plot data
        ax.plot(dates, scores, marker='o', linestyle='-', color=self.colors["accent"])
        ax.fill_between(dates, scores, color=self.colors["accent"], alpha=0.2)
        
        # Configure axes and title
        ax.set_xlabel("Date", color=self.colors["text_light"])
        ax.set_ylabel("Score", color=self.colors["text_light"])
        ax.set_title("Codeforces Progress (Last 30 Days)", color=self.colors["text_light"], fontsize=14)
        ax.grid(True, linestyle='--', alpha=0.3)
        
        # Style the plot to match the application theme
        ax.spines['bottom'].set_color(self.colors["text_light"])
        ax.spines['top'].set_color(self.colors["text_light"])
        ax.spines['left'].set_color(self.colors["text_light"])
        ax.spines['right'].set_color(self.colors["text_light"])
        ax.tick_params(axis='x', colors=self.colors["text_light"], rotation=45)
        ax.tick_params(axis='y', colors=self.colors["text_light"])
        
        # Show every 5th date to avoid overcrowding
        visible_ticks = [i for i in range(len(dates)) if i % 5 == 0]
        ax.set_xticks([dates[i] for i in visible_ticks])
        
        # Create popup window with the graph
        top = tk.Toplevel(self.root)
        top.title("Progress Graph - Last 30 Days")
        top.geometry("800x750")
        top.configure(bg=self.colors["bg_dark"])
        
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

    def manage_records(self):
        """Open a window to manage records."""
        top = tk.Toplevel(self.root)
        top.title("Manage Records")
        top.geometry("700x500")
        top.configure(bg=self.colors["bg_dark"])

        search_frame = tk.Frame(top, bg=self.colors["bg_dark"])
        search_frame.pack(pady=10)

        search_entry = tk.Entry(search_frame, width=30, bg=self.colors["bg_medium"], 
                               fg=self.colors["text_light"], insertbackground=self.colors["text_light"])
        search_entry.pack(side=tk.LEFT, padx=5)

        def search_records():
            query = search_entry.get()
            self.cursor.execute(
                """SELECT * FROM problems 
                   WHERE date LIKE ? OR rating LIKE ? OR problem_id LIKE ? 
                   ORDER BY date DESC, id DESC""",
                (f"%{query}%", f"%{query}%", f"%{query}%")
            )
            records = self.cursor.fetchall()
            listbox.delete(0, tk.END)
            for record in records:
                problem_id = record[3] if record[3] else "N/A"
                listbox.insert(tk.END, f"{record[0]} | {record[1]} | Rating: {record[2]} | Problem: {problem_id}")

        search_button = tk.Button(search_frame, text="Search", command=search_records,
                                bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        search_button.pack(side=tk.LEFT)

        clear_button = tk.Button(search_frame, text="Clear", 
                               command=lambda: (search_entry.delete(0, tk.END), load_all_records()),
                               bg=self.colors["bg_medium"], fg=self.colors["text_light"])
        clear_button.pack(side=tk.LEFT, padx=5)

        # Create a frame for the listbox with scrollbars
        list_frame = tk.Frame(top, bg=self.colors["bg_dark"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar_y = tk.Scrollbar(list_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = tk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        listbox = tk.Listbox(list_frame, width=70, height=20, bg=self.colors["bg_medium"],
                           fg=self.colors["text_light"], selectbackground=self.colors["highlight"])
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbars
        listbox.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.config(command=listbox.yview)
        scrollbar_x.config(command=listbox.xview)

        def load_all_records():
            self.cursor.execute("SELECT * FROM problems ORDER BY date DESC, id DESC")
            records = self.cursor.fetchall()
            listbox.delete(0, tk.END)
            for record in records:
                problem_id = record[3] if record[3] else "N/A"
                listbox.insert(tk.END, f"{record[0]} | {record[1]} | Rating: {record[2]} | Problem: {problem_id}")
            return records

        records = load_all_records()

        button_frame = tk.Frame(top, bg=self.colors["bg_dark"])
        button_frame.pack(pady=10)

        def delete_selected():
            selected = listbox.curselection()
            if not selected:
                messagebox.showerror("Error", "Select a record to delete.")
                return

            record_id = records[selected[0]][0]
            record_date = records[selected[0]][1]
            self.cursor.execute("DELETE FROM problems WHERE id = ?", (record_id,))
            self.conn.commit()
            listbox.delete(selected[0])
            records.pop(selected[0])
            if record_date == str(self.today):
                self.update_today_score()
            logging.info(f"Deleted record: id={record_id}")

        def update_selected():
            selected = listbox.curselection()
            if not selected:
                messagebox.showerror("Error", "Select a record to update.")
                return

            record_id = records[selected[0]][0]
            record_date = records[selected[0]][1]
            new_rating = simpledialog.askinteger("Update Rating", "Enter new rating:")
            if new_rating and self.validate_rating(new_rating):
                self.cursor.execute("UPDATE problems SET rating = ? WHERE id = ?", (new_rating, record_id))
                self.conn.commit()
                problem_id = records[selected[0]][3] if records[selected[0]][3] else "N/A"
                listbox.delete(selected[0])
                listbox.insert(selected[0], f"{record_id} | {record_date} | Rating: {new_rating} | Problem: {problem_id}")
                records[selected[0]] = (record_id, record_date, new_rating, records[selected[0]][3], records[selected[0]][4])
                if record_date == str(self.today):
                    self.update_today_score()
                logging.info(f"Updated record: id={record_id}, new_rating={new_rating}")

        def insert_record():
            date = simpledialog.askstring("Insert Record", "Enter date (YYYY-MM-DD):")
            rating = simpledialog.askinteger("Insert Record", "Enter rating:")
            problem_id = simpledialog.askstring("Insert Record", "Enter problem ID (optional):")
            if date and rating and self.validate_rating(rating) and self.validate_date(date):
                self.add_problem(date, rating, problem_id)
                load_all_records()  # Reload all records
                logging.info(f"Inserted record: date={date}, rating={rating}, problem_id={problem_id}")

        delete_button = tk.Button(button_frame, text="Delete", command=delete_selected)
        delete_button.pack(side=tk.LEFT, padx=5)

        update_button = tk.Button(button_frame, text="Update", command=update_selected)
        update_button.pack(side=tk.LEFT, padx=5)

        insert_button = tk.Button(button_frame, text="Insert", command=insert_record)
        insert_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = tk.Button(button_frame, text="Refresh", command=lambda: (records.clear(), records.extend(load_all_records())))
        refresh_button.pack(side=tk.LEFT, padx=5)

    def reset_database(self):
        """Reset the database after confirmation."""
        confirm = messagebox.askyesno("Confirm Reset", "Are you sure you want to reset the database? This will delete all records.")
        if confirm:
            self.cursor.execute("DELETE FROM problems")
            self.cursor.execute("DELETE FROM user_rating")
            self.cursor.execute("DELETE FROM user_info")
            self.cursor.execute("DELETE FROM sync_info")
            self.conn.commit()
            
            # Restart the application
            messagebox.showinfo("Info", "Database reset successfully. The application will now restart.")
            logging.info("Database reset.")
            self.root.destroy()
            self.__init__(tk.Tk())
            self.run()

    def show_help(self):
        """Display a help message in a customized window."""
        # Define the help text without extra indentation
        help_text = """Codeforces Progress Tracker Help:

    Hello bud, this widget tracks and scores your cf journey based on ppd*.
    Enter your cf handle, 'sync' will collect the data of all your 'accepted' questions.
    Your virtualised rating depicts the rating of problems 'just' above your level.
    Hence, enter your 'very short term rating goal' as your virtualised rating.

    Key Features:
    • Automatic submission syncing every 10 minutes
    • Full history sync/ Manual sync option
    • Manual problem entry (maybe if you're using a minor account)
    • Progress visualization
    • Record management (no shit sherlock)

    Scoring Formula:
    Daily score = (rating / base) ^ exponent
    • base = your rating + 100
    • exponent = 1 + (your rating / 2000)
    
    *ppd - personal problem difficulty represents how difficult the problem is to 'you' specifically based on your virtualised rating"""

        # Create a custom window
        help_window = tk.Toplevel(self.root)
        help_window.title("Help Guide")
        help_window.geometry("700x400")  # Wider window for better text flow

        # Set window colors
        help_window.configure(bg="#2E3440")  # Dark background

        # Create a frame for better organization
        main_frame = tk.Frame(help_window, bg="#2E3440")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Create a text widget with scrollbar
        text_frame = tk.Frame(main_frame, bg="#2E3440")
        text_frame.pack(fill=tk.BOTH, expand=True)

        text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 11),  # Modern, readable font
            fg="#EFF1F6",  # Light text color
            bg="#3B4252",  # Slightly lighter background
            padx=15,
            pady=15,
            insertbackground="#EFF1F6",  # Cursor color
            selectbackground="#4C566A",  # Selection color
            relief=tk.FLAT,
            borderwidth=0
        )

        # Insert the help text
        text.insert(tk.END, help_text)

        # Configure tags for different text styles
        text.tag_configure("title", font=("Segoe UI", 14, "bold"), foreground="#88C0D0")
        text.tag_configure("bullet", lmargin1=20, lmargin2=40)

        # Apply formatting
        text.tag_add("title", "1.0", "1.34")  # Format title
        text.config(state=tk.DISABLED)  # Make it read-only

        # Add scrollbar
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        text.config(yscrollcommand=scrollbar.set)

        # Layout with grid for better control
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Close button with modern style
        close_button = ttk.Button(
            main_frame,
            text="Close",
            command=help_window.destroy,
            style="Accent.TButton"  # Requires themed style
        )
        close_button.pack(pady=(15, 5))

        # Make the window resizable
        help_window.resizable(True, True)

    def validate_rating(self, rating):
        """Validate that the rating is within a reasonable range."""
        return 800 <= rating <= 3500

    def validate_date(self, date_str):
        """Validate that the date is in the correct format."""
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def run(self):
        """Run the application."""
        self.root.mainloop()
        self.conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = CodeforcesTracker(root)
    app.run()