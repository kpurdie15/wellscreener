# 🛢️ Appalachian Basin Oil & Gas Well Aggregator

A real-time Streamlit web application that scrapes, standardizes, and consolidates oil and gas well registry data across multiple state regulatory agencies (**Ohio, Pennsylvania, New York, West Virginia, and Kentucky**).

## 📌 Features

- **Multi-State API Integration:** Directly queries open GIS REST APIs (ArcGIS Server, Socrata) from ODNR, PA DEP, NYS DEC, WV DEP, and KGS.
- **Unified Data Schema:** Normalizes varied state columns into standard metrics (`State`, `Permit_ID`, `Operator`, `County`, `Type`, `Status`).
- **Interactive Filtering:** Dynamically filter records by state selection, operator/owner, or county.
- **Basin Analytics:** Real-time visual tallies, distribution charts, and printable permit tables.

---

## 🚀 Quickstart (Local Setup)

### Prerequisites
Make sure you have Python 3.9+ installed.

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
   cd YOUR_REPO_NAME
