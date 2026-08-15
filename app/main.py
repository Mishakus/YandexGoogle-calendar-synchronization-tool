from fastapi import FastAPI, HTTPException, Response
import json
import httpx
from icalendar import Calendar, vText
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
CONFIG_PATH = os.getenv("CONFIG_PATH", "/data/config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def get_cal_info(cal_id: str):
    config = load_config()
    clean_id = cal_id.replace(".ics", "")
    
    if clean_id not in config:
        raise HTTPException(status_code=404, detail="Calendar not found")
    
    entry = config[clean_id]
    if isinstance(entry, dict):
        yandex_url = entry.get("url")
        cal_name = entry.get("name", "Yandex Calendar")
    else:
        yandex_url = entry
        cal_name = "Yandex Calendar"
        
    if yandex_url.startswith("webcal://"):
        yandex_url = "https://" + yandex_url[9:]
        
    return yandex_url, cal_name

@app.get("/cal/{cal_id}")
async def get_calendar(cal_id: str):
    yandex_url, cal_name = get_cal_info(cal_id)
    
    async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
        try:
            resp = await client.get(yandex_url)
            resp.raise_for_status()
            ical_data = resp.text
        except Exception as e:
            logger.error(f"Failed to fetch from Yandex: {e}")
            raise HTTPException(status_code=502, detail=f"Failed to fetch from Yandex: {e}")
            
    try:
        cal = Calendar.from_ical(ical_data)
        
        # Set calendar name
        cal["X-WR-CALNAME"] = vText(cal_name)
        
        event_count = 0
        modified_count = 0
        for component in cal.walk():
            if component.name == "VEVENT":
                event_count += 1
                if component.get("CLASS") in ["PRIVATE", "CONFIDENTIAL"]:
                    component["CLASS"] = vText("PUBLIC")
                    modified_count += 1
                    
        logger.info(f"Processed calendar {cal_id}: Found {event_count} events, modified CLASS for {modified_count} events.")
        modified_ical = cal.to_ical()
    except Exception as e:
        logger.error(f"Failed to parse iCal: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse iCal: {e}")
        
    return Response(content=modified_ical, media_type="text/calendar")
