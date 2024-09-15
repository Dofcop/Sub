import signal
import sys
import textwrap
import threading
import tkinter as tk
from os import getenv
from queue import Queue
from dotenv import load_dotenv
from modules.audio_translate import translate_audio

load_dotenv()

OFFSET_X = int(getenv('OFFSET_X'))
OFFSET_Y = int(getenv('OFFSET_Y'))
SUBTITLE_FONT_SIZE = int(getenv('SUBTITLE_FONT_SIZE'))
SUBTITLE_COLOR = getenv('SUBTITLE_COLOR')
SUBTITLE_BG_COLOR = getenv('SUBTITLE_BG_COLOR')
SACRIFICIAL_COLOR = getenv('SACRIFICIAL_COLOR')


def subtitle_updater(root, queue, label):
    while not queue.empty():
        label.destroy()
        if root.wm_state() == 'withdrawn':
            root.deiconify()

        msg = queue.get()
        label = tk.Label(
            text=textwrap.fill(msg, 64),
            font=('Comic Sans MS', SUBTITLE_FONT_SIZE, 'bold italic'),
            fg=SUBTITLE_COLOR,
            bg=SUBTITLE_BG_COLOR
        )

        label.after(3000, root.withdraw)
        label.after(3000, label.destroy)

        label.pack(side='bottom', anchor='s')
        root.update_idletasks()

    root.after(50, lambda: subtitle_updater(root, queue, label))


def setup_overlay():
    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry(f'{root.winfo_screenwidth()}x{root.winfo_screenheight()}+{OFFSET_X}+{OFFSET_Y}')
    root.lift()
    root.wm_attributes('-topmost', True)
    root.wm_attributes('-disabled', True)

    root.wm_attributes('-transparentcolor', SACRIFICIAL_COLOR)
    root.config(bg=SACRIFICIAL_COLOR)

    root.withdraw()

    return root


def close_app(*_):
    print('Closing subtitler.')
    sys.exit(0)


def start_app():
    signal.signal(signal.SIGINT, close_app)

    overlay = setup_overlay()
    subtitle = tk.Label()
    subtitle_queue = Queue()

    threading.Thread(target=translate_audio, args=[subtitle_queue], daemon=True).start()

    subtitle_updater(overlay, subtitle_queue, subtitle)

    overlay.mainloop()


if __name__ == '__main__':
    start_app()
