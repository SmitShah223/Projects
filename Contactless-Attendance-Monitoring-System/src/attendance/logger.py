"""
attendance/logger.py — CSV-based attendance logger.

Records:
  - candidate ID, name, entry timestamp, session date
  - Monthly report with: name, roll no, entry time, exit time, percentage
  - Marks ALL unrecognised enrolled candidates as ABSENT at session end
  - Sends email alert to administrator when candidates are absent

Output file: src/attendance/attendance.csv
  Columns: Date, CandidateID, Name, Status, EntryTime, ExitTime

Published: ICCDS February 2023 (ISBN: 979-8-9879839-0-4)
"""

import csv
import os
import sys
import smtplib
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ATTENDANCE_CSV, ATTENDANCE_DIR

CSV_HEADERS = ["Date", "CandidateID", "Name", "Status", "EntryTime", "ExitTime"]


class AttendanceLogger:
    """
    Logs attendance for a session and generates reports.
    """

    def __init__(self, session_date: date = None):
        self.session_date     = session_date or date.today()
        self.session_present  = {}   # candidate_id → {name, entry_time}
        self._ensure_csv()

    def _ensure_csv(self):
        """Create the CSV file with headers if it doesn't exist."""
        if not os.path.exists(ATTENDANCE_CSV):
            with open(ATTENDANCE_CSV, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()

    def mark_present(self, candidate_id: str, name: str) -> bool:
        """
        Mark a candidate as PRESENT for today's session.

        Returns:
            True  if newly marked (first time in this session)
            False if already marked
        """
        if candidate_id in self.session_present:
            return False   # already marked

        entry_time = datetime.now().strftime("%H:%M:%S")
        self.session_present[candidate_id] = {
            "name":       name,
            "entry_time": entry_time,
        }
        print(f"[LOG] ✅ PRESENT: {name} (ID: {candidate_id}) at {entry_time}")
        return True

    def close_session(self, all_enrolled_ids: set, all_label_names: dict):
        """
        Called at end of session:
          1. Writes PRESENT records to CSV
          2. Writes ABSENT records for all enrolled candidates not seen
          3. Returns list of absent candidates for email alert
        """
        exit_time = datetime.now().strftime("%H:%M:%S")
        absent_candidates = []

        rows = []
        for cid, data in self.session_present.items():
            rows.append({
                "Date":        str(self.session_date),
                "CandidateID": cid,
                "Name":        data["name"],
                "Status":      "PRESENT",
                "EntryTime":   data["entry_time"],
                "ExitTime":    exit_time,
            })

        for cid in all_enrolled_ids:
            if cid not in self.session_present:
                name = all_label_names.get(cid, f"ID_{cid}")
                rows.append({
                    "Date":        str(self.session_date),
                    "CandidateID": cid,
                    "Name":        name,
                    "Status":      "ABSENT",
                    "EntryTime":   "",
                    "ExitTime":    "",
                })
                absent_candidates.append(name)
                print(f"[LOG] ❌ ABSENT:  {name} (ID: {cid})")

        # Append to CSV
        with open(ATTENDANCE_CSV, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writerows(rows)

        print(f"[LOG] Session closed. {len(self.session_present)} present, "
              f"{len(absent_candidates)} absent.")
        return absent_candidates

    def generate_monthly_report(self, month: int = None, year: int = None) -> str:
        """
        Generate a monthly attendance report.

        Returns:
            Path to the saved report CSV file.
        """
        now   = datetime.now()
        month = month or now.month
        year  = year  or now.year

        # Read all records for the given month/year
        stats = defaultdict(lambda: {"name": "", "total": 0, "present": 0})

        with open(ATTENDANCE_CSV, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rec_date = date.fromisoformat(row["Date"])
                except ValueError:
                    continue
                if rec_date.month != month or rec_date.year != year:
                    continue

                cid = row["CandidateID"]
                stats[cid]["name"]  = row["Name"]
                stats[cid]["total"] += 1
                if row["Status"] == "PRESENT":
                    stats[cid]["present"] += 1

        # Write report
        report_path = os.path.join(
            ATTENDANCE_DIR, f"report_{year}_{month:02d}.csv"
        )
        report_headers = ["CandidateID", "Name", "TotalDays", "Present", "Absent", "Percentage"]
        with open(report_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=report_headers)
            writer.writeheader()
            for cid, data in sorted(stats.items()):
                pct = (data["present"] / data["total"] * 100) if data["total"] else 0
                writer.writerow({
                    "CandidateID": cid,
                    "Name":        data["name"],
                    "TotalDays":   data["total"],
                    "Present":     data["present"],
                    "Absent":      data["total"] - data["present"],
                    "Percentage":  f"{pct:.1f}%",
                })

        print(f"[LOG] Monthly report saved: {report_path}")
        return report_path

    @staticmethod
    def send_alert_email(
        absent_names: list,
        smtp_host: str,
        smtp_port: int,
        sender: str,
        password: str,
        recipient: str,
        session_date: date = None,
    ) -> bool:
        """
        Send an email alert to the administrator listing absent candidates.
        Returns True on success.
        """
        if not absent_names:
            return True

        session_date = session_date or date.today()
        subject = f"Attendance Alert — {len(absent_names)} absent on {session_date}"
        body    = (
            f"The following candidates were ABSENT on {session_date}:\n\n"
            + "\n".join(f"  • {name}" for name in absent_names)
            + "\n\nPlease review the attendance records."
        )

        msg = MIMEMultipart()
        msg["From"]    = sender
        msg["To"]      = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(sender, password)
                server.sendmail(sender, recipient, msg.as_string())
            print(f"[LOG] Email alert sent to {recipient}")
            return True
        except Exception as e:
            print(f"[LOG] Email failed: {e}")
            return False
