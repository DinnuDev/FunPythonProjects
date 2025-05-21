# title: Web Scraper

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import datetime
import re
import os
import csv

# === Core Functions ===

def validate_url(url):
    return url.startswith("http://") or url.startswith("https://")

def fetch_url_content(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        start = time.perf_counter()
        response = requests.get(url, headers=headers, timeout=10)
        request_duration = time.perf_counter() - start
        response.raise_for_status()
        return response.text, request_duration, None
    except requests.RequestException as e:
        return None, None, str(e)

def parse_content(html, base_url):
    start = time.perf_counter()
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style']):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    links = [(a.get_text(strip=True), urljoin(base_url, a['href'])) for a in soup.find_all('a', href=True)]
    images = [urljoin(base_url, img['src']) for img in soup.find_all('img', src=True)]
    parse_duration = time.perf_counter() - start
    return text, links, images, parse_duration

def analyze_performance(text, links, images):
    words = re.findall(r'\b\w+\b', text)
    return {
        "word_count": len(words),
        "unique_links": len(set(href for _, href in links)),
        "unique_images": len(set(images))
    }

def generate_report(url, timestamp, timings, metrics, text, links, images, error=None):
    domain = urlparse(url).netloc.replace('.', '_')
    folder_path = os.path.join("scraped_data", domain)
    os.makedirs(folder_path, exist_ok=True)

    report_filename = os.path.join(folder_path, f"{domain}_report.md")
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(f"# Web Scraping Report\n\n")
        f.write(f"**Scraped URL:** {url}\n")
        f.write(f"**Timestamp:** {timestamp}\n\n")
        f.write(f"## Performance Metrics\n")
        f.write(f"- Total scraping time: {timings['total_time']:.3f} seconds\n")
        f.write(f"- HTTP request time: {timings['request_time']:.3f} seconds\n")
        f.write(f"- HTML parsing time: {timings['parse_time']:.3f} seconds\n\n")
        f.write(f"## Content Summary\n")
        f.write(f"- Word count: {metrics['word_count']}\n")
        f.write(f"- Unique links found: {metrics['unique_links']}\n")
        f.write(f"- Unique image URLs found: {metrics['unique_images']}\n\n")
        if error:
            f.write(f"## Errors\n- {error}\n")
        else:
            f.write(f"## Extracted Data Samples\n")
            f.write(f"### Text Snippet\n```\n{text[:500]}...\n```\n\n")
            f.write(f"### First 10 Links\n")
            for anchor, href in links[:10]:
                f.write(f"- [{anchor}]({href})\n")
            f.write(f"\n### First 10 Image URLs\n")
            for img in images[:10]:
                f.write(f"- {img}\n")

    with open(os.path.join(folder_path, "text.txt"), 'w', encoding='utf-8') as f:
        f.write(text)

    with open(os.path.join(folder_path, "links.csv"), 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Anchor Text", "URL"])
        writer.writerows(links)

    with open(os.path.join(folder_path, "images.txt"), 'w', encoding='utf-8') as f:
        for img_url in images:
            f.write(f"{img_url}\n")

    return report_filename

# === GUI Function ===

def run_scraper():
    url = url_entry.get().strip()
    if not validate_url(url):
        messagebox.showerror("Invalid URL", "Please enter a valid URL starting with http:// or https://")
        return

    results_box.delete("1.0", tk.END)
    start_time = time.perf_counter()
    html, request_time, fetch_error = fetch_url_content(url)

    if fetch_error:
        timings = {"total_time": 0, "request_time": 0, "parse_time": 0}
        metrics = {"word_count": 0, "unique_links": 0, "unique_images": 0}
        report_path = generate_report(url, datetime.datetime.now(), timings, metrics, "", [], [], fetch_error)
        results_box.insert(tk.END, f"❌ Error: {fetch_error}\n\n📄 Report saved to: {report_path}")
        return

    text, links, images, parse_time = parse_content(html, url)
    total_time = time.perf_counter() - start_time
    metrics = analyze_performance(text, links, images)
    timings = {"total_time": total_time, "request_time": request_time, "parse_time": parse_time}
    timestamp = datetime.datetime.now()
    report_path = generate_report(url, timestamp, timings, metrics, text, links, images)

    summary = (
        f"✅ Scraping Complete!\n\n"
        f"Scraped URL: {url}\n"
        f"Timestamp: {timestamp}\n\n"
        f"Total Time: {timings['total_time']:.2f}s\n"
        f"Request Time: {timings['request_time']:.2f}s\n"
        f"Parsing Time: {timings['parse_time']:.2f}s\n\n"
        f"Words: {metrics['word_count']}\n"
        f"Links Found: {metrics['unique_links']}\n"
        f"Images Found: {metrics['unique_images']}\n\n"
        f"📁 All data saved to folder: {os.path.dirname(report_path)}"
    )

    results_box.insert(tk.END, summary)

# === GUI Layout ===

app = tk.Tk()
app.title("Web Scraper")
app.geometry("720x520")
app.resizable(False, False)

style = ttk.Style(app)
style.theme_use('clam')
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("TEntry", font=("Segoe UI", 10))

frame = ttk.Frame(app, padding=20)
frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(frame, text="Enter URL:").grid(row=0, column=0, sticky=tk.W)
url_entry = ttk.Entry(frame, width=80)
url_entry.grid(row=0, column=1, padx=10, pady=5)

scrape_button = ttk.Button(frame, text="Start Scraping", command=run_scraper)
scrape_button.grid(row=0, column=2, padx=5)

results_box = scrolledtext.ScrolledText(frame, height=22, wrap=tk.WORD, font=("Consolas", 10))
results_box.grid(row=1, column=0, columnspan=3, pady=10)

app.mainloop()
