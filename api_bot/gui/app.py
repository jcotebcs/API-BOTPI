import tkinter as tk
from tkinter import ttk, messagebox
from api_bot.core.discovery_bot import ComprehensiveAPIBot

class DesktopApp(tk.Tk):
    """Simple desktop GUI for the API Discovery Bot."""

    def __init__(self):
        super().__init__()
        self.title("API Discovery Bot")
        self.geometry("800x600")
        self.bot = ComprehensiveAPIBot()
        self._build_ui()

    def _build_ui(self):
        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", padx=10, pady=10)

        self.query_var = tk.StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.query_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.perform_search())

        ttk.Button(search_frame, text="Search", command=self.perform_search).pack(side="left", padx=5)

        self.results = tk.Text(self, wrap="word")
        self.results.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def perform_search(self):
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("API Discovery Bot", "Please enter search terms.")
            return
        try:
            results = self.bot.comprehensive_search(query)
            formatted = self.bot.format_search_results(results, query)
            self.results.delete("1.0", tk.END)
            self.results.insert(tk.END, formatted)
        except Exception as exc:
            messagebox.showerror("API Discovery Bot", str(exc))

def main():
    app = DesktopApp()
    app.mainloop()

if __name__ == "__main__":
    main()
