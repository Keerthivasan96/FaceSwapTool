import os
import sys
import cv2
import numpy as np
from tkinter import Tk, Label, filedialog
from tkinter import ttk, Entry
from PIL import Image, ImageTk
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model

# ========= Helper to get correct path in both .py and PyInstaller EXE =========
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):  # Running in PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# ========= Unique output path helper =========
def get_unique_output_path(base_dir, base_name="swapped_output", ext=".mp4"):
    counter = 1
    while True:
        candidate = os.path.join(base_dir, f"{base_name}_{counter}{ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1

class FaceSwapApp:
    def __init__(self, master):
        self.master = master
        master.title("🎭 Face Swap Video Tool")
        master.geometry("520x520")

        # Use ttk (modern styled widgets)
        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 11), padding=6)
        style.configure("TLabel", font=("Segoe UI", 11))

        self.label = ttk.Label(master, text="Select video and target image:")
        self.label.pack(pady=10)

        self.video_button = ttk.Button(master, text="🎥 Choose Video", command=self.load_video)
        self.video_button.pack(pady=5)

        self.image_button = ttk.Button(master, text="🖼 Choose Target Image", command=self.load_image)
        self.image_button.pack(pady=5)

        # Custom output name entry
        self.output_label = ttk.Label(master, text="📁 Output name (optional, no extension):")
        self.output_label.pack(pady=5)
        self.output_entry = Entry(master, width=30)
        self.output_entry.pack(pady=5)

        self.run_button = ttk.Button(master, text="⚡ Run Face Swap", command=self.run_face_swap)
        self.run_button.pack(pady=10)

        # Image preview area
        self.preview_label = Label(master)
        self.preview_label.pack(pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(master, orient="horizontal", length=350, mode="determinate")
        self.progress.pack(pady=10)

        # Status text
        self.status_label = ttk.Label(master, text="Waiting for input...")
        self.status_label.pack(pady=5)

        self.video_path = ""
        self.image_path = ""
        self.preview_image = None  # keep reference

    def load_video(self):
        path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
        )
        if path:
            self.video_path = path
            self.status_label.config(text=f"✅ Video: {os.path.basename(path)}")

    def load_image(self):
        path = filedialog.askopenfilename(
            title="Select Target Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if path:
            self.image_path = path
            # Show preview safely
            img = Image.open(self.image_path)
            img.thumbnail((200, 200))
            self.preview_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.preview_image)
            self.status_label.config(text=f"✅ Image: {os.path.basename(path)}")

    def run_face_swap(self):
        if not self.video_path or not self.image_path:
            self.status_label.config(text="❌ Please select both video and image.")
            return

        self.status_label.config(text="⏳ Processing...")
        self.progress["value"] = 0
        self.master.update_idletasks()

        try:
            # Load target image
            target_img = cv2.imread(self.image_path)
            if target_img is None:
                self.status_label.config(text="❌ Failed to load target image.")
                return

            # Face analysis
            model_dir = resource_path("models")
            face_analyser = FaceAnalysis(name='buffalo_l', root=model_dir, providers=["CPUExecutionProvider"])
            face_analyser.prepare(ctx_id=0, det_size=(640, 640))
            target_faces = face_analyser.get(target_img)

            if not target_faces:
                self.status_label.config(text="❌ No face found in target image.")
                return
            target_face = target_faces[0]

            # Load swapper model
            swapper_path = resource_path(os.path.join("models", "inswapper_128.onnx"))
            if not os.path.exists(swapper_path):
                self.status_label.config(text="❌ inswapper_128.onnx not found in models/.")
                return
            swapper = get_model(swapper_path, providers=["CPUExecutionProvider"])

            # Video setup
            cap = cv2.VideoCapture(self.video_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            output_dir = resource_path("output")
            os.makedirs(output_dir, exist_ok=True)

            # Decide filename based on entry
            user_name = self.output_entry.get().strip()
            if user_name:
                output_path = os.path.join(output_dir, f"{user_name}.mp4")
                if os.path.exists(output_path):  # fallback to unique
                    output_path = get_unique_output_path(output_dir, base_name=user_name)
            else:
                output_path = get_unique_output_path(output_dir)

            out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                faces = face_analyser.get(frame)
                for face in faces:
                    try:
                        frame = swapper.get(frame, face, target_face, paste_back=True)
                    except Exception as e:
                        print(f"Face swap error at frame {frame_count}: {e}")
                out.write(frame)

                frame_count += 1
                if total_frames > 0:
                    self.progress["value"] = (frame_count / total_frames) * 100
                    self.master.update_idletasks()

            cap.release()
            out.release()

            self.status_label.config(text=f"✅ Done! Output saved: {output_path}")

            # Open output folder button
            open_btn = ttk.Button(self.master, text="📂 Open Output Folder", command=lambda: os.startfile(output_dir))
            open_btn.pack(pady=5)

        except Exception as e:
            self.status_label.config(text=f"❌ Error: {e}")

# === Run GUI ===
if __name__ == "__main__":
    root = Tk()
    app = FaceSwapApp(root)
    root.mainloop()
