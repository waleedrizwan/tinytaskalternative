# Tiny Macro

Alternative to [Tiny Task](https://tinytask.net/)
A single‑file Python tool to **record and replay mouse & keyboard input** on Windows. 
---

## Install & Run

```bash
pip install -r requirements.txt
python tiny_macro.py
```

## Hotkeys

| Action         | Key                       |
| -------------- | ------------------------- |
| Stop recording | **F7** or **Pause/Break** |
| Abort playback | **F8**                    |

## Files

* **tiny\_macro.py** – the app.
* **requirements.txt** – deps (`pynput`, `pyautogui`, `pillow`, `pywin32`).
* **macro.json** – last recording (auto‑created; delete anytime).