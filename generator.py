import tkinter as tk
from tkinter import filedialog, messagebox
from bs4 import BeautifulSoup
import datetime
import os
import chardet

def detect_encoding(filepath):
    with open(filepath, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

class HTMLGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HTMLフォーム生成ツール")
        self.entries = {}

        self.placeholders = [
            ("ページタイトル", "Page Title"),
            ("カノニカルURL", "Canonical URL"),
            ("メタディスクリプション", "Meta Description"),
            ("OGディスクリプション", "OG Description"),
            ("ヘッドライン1", "Head Line1"),
            ("ヘッドライン2", "Head Line2"),
            ("ヘッドライン3", "Head Line3"),
            ("締切年", "Deadline year"),
            ("締切月", "Deadline month"),
            ("締切日", "Deadline day"),
            ("締切曜日", "Deadline weekday"),
            ("発送予定日", "Deliver date"),
            ("抽出年", "Extract year"),
            ("抽出月", "Extract month"),
            ("抽出日", "Extract day"),
            ("抽出曜日", "Extract weekday")
        ]

        self.headline_limit = len("描き下ろしイラスト使用アクリルスタンドが")

        for idx, (jp_label, key) in enumerate(self.placeholders):
            tk.Label(root, text=jp_label).grid(row=idx, column=0, sticky=tk.W, padx=5, pady=2)
            entry = tk.Entry(root, width=60)
            entry.grid(row=idx, column=1, padx=5, pady=2)
            self.entries[key] = entry
            if "Head Line" in key:
                entry.bind("<KeyRelease>", lambda e, k=key: self.enforce_length(e, k))

        tk.Button(root, text="第2HTMLファイルを選択", command=self.load_second_html).grid(row=len(self.placeholders), column=0, pady=10)
        tk.Button(root, text="HTML生成", command=self.generate_html).grid(row=len(self.placeholders), column=1, pady=10)

        self.second_html_path = None

    def enforce_length(self, event, key):
        entry = self.entries[key]
        value = entry.get()
        if len(value) > self.headline_limit:
            entry.delete(self.headline_limit, tk.END)
            messagebox.showwarning("制限超過", f"{key} は最大 {self.headline_limit} 文字までです。")

    def load_second_html(self):
        self.second_html_path = filedialog.askopenfilename(title="第2HTMLファイルを選択", filetypes=[("HTML files", "*.html")])
        if self.second_html_path:
            messagebox.showinfo("ファイル選択", f"{os.path.basename(self.second_html_path)} を読み込みました。")

    def generate_html(self):
        if not self.second_html_path:
            messagebox.showerror("エラー", "第2HTMLファイルを選択してください。")
            return

        with open("template.html", "r", encoding="utf-8") as f:
            template_soup = BeautifulSoup(f, "html.parser")

        encoding = detect_encoding(self.second_html_path)
        with open(self.second_html_path, "r", encoding=encoding, errors="ignore") as f:
            second_soup = BeautifulSoup(f, "html.parser")

        # Insert script tags from second HTML
        for script_tag in second_soup.find_all("script"):
            template_soup.head.append(script_tag)

        # Replace placeholders in template
        html_str = str(template_soup)
        for jp_label, key in self.placeholders:
            html_str = html_str.replace(f"【REPLACE: {key}】", self.entries[key].get())
        template_soup = BeautifulSoup(html_str, "html.parser")

        # Update form attributes (action and name)
        form_in_template = template_soup.find("form", {"class": "userSurvey__form"})
        form_in_second = second_soup.find("form")
        if form_in_template and form_in_second:
            if form_in_second.has_attr("action"):
                form_in_template["action"] = form_in_second["action"]
            if form_in_second.has_attr("name"):
                form_in_template["name"] = form_in_second["name"]
            if form_in_second.has_attr("onsubmit"):
                form_in_template["onsubmit"] = form_in_second["onsubmit"]

        # Replace radio inputs and labels
        second_radios = second_soup.find_all("input", {"type": "radio"})
        second_labels = second_soup.find_all("label")
        template_radios = form_in_template.find_all("input", {"type": "radio"})
        template_labels = form_in_template.find_all("label", {"class": "userSurvey__form-list-label01"})

        for new_input, new_label, old_input, old_label in zip(second_radios, second_labels, template_radios, template_labels):
            old_input["id"] = new_input.get("id", "")
            old_input["name"] = new_input.get("name", "")
            old_input["value"] = new_input.get("value", "")
            old_label["for"] = new_input.get("id", "")
            old_label.string = new_label.get_text(strip=True)

        # Replace textarea field with input type="text" from second HTML
        template_textarea = form_in_template.find("textarea", {"name": "answers[QUESTION_2_ID]"})
        second_input = second_soup.find("input", {"type": "text", "name": True})
        if template_textarea and second_input:
            template_textarea["name"] = second_input["name"]

        # Write to output HTML
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"output_{now}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(template_soup.prettify())

        messagebox.showinfo("成功", f"{output_file} を生成しました。")

if __name__ == "__main__":
    root = tk.Tk()
    app = HTMLGeneratorApp(root)
    root.mainloop()
