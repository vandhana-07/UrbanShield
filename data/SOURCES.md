# Calibration Anchors & Sources for Synthetic Dataset Generation

This document lists the documented real-world meteorological, hydrological, and municipal figures used to calibrate the parameter ranges of UrbanShield's synthetic training dataset (`data/indian_flood_dataset.csv`). 

> **Important Disclosure**: UrbanShield's training data is **synthetically generated but calibrated** against these documented statistics. It is **not** raw governmental telemetry.

---

### 1. Mumbai (Mithi River & Kurla)
* **Anchor Event**: August 29, 2017 Mumbai Floods (and July 26, 2005 benchmark).
* **Rainfall Figure**: 468 mm in 12 hours recorded in Mumbai suburbs (highest single-day event between 1997 and 2017). Baseline monsoon rainfall calibrated to IMD Santacruz/Colaba seasonal normals (approx. 20–80 mm/day baseline during active monsoon).
* **Drainage & Topography**: Mithi River basin drainage bottleneck; low-lying Kurla basin with high tidal lock susceptibility.
* **Citations / References**:
  * Indian Meteorological Department (IMD) Mumbai Extreme Rainfall Archive.
  * Municipal Corporation of Greater Mumbai (MCGM) Disaster Management Cell Reports (2017 Floods).

---

### 2. Chennai (Velachery & Adyar)
* **Anchor Event**: November–December 2015 South Indian Floods (Chennai Inundation).
* **Rainfall Figure**: 494 mm in 24 hours (Dec 1, 2015), with active monsoon baseline daily rainfall of 15–70 mm.
* **Inundation & Infrastructure**: Inundation severity calibrated from open-source mapping of low-lying marshlands (Velachery lake encroachment, Adyar river basin overflow).
* **Citations / References**:
  * OpenCity.in Chennai Flooding Data & Inundation Map Catalogue: [https://opencity.in/](https://opencity.in/)
  * IMD Chennai Regional Meteorological Centre (RMC) Historical Weather Data.

---

### 3. Bengaluru (Silk Board & Bellandur)
* **Anchor Event**: September 2022 Bengaluru Urban Floods.
* **Rainfall Figure**: 131.6 mm in 24 hours (highest single-day rainfall in September in 8 years), with severe local storm bursts exceeding 80 mm/hr.
* **Drainage & Bottlenecks**: Stormwater drain encroachment in the Mahadevapura zone, Bellandur Lake catchment overflow, and Silk Board junction subgrade runoff.
* **Citations / References**:
  * Karnataka State Natural Disaster Monitoring Centre (KSNDMC) Urban Flood Reports (Sept 2022).
  * Bruhat Bengaluru Mahanagara Palike (BBMP) Stormwater Drain Audit.

---

### 4. Kolkata (MG Road & Central Corridor)
* **Anchor Event**: September 2021 Kolkata Monsoon Inundation.
* **Rainfall Figure**: 142 mm in a 6-hour convective deluge; monthly monsoon normal ~300–350 mm.
* **Drainage & Topography**: Heritage underground drainage system with slow outfall to the Hooghly River during high tide.
* **Citations / References**:
  * IMD Alipore Meteorological Office Monsoon Bulletins.
  * Kolkata Municipal Corporation (KMC) Drainage Pumping Station Telemetry Logs.

---

### 5. Delhi (Yamuna Floodplain & Central Lowlands)
* **Anchor Event**: July 2023 Delhi Yamuna River Inundation.
* **Rainfall Figure**: 153 mm in 24 hours (highest single-day July rainfall in 41 years); Yamuna River water level reached historic 208.66 meters.
* **Drainage & Bottlenecks**: Stormwater backflow at ITO, Minto Bridge underpass waterlogging, and floodplain encroachment.
* **Citations / References**:
  * Central Water Commission (CWC) Yamuna Hydrograph & Flood Bulletins (July 2023).
  * Delhi Disaster Management Authority (DDMA) Monsoon Contingency Plan.

---

### 6. Hyderabad (Musi River Basin & Begumpet)
* **Anchor Event**: October 2020 Hyderabad Urban Flash Floods.
* **Rainfall Figure**: 191.8 mm to 241 mm in 24 hours recorded across Greater Hyderabad (highest single-day October rain in over a century).
* **Drainage & Inundation**: Musi river carrying capacity breach, inundating low-lying residential clusters in Begumpet and Khairatabad.
* **Citations / References**:
  * Telangana State Development Planning Society (TSDPS) Weather Network Reports.
  * IMD Hyderabad Climatological Data.

---

### 7. Kochi (Aluva & Ernakulam City Center)
* **Anchor Event**: August 2018 & August 2019 Kerala Deluges.
* **Rainfall Figure**: Regional 24-hour rainfall exceeding 200–310 mm across Periyar River catchment; coastal monsoon baseline 30–90 mm.
* **Hydrology**: High groundwater table, coastal tidal fluctuations, and Periyar river spillway discharge.
* **Citations / References**:
  * Kerala State Disaster Management Authority (KSDMA) Flood Assessments (2018/2019).
  * CWC Southern Region Hydro-Meteorological Reports.
