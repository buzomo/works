from flask import Flask, render_template
import icalendar
import requests
from datetime import datetime
from collections import defaultdict
import re

app = Flask(__name__)


def parse_ics(ics_url):
    """ICSファイルをパースしてイベント情報を抽出し、タグ整理も同時に行う"""
    response = requests.get(ics_url, timeout=10)
    calendar = icalendar.Calendar.from_ical(response.text)
    events = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            start_dt = component.get("DTSTART").dt
            start = start_dt.date() if hasattr(start_dt, "date") else start_dt
            raw_description = str(component.get("DESCRIPTION"))
            description_lines = raw_description.splitlines()
            tags = []
            filtered_lines = []
            screenshot_url = None
            for line in description_lines:
                stripped = line.lstrip()
                if stripped.startswith("#"):  # 空白許容
                    tags.extend(
                        [t.strip() for t in line.strip().split("#") if t.strip()]
                    )
                    continue
                # Gyazoリンク検出（@有無どちらも許容、行内どこでも）
                m = re.search(r"@?https://gyazo\.com/([A-Za-z0-9]+)", line)
                if m and not screenshot_url:
                    gyazo_id = m.group(1)
                    screenshot_url = f"https://i.gyazo.com/{gyazo_id}.png"
                    # この行は説明に含めない
                    continue
                filtered_lines.append(line)
            event = {
                "summary": str(component.get("SUMMARY")),
                "location": str(component.get("LOCATION")),
                "description": "\n".join(filtered_lines).strip(),
                "start": start,
                "tags": tags,
                "screenshot_url": screenshot_url,
            }
            events.append(event)
    events.sort(key=lambda x: x["start"], reverse=True)
    return events


def generate_yearly_calendar(year, events):
    """日付ごとのデータ構造を生成 + 月ごとのイベント個数も同時に計算"""
    calendar_by_date = defaultdict(list)
    for event in events:
        calendar_by_date[event["start"]].append(event)

    # 月ごとにグループ化
    monthly_calendar = defaultdict(list)
    monthly_counts = defaultdict(int)
    for date, event_list in calendar_by_date.items():
        month = date.month
        monthly_calendar[month].append(
            {
                "date": date,
                "events": event_list,
            }
        )
        monthly_counts[month] += len(event_list)

    # 月を降順にソート
    sorted_monthly_calendar = dict(sorted(monthly_calendar.items(), reverse=True))
    sorted_monthly_counts = dict(sorted(monthly_counts.items(), reverse=True))
    return sorted_monthly_calendar, sorted_monthly_counts


@app.route("/")
def index():
    ics_url = "https://calendar.google.com/calendar/ical/3b0cf5c3987b37ec7a28ba13677629e3d21b23c1c5b65e5a2250521ca3157b53%40group.calendar.google.com/private-7b9ec4075feb534a998aa9494a735161/basic.ics"
    events = parse_ics(ics_url)
    yearly_calendar, monthly_counts = generate_yearly_calendar(
        datetime.now().year, events
    )

    # タグの頻度集計
    tag_freq = defaultdict(int)
    for event in events:
        for t in event.get("tags", []):
            tag_freq[t] += 1
    sorted_tags = sorted(tag_freq.items(), key=lambda x: (-x[1], x[0]))

    # タグ名 -> インラインスタイル（重複しないパステルカラー）
    tag_styles = {}
    n_tags = len(sorted_tags) if sorted_tags else 1
    for i, (tag, _cnt) in enumerate(sorted_tags):
        hue = int(round(360 * i / n_tags)) % 360
        bg = f"hsl({hue}, 70%, 90%)"
        fg = f"hsl({hue}, 35%, 30%)"
        tag_styles[tag] = f"background: {bg}; color: {fg};"

    # タグ名 -> カラークラス番号(1..5)の決定的マッピング
    def color_index_for_tag(tag: str) -> int:
        return (sum(ord(c) for c in tag) % 5) + 1

    tag_color_index = {tag: color_index_for_tag(tag) for tag, _ in sorted_tags}

    return render_template(
        "index.html",
        yearly_calendar=yearly_calendar,
        monthly_counts=monthly_counts,
        tags=sorted_tags,
        events=events,
        tag_color_index=tag_color_index,
        tag_styles=tag_styles,
    )


if __name__ == "__main__":
    app.run(debug=True)
