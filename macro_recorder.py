import json, threading, time, sys, tkinter as tk
from tkinter import messagebox
from pynput import mouse, keyboard

try:
    import pyautogui as pag
except Exception as e:
    sys.exit("PyAutoGUI missing →  pip install pyautogui pillow pywin32\n" + str(e))

ABORT_KEY    = 'f8'      # stop playback
STOP_REC_KEY = 'f7'   # stop recording (works on all PC keyboards)
SPEED = 1.0
MACRO_PATH = "macro.json"

# ───────────── globals ───────────────
recording, start_time = [], None
mouse_listener = kb_listener = None

# ───────────── helpers ───────────────
def ui(fn, *a, **k):      # Tk‑safe call from threads
    root.after(0, lambda: fn(*a, **k))

def key_name(key):
    """Translate pynput key → PyAutoGUI string."""
    if isinstance(key, keyboard.KeyCode):  # printable keys
        return key.char
    else:                                  # specials (Key.up, Key.shift, etc.)
        return key.name

def stamp(kind, data):
    if start_time is not None:
        recording.append((time.time() - start_time, kind, data))

# ────────── listener callbacks ───────
def on_mouse_move(x, y):                 stamp('move',   (x, y))
def on_mouse_click(x, y, btn, pressed):  stamp('click',  (x, y, btn.name, pressed))
def on_mouse_scroll(x, y, dx, dy):       stamp('scroll', (x, y, dx, dy))

def on_key_press(key):
    name = key_name(key)
    if name == STOP_REC_KEY and start_time is not None:
        ui(stop_recording); return
    stamp('key', (name, True))

def on_key_release(key):
    name = key_name(key)
    if name == STOP_REC_KEY and start_time is not None: return
    stamp('key', (name, False))

# ────────── recording control ────────
def start_recording():
    global recording, start_time, mouse_listener, kb_listener
    if mouse_listener: return
    recording, start_time = [], time.time()

    mouse_listener = mouse.Listener(on_move=on_mouse_move,
                                    on_click=on_mouse_click,
                                    on_scroll=on_mouse_scroll)
    kb_listener    = keyboard.Listener(on_press=on_key_press,
                                       on_release=on_key_release)
    mouse_listener.start(); kb_listener.start()
    record_btn.config(state=tk.DISABLED); stop_btn.config(state=tk.NORMAL)
    status_var.set("Recording…  (Pause key to stop)")
    print("Recording started")

def stop_recording():
    global mouse_listener, kb_listener, start_time
    if not mouse_listener: return
    mouse_listener.stop(); kb_listener.stop()
    mouse_listener = kb_listener = None;  start_time = None
    with open(MACRO_PATH, "w", encoding="utf-8") as f: json.dump(recording, f)
    record_btn.config(state=tk.NORMAL)
    stop_btn.config(state=tk.DISABLED); play_btn.config(state=tk.NORMAL)
    status_var.set(f"Saved {len(recording)} events → {MACRO_PATH}")
    print("Recording stopped – total events:", len(recording))

# ───────────── playback ──────────────
def play_macro():
    try:
        with open(MACRO_PATH, "r", encoding="utf-8") as f:
            events = json.load(f)
    except FileNotFoundError:
        messagebox.showerror("No recording", "macro.json not found – record first."); return

    play_btn.config(state=tk.DISABLED); status_var.set("Playing…  (F8 abort)")

    def _play():
        abort = threading.Event()
        def _abort_listener():
            with keyboard.Listener(on_press=lambda k: abort.set()
                                   if key_name(k)==ABORT_KEY else None): pass
        threading.Thread(target=_abort_listener, daemon=True).start()

        prev_xy, t0 = None, time.time()
        for dt, kind, data in events:
            if abort.is_set(): break
            time.sleep(max(0, dt/SPEED - (time.time()-t0)))

            if kind == 'move':
                x, y = data
                if (x, y) != prev_xy:
                    pag.moveTo(x, y, _pause=False); prev_xy=(x, y)

            elif kind == 'click':
                x, y, btn, pressed = data
                pag.moveTo(x, y, _pause=False)
                (pag.mouseDown if pressed else pag.mouseUp)(button=btn)

            elif kind == 'scroll':
                x, y, dx, dy = data
                pag.moveTo(x, y, _pause=False)
                if dy: pag.scroll(dy, x=x, y=y)
                if dx: pag.hscroll(dx)

            elif kind == 'key':
                k, pressed = data
                (pag.keyDown if pressed else pag.keyUp)(k)

        ui(play_btn.config, state=tk.NORMAL)
        ui(status_var.set, "Ready")
        print("Playback done")

    threading.Thread(target=_play, daemon=True).start()

# ───────────── GUI ───────────────────
root = tk.Tk(); root.title("Tiny Macro")

record_btn = tk.Button(root, text="⏺ Record", width=12, command=start_recording)
stop_btn   = tk.Button(root, text="⏹ Stop",   width=12, command=stop_recording, state=tk.DISABLED)
play_btn   = tk.Button(root, text="▶ Play",   width=12, command=play_macro,    state=tk.DISABLED)
exit_btn   = tk.Button(root, text="✖ Exit",   width=12, command=root.quit)

for i, btn in enumerate((record_btn, stop_btn, play_btn, exit_btn)):
    btn.grid(row=0, column=i, padx=5, pady=5)

status_var = tk.StringVar(value="Ready")
tk.Label(root, textvariable=status_var, anchor="w").grid(
    row=1, column=0, columnspan=4, sticky="we", padx=5
)

root.mainloop()
