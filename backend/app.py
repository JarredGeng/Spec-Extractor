from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import re
import sqlite3
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import os
import io
import xlsxwriter

# === Setup ===
app = Flask(__name__)
CORS(app)

DB_FILE = "specs.db"

# === DB Init ===
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chassis_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            model_name TEXT,
            date_scraped TEXT,
            cpu_socket TEXT,
            cpu_count TEXT,
            max_tdp TEXT,
            total_tdp TEXT,
            memory_type TEXT,
            dimm_slots TEXT,
            power_supply TEXT,
            rack_unit TEXT,
            drive_bays TEXT,
            m2_slots TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# === Scraping Logic ===
def extract_visible_specs(url):
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        text = driver.find_element(By.TAG_NAME, "body").text
    finally:
        driver.quit()

    return text

def parse_spec_text(text):
    summary = {}
    cpu_count = 1
    max_tdp = None

    socket_match = re.search(r"(LGA\s*\d{4})(.*?Socket\s*\w+)?", text, re.IGNORECASE)
    if socket_match:
        socket_str = socket_match.group(1)
        if socket_match.group(2):
            socket_str += " " + socket_match.group(2).strip()
        summary["CPU Socket"] = socket_str.strip()

    tdp_match = re.search(r"(\d{2,4})\s*[wW].*?TDP", text, re.IGNORECASE)
    if not tdp_match:
        tdp_match = re.search(r"TDP.*?(\d{2,4})\s*[wW]", text, re.IGNORECASE)
    if tdp_match:
        max_tdp = int(tdp_match.group(1))
        summary["Max TDP"] = f"{max_tdp}W"

    cpu_count_match = re.search(r"(single|dual|quad|2|4)[-\s]*(processor|cpu)", text, re.IGNORECASE)
    if cpu_count_match:
        val = cpu_count_match.group(1).lower()
        if val in ["dual", "2"]:
            cpu_count = 2
        elif val in ["quad", "4"]:
            cpu_count = 4
    summary["CPU Count"] = str(cpu_count)
    if max_tdp:
        summary["Total TDP"] = f"{max_tdp * cpu_count}W"

    mem_match = re.search(r"(ddr[345][^\n]*)", text, re.IGNORECASE)
    if mem_match:
        summary["Memory Type"] = mem_match.group(1)

    dimm_match = re.search(r"(\d+)\s*x\s*dimm", text, re.IGNORECASE)
    if dimm_match:
        summary["DIMM Slots"] = dimm_match.group(1)

    psu_match = re.search(r"(\d+)\s*x\s*(\d{3,4})\s*w", text, re.IGNORECASE)
    if psu_match:
        count = int(psu_match.group(1))
        watts = psu_match.group(2)
        summary["Power Supply"] = f"{count} x {watts}W"

    rack_match = re.search(r"\b([1-8][Uu])\b", text)
    if rack_match:
        summary["Rack Unit"] = rack_match.group(1).upper()

    bay_match = re.search(r"(\d+)\s*x\s*2.5.*?(nvme|sata)", text, re.IGNORECASE)
    if bay_match:
        summary["2.5\" Drive Bays"] = bay_match.group(1)

    m2_matches = re.findall(r"\d+\s*x\s*M\.2[^\n]*", text, re.IGNORECASE)
    if m2_matches:
        summary["M.2 Slots"] = f"{len(m2_matches)} detected"

    return summary

def save_to_db(url, model_name, summary):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chassis_specs WHERE url = ?", (url,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return False
    cursor.execute("""
        INSERT INTO chassis_specs (
            url, model_name, date_scraped, cpu_socket, cpu_count, max_tdp, total_tdp,
            memory_type, dimm_slots, power_supply, rack_unit, drive_bays, m2_slots
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        url, model_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        summary.get("CPU Socket"), summary.get("CPU Count"), summary.get("Max TDP"), summary.get("Total TDP"),
        summary.get("Memory Type"), summary.get("DIMM Slots"), summary.get("Power Supply"),
        summary.get("Rack Unit"), summary.get("2.5\" Drive Bays"), summary.get("M.2 Slots")
    ))
    conn.commit()
    conn.close()
    return True

# === API Routes ===
@app.route("/api/specs", methods=["POST"])
def get_specs():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    model_match = re.search(r"/([^/#]+)(?:#|$)", url)
    model_name = model_match.group(1) if model_match else "Unknown"

    try:
        raw_text = extract_visible_specs(url)
        summary = parse_spec_text(raw_text)
        saved = save_to_db(url, model_name, summary)
        return jsonify({"Model": model_name, "Saved": "✅ Yes" if saved else "❌ No", **summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/database", methods=["GET"])
def get_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT model_name, date_scraped, url FROM chassis_specs")
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "Model": row[0],
            "Date Scraped": row[1],
            "URL": row[2]
        })

    return jsonify(result)

@app.route("/api/download/<model>", methods=["GET"])
def download_model(model):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chassis_specs WHERE model_name = ?", (model,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Model not found"}), 404

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    sheet = workbook.add_worksheet()

    headers = ["Model", "URL", "Date Scraped", "CPU Socket", "CPU Count", "Max TDP", "Total TDP",
               "Memory Type", "DIMM Slots", "Power Supply", "Rack Unit", "Drive Bays", "M.2 Slots"]
    values = [row[2], row[1], row[3], row[4], row[5], row[6], row[7],
              row[8], row[9], row[10], row[11], row[12], row[13]]

    for i, (h, v) in enumerate(zip(headers, values)):
        sheet.write(i, 0, h)
        sheet.write(i, 1, v)

    workbook.close()
    output.seek(0)

    return send_file(output, download_name=f"{model}.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route("/api/delete/<model>", methods=["DELETE"])
def delete_model(model):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chassis_specs WHERE model_name = ?", (model,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

@app.route("/api/download-all", methods=["GET"])
def download_all():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chassis_specs")
    rows = cursor.fetchall()
    conn.close()

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    sheet = workbook.add_worksheet()

    headers = ["Model", "URL", "Date Scraped", "CPU Socket", "CPU Count", "Max TDP", "Total TDP",
               "Memory Type", "DIMM Slots", "Power Supply", "Rack Unit", "Drive Bays", "M.2 Slots"]

    for col, h in enumerate(headers):
        sheet.write(0, col, h)

    for row_idx, row in enumerate(rows, start=1):
        values = [row[2], row[1], row[3], row[4], row[5], row[6], row[7],
                  row[8], row[9], row[10], row[11], row[12], row[13]]
        for col, v in enumerate(values):
            sheet.write(row_idx, col, v)

    workbook.close()
    output.seek(0)

    return send_file(output, download_name="All_Chassis_Specs.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
