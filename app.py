from flask import Flask, render_template
from icalendar import Calendar
from datetime import datetime, timedelta
from collections import defaultdict
import urllib.request

app = Flask(__name__)

def parse_ics(ics_data):
    cal = Calendar.from_ical(ics_data)
    events = []
    for component in cal.walk():
        if component.name == "VEVENT":
            event = {
                "date": component.get("dtstart").dt,
                "summary": component.get("summary"),
                "location": component.get("location"),
                "description": component.get("description"),
            }
            events.append(event)
    return events

def generate_yearly_calendar(year, events):
    months = []
    for month in range(1, 13):
        first_day = datetime(year, month, 1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        first_day_weekday = first_day.weekday()
        start_day = first_day - timedelta(days=first_day_weekday)

        weeks = []
        week = []
        current_day = start_day

        events_by_date = defaultdict(list)
        for event in events:
            event_date = event["date"].date() if isinstance(event["date"], datetime) else event["date"]
            if event_date.month == month:
                events_by_date[event_date].append(event)

        while current_day <= last_day or current_day.weekday() != 6:
            day_events = events_by_date.get(current_day.date(), [])
            week.append({
                "day": current_day.day if current_day.month == month else None,
                "date": current_day.date(),
                "events": day_events,
            })
            if current_day.weekday() == 6:
                weeks.append(week)
                week = []
            current_day += timedelta(days=1)

        months.append({
            "name": first_day.strftime("%B"),
            "year": year,
            "weeks": weeks,
        })
    return months

@app.route("/")
def index():
    ics_url = "https://calendar.google.com/calendar/ical/3b0cf5c3987b37ec7a28ba13677629e3d21b23c1c5b65e5a2250521ca3157b53%40group.calendar.google.com/private-7b9ec4075feb534a998aa9494a735161/basic.ics"
    with urllib.request.urlopen(ics_url) as response:
        ics_data = response.read()
    events = parse_ics(ics_data)
    year = datetime.now().year
    calendar_data = generate_yearly_calendar(year, events)
    return render_template("index.html", calendar=calendar_data)

# Vercel用のエントリーポイント
# 実際のVercelデプロイ時は、以下のコードを追加してください
# from vercel import app as vercel_app

if __name__ == "__main__":
    app.run(debug=True)
