import tkinter as tk
from tkinter import messagebox
from bs4 import BeautifulSoup
import json
import nltk
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ZohoScraper:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Zoho CRM Scraper")
        self.root.geometry("600x400")

        # Browser selection
        tk.Label(self.root, text="Браузер:").pack(pady=5)
        self.browser_var = tk.StringVar(value="chrome")
        browser_frame = tk.Frame(self.root)
        browser_frame.pack(pady=2)
        tk.Radiobutton(
            browser_frame,
            text="Chrome",
            variable=self.browser_var,
            value="chrome"
        ).pack(side=tk.LEFT)

        # URL input
        tk.Label(self.root, text="URL для скрейпінгу:").pack(pady=5)
        self.url_entry = tk.Entry(self.root, width=50)
        self.url_entry.insert(0, "https://help.zoho.com/portal/en/kb/crm")
        self.url_entry.pack(pady=5)

        # Depth input
        tk.Label(self.root, text="Глибина скрейпінгу:").pack(pady=5)
        self.depth_entry = tk.Entry(self.root, width=10)
        self.depth_entry.insert(0, "1")
        self.depth_entry.pack(pady=5)

        # Start button
        button_config = {"text": "Почати", "command": self.start_scraping}
        self.start_button = tk.Button(self.root, **button_config)
        self.start_button.pack(pady=20)

        # Results
        self.results_text = tk.Text(self.root, height=10, width=50)
        self.results_text.pack(pady=10)

        self.visited_urls = set()
        self.knowledge_base = []

    def clean_text(self, text):
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def split_into_chunks(self, text, min_words=100, max_words=1000):
        words = text.split()
        chunks = []
        current_chunk = []
        current_count = 0

        for word in words:
            current_chunk.append(word)
            current_count += 1

            if current_count >= min_words:
                if current_count >= max_words or word.endswith('.'):
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_count = 0

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def get_html_selenium(self, url):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "portal.portalContainer.article_subcategory.crm"
                    )
                )
            )
        except Exception as e:
            print("Елемент не знайдено:", e)
        html = driver.page_source
        with open('page_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        driver.quit()
        return html

    def scrape_page(self, url, depth=1):
        if depth < 1 or url in self.visited_urls:
            return

        try:
            html = self.get_html_selenium(url)
            with open('debug.log', 'a', encoding='utf-8') as log:
                log.write(f"Selenium HTML отримано для {url}\n")
            soup = BeautifulSoup(html, 'html.parser')
            self.visited_urls.add(url)

            # Знаходимо всі розділи
            sections = []
            for module in soup.find_all(
                'div', class_='ModuleItem__moduleItem'
            ):
                title_tag = module.find(
                    'div', class_='ModuleItem__moduleTitle'
                )
                if title_tag and title_tag.a:
                    title = title_tag.a.get_text(strip=True)
                    link = title_tag.a['href']
                else:
                    title = ''
                    link = ''
                desc_tag = module.find(
                    'div', class_='ModuleItem__moduleDescription'
                )
                description = desc_tag.get_text(strip=True) if desc_tag else ''
                # Знаходимо кількість статей (опціонально)
                count_tag = module.find(
                    'span', class_='ModuleItem__moduleCount'
                )
                articles_count = (
                    count_tag.get_text(strip=True) if count_tag else ''
                )
                sections.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "articles_count": articles_count
                })
            self.knowledge_base.append({
                "url": url,
                "sections": sections
            })
        except Exception as e:
            error_msg = (f"Помилка при скрейпінгу {url}: "
                         f"{str(e)}\n")
            self.results_text.insert(tk.END, error_msg)

    def save_results(self):
        with open('knowledge_base.json', 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
        msg = "Результати збережено в knowledge_base.json\n"
        self.results_text.insert(tk.END, msg)

    def start_scraping(self):
        url = self.url_entry.get()
        try:
            depth = int(self.depth_entry.get())
        except ValueError:
            messagebox.showerror("Помилка", "Глибина має бути числом")
            return

        self.results_text.delete(1.0, tk.END)
        self.visited_urls.clear()
        self.knowledge_base.clear()

        self.results_text.insert(tk.END, "Початок скрейпінгу...\n")
        self.scrape_page(url, depth)
        self.save_results()
        self.results_text.insert(tk.END, "Скрейпінг завершено!\n")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    nltk.download('punkt')
    scraper = ZohoScraper()
    scraper.run()
    