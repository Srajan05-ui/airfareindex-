# Aerofare: National Airfare Consumer Price Index (CPI) Monitoring System

**Smart India Hackathon (SIH) Problem Statement: SIH26056**
**Ministry:** Ministry of Statistics and Programme Implementation (MoSPI)

---

## 📖 The Problem
Currently, the Ministry of Statistics and Programme Implementation (MoSPI) calculates the Consumer Price Index (CPI) for airfares using manual data collection methods. This manual approach is:
- **Prone to human error**
- **Incapable of tracking dynamic pricing** (flight prices change multiple times a day)
- **Extremely time-consuming and unscalable**

MoSPI requires a smart, automated system that can monitor flight prices in real-time across various airlines and Online Travel Agencies (OTAs), process the data, detect outliers, and generate an accurate Airfare Index.

---

## 🚀 Our Solution: Aerofare
**Aerofare** is an end-to-end, automated intelligence platform that eliminates manual data entry. It dynamically scrapes flight data, cleans it using statistical models, and visualizes the Airfare Consumer Price Index on a real-time, interactive dashboard designed for government officials.

### Core Features of the Prototype:
1. **Smart Automation Engine:** A background pipeline powered by `APScheduler` that runs multiple times a day to fetch live flight data without any human intervention.
2. **Robust Data Pipeline:**
   - **Data Collection:** Automated scripts gathering live fares across major domestic routes (e.g., DEL-BOM, BOM-BLR).
   - **Data Cleaning:** Real-time anomaly detection drops statistical outliers (e.g., abnormally high last-minute business class fares) to prevent index skewing.
   - **Index Calculation:** Implements a fixed-basket **Laspeyres-style Index** algorithm to accurately calculate inflation/deflation on specific routes compared to a base period.
3. **Government-Grade Analytics Dashboard:**
   - **Real-time CPI Tracking:** Visualizes current index values against historical baselines.
   - **Geographical Heatmaps:** Interactive map showing critical inflation routes in red and stable routes in blue.
   - **Booking Window Analysis:** Tracks how prices surge as the departure date approaches (3-day vs 7-day vs 30-day advance bookings).

---

## 🛠️ Technology Stack (Prototype)
Our prototype is built using a modern, decoupled architecture ensuring high performance and ease of deployment.

**Backend (Data & API)**
- **Python 3.11:** Core language for data processing.
- **FastAPI:** High-performance REST API to serve data to the frontend.
- **PostgreSQL:** Relational database for storing raw observations and computed index values.
- **Pandas:** For heavy data manipulation and index calculation.
- **APScheduler / Subprocess:** For running background automation tasks.

**Frontend (Dashboard)**
- **React.js & Vite:** Lightning-fast frontend framework.
- **TailwindCSS:** For a premium, responsive, "Corporate Fintech" UI design (Slate, Royal Blue, Emerald, Red).
- **Recharts:** For rendering complex statistical graphs.
- **React-Leaflet:** For interactive geospatial mapping of flight routes.

---

## 🏗️ Future Production Architecture
While the prototype demonstrates the core functionality, the final production system is designed to scale nationwide across millions of daily queries:

1. **Distributed Scraping Farm:** Managed by **Kubernetes**, automatically scaling scraper pods during peak booking hours.
2. **Enterprise Proxies:** Integration with BrightData/Oxylabs to bypass advanced OTA bot protection.
3. **Message Queue (Apache Kafka):** Decouples scrapers from the database to ensure zero data loss during high-traffic ingestion.
4. **Data Warehouse (Google BigQuery):** Shifts complex CPI aggregations from the transactional database to an OLAP warehouse for instant analysis.
5. **Strict Security & Compliance:** AES-256 encryption, VPC isolation, and 100% Indian Data Localization to comply with government standards.

---

## ⚙️ How to Run the Prototype Locally

### 1. Start the Backend API
Navigate to the root project directory:
```bash
# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn api:app --reload --port 8000
```
*The API will be available at `http://localhost:8000/docs`*

### 2. Run the Automated Scraper
You can manually trigger the background scraper by hitting the live endpoint, or run the pipeline script directly:
```bash
python run_pipeline.py
```

### 3. Start the Frontend Dashboard
Open a new terminal and navigate to the `frontend` directory:
```bash
cd frontend

# Install Node modules
npm install

# Start the development server
npm run dev
```
*The Dashboard will be accessible at `http://localhost:5173`*

---
*Built with ❤️ for Smart India Hackathon 2024*
