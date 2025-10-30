from flask import Flask, render_template, request, jsonify
import icalendar
import requests
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)


def parse_ics(ics_url):
    """ICSファイルをパースしてイベント情報を抽出"""
    response = requests.get(ics_url)
    calendar = icalendar.Calendar.from_ical(response.text)
    events = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            start_dt = component.get("DTSTART").dt
            start = start_dt.date() if hasattr(start_dt, "date") else start_dt
            event = {
                "summary": str(component.get("SUMMARY")),
                "location": str(component.get("LOCATION")),
                "description": str(component.get("DESCRIPTION")),
                "start": start,
            }
            events.append(event)
    # 新しい順にソート
    events.sort(key=lambda x: x["start"], reverse=True)
    return events


def generate_yearly_calendar(year, events):
    """日付ごとのデータ構造を生成"""
    calendar_by_date = defaultdict(list)
    for event in events:
        calendar_by_date[event["start"]].append(event)

    # 月ごとにグループ化
    monthly_calendar = defaultdict(list)
    for date, event_list in calendar_by_date.items():
        month = date.month
        monthly_calendar[month].append(
            {
                "date": date,
                "events": event_list,
            }
        )

    # 月を降順にソート
    sorted_monthly_calendar = dict(sorted(monthly_calendar.items(), reverse=True))
    return sorted_monthly_calendar


@app.route("/")
def index():
    ics_url = "https://calendar.google.com/calendar/ical/3b0cf5c3987b37ec7a28ba13677629e3d21b23c1c5b65e5a2250521ca3157b53%40group.calendar.google.com/private-7b9ec4075feb534a998aa9494a735161/basic.ics"
    events = parse_ics(ics_url)
    yearly_calendar = generate_yearly_calendar(datetime.now().year, events)
    return render_template("index.html", yearly_calendar=yearly_calendar)


if __name__ == "__main__":
    app.run(debug=True)
