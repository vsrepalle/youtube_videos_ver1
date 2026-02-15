import customtkinter as ctk
import json
import threading
import typing_extensions as typing
from google import genai
from create_video import generate_video

# --- 1. DATA STRUCTURE (Ensures Keys never change) ---
class VideoEntry(typing.TypedDict):
    channel_id: str
    hook_text: str
    headline: str
    details: str
    search_key: str

# --- 2. SETUP ---
MODEL_NAME = 'gemini-2.5-flash' 
# Ensure your API Key is set in your environment or replace here
API_KEY = "AIzaSyBEN__vT3tOUs83xEOOl9gdomLI4QYdH7w"
client = genai.Client(api_key=API_KEY)

class YoutubeAutomationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gemini Auto-Channel 2026")
        self.geometry("600x620")
        ctk.set_appearance_mode("dark")

        # UI
        self.label = ctk.CTkLabel(self, text="One-Click Content Pipeline", font=("Arial", 24, "bold"))
        self.label.pack(pady=20)

        self.progress_label = ctk.CTkLabel(self, text="Ready to start...", font=("Arial", 14))
        self.progress_label.pack(pady=(10, 0))
        
        self.progress_bar = ctk.CTkProgressBar(self, width=480)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=15)

        self.status_box = ctk.CTkTextbox(self, width=520, height=280, font=("Consolas", 12))
        self.status_box.pack(pady=10)

        self.run_btn = ctk.CTkButton(self, text="START FULL AUTOMATION", 
                                     command=self.run_threaded_automation, 
                                     fg_color="#1f538d", height=45, font=("Arial", 16, "bold"))
        self.run_btn.pack(pady=20)

    def log(self, message):
        self.status_box.insert("end", f"> {message}\n")
        self.status_box.see("end")

    def update_ui(self, step, total, msg):
        fraction = step / total
        self.progress_bar.set(fraction)
        self.progress_label.configure(text=f"{msg} ({int(fraction*100)}%)")
        self.log(f"{msg}...")
        self.update_idletasks()

    def run_threaded_automation(self):
        self.run_btn.configure(state="disabled")
        threading.Thread(target=self.start_process, daemon=True).start()

    def start_process(self):
        try:
            # Stage 1: AI Fetching
            self.update_ui(1, 6, "Connecting to Gemini 2.5")
            
            prompt = """Provide JSON for 4 channels for Feb 15, 2026: 
            TrendWave Now (IND vs PAK Colombo Match), SpaceMind AI (Artemis 2 NASA update), 
            ExamPulse24_7 (UPSC riddle questions), WonderFacts24_7 (Triple Point of Water).
            Details MUST end with 'Tune with us for more such news.' 
            Search keys in 'Keyword | Context' format."""

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={'response_mime_type': 'application/json', 'response_schema': list[VideoEntry]},
            )
            
            data = response.parsed
            self.update_ui(2, 6, "JSON Data Received")

            # Stage 2: Processing (60% of total work)
            for i, entry in enumerate(data):
                channel = entry['channel_id']
                self.update_ui(i + 3, 6, f"Generating Video: {channel}")
                
                # Auto-save temp JSON for the specific channel
                temp_file = f"temp_{channel}.json"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump([entry], f)
                
                # Calls your video engine (Image fetching + Audio + Overlay)
                generate_video(temp_file)
                
            self.update_ui(6, 6, "Process Finished")
            self.log("✅ SUCCESS: All 4 channels updated (Private).")

        except Exception as e:
            self.log(f"❌ ERROR: {str(e)}")
        finally:
            self.run_btn.configure(state="normal")

if __name__ == "__main__":
    app = YoutubeAutomationApp()
    app.mainloop()