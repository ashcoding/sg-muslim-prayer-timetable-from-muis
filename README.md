<div align="center">

# Bismillahirrahmanirrahim
*In the name of Allah, the Most Gracious, the Most Merciful*

---
</div>

# 🕋 SG Muslim Prayer Timetable from MUIS (Home Assistant Custom Integration)

This directory contains **SG Muslim Prayer Timetable from MUIS**: a native Home Assistant custom integration that automates the tracking of accurate local prayer times in Singapore using open data.

---

## ✨ Features

- **Yearly Offline Caching:** Downloads the prayer times once from `data.gov.sg` and saves them locally grouped by year (`muslim_prayers_{year}.json` in HA `.storage`).
- **Config Flow UI:** Fully configurable via Settings -> Devices & Services. Users can input the custom collection ID (Default: `2312`).
- **Periodic Checks & Retry Logic:**
  - The coordinator runs a periodic background check every 2 hours to ensure the current year's data is loaded.
  - If a download attempt failed (e.g. internet down at startup or setup), it automatically retries every 2 hours until the data is successfully fetched and cached.
  - During November and December, it checks at most once a week for next year's schedule. Once the new dataset is found and cached locally, the network requests stop.
- **Graceful Rollover & Failure:** If a new year arrives and the schedule is still not published, the entities quietly report as `unavailable` with a custom state on the status sensor rather than crashing.

---

## 📂 Installation

1. Copy the `custom_components/sg_muslim_prayer_timetable_from_muis` folder to your Home Assistant's `/config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings > Devices & Services > Add Integration**.
4. Search for **"SG Muslim Prayer Timetable from MUIS"** and click add.
5. (Optional) Provide a custom dataset Resource ID or Collection ID, or leave it as default to use the pre-consolidated 2024-2026 data.

---

## 📡 Exposed Entities

- `sensor.sg_muis_subuh_prayer` (Timestamp: Next Subuh)
- `sensor.sg_muis_syuruk_prayer` (Timestamp: Next Syuruk)
- `sensor.sg_muis_zohor_prayer` (Timestamp: Next Zohor)
- `sensor.sg_muis_asar_prayer` (Timestamp: Next Asar)
- `sensor.sg_muis_maghrib_prayer` (Timestamp: Next Maghrib)
- `sensor.sg_muis_isyak_prayer` (Timestamp: Next Isyak)
- `sensor.sg_muis_last_sync` (Status sensor: `success`, `missing_schedule_data`, or `awaiting_next_year_schedule`)

---

## 🛠️ Development & Testing Workflow

If you want to edit and develop the integration locally on your PC and push it to your Home Assistant server:

1. **Deploying Updates:**
   Use Secure Copy (`scp`) to copy changes directly from your development directory to your Home Assistant server:
   ```powershell
   # Copy the entire directory
   scp -r "C:\path\to\your\custom_components\sg_muslim_prayer_timetable_from_muis" root@<YOUR_HA_IP>:/config/custom_components/
   ```
2. **Restarting Home Assistant:**
   Always restart Home Assistant via **Settings > System > Developer Tools > Restart** to reload any changes in python files.

---

## 🗑️ How to Uninstall & Clean Up

To cleanly remove a manual installation of this integration (e.g. before installing it via HACS):

1. **Remove from UI:** Go to **Settings > Devices & Services**, find **SG Muslim Prayer Timetable from MUIS**, click the **3 dots**, and click **Delete**.
2. **Remove Files:** SSH into your Home Assistant server and delete the custom component folder:
   ```bash
   rm -rf /config/custom_components/sg_muslim_prayer_timetable_from_muis
   ```
3. **Clean Cache:** Delete cached JSON timetables from the internal storage to ensure a clean slate:
   ```bash
   rm -f /config/.storage/muslim_prayers_*
   ```
4. **Restart:** Restart Home Assistant.

---

## 🤝 Credits & Acknowledgements

- This integration is only possible due to the public availability of the [Singapore Muslim Prayer Timetables Collection (2312) on data.gov.sg](https://data.gov.sg/collections/2312/view).
- Vibe coded with **Antigravity 2.91** using **Gemini 3.5 Flash** with directions from **ashcoding**.


