import time
import threading
import requests
import solara
import pyttsx3

API_BASE = "http://127.0.0.1:8000"
POLL_INTERVAL = 3
CAMERA_TIMEOUT = 20

faces_detected = solara.reactive(0)
brightness_set = solara.reactive(-1)
status = solara.reactive("idle")
last_checked = solara.reactive("")
auto_monitor = solara.reactive(False)
loading = solara.reactive(False)
error_msg = solara.reactive("")

_monitor_thread = None
_stop_event = threading.Event()

ann_message = solara.reactive(
    "Time is up for the current group. Next group please proceed to the practical exam area."
)
ann_delay_min = solara.reactive(15)
ann_status = solara.reactive("idle")        
ann_remaining = solara.reactive("")         
ann_history = solara.reactive([])         

_ann_thread = None
_ann_stop = threading.Event()

active_tab = solara.reactive(0)


def _fetch_faces():
    """Call the backend once and update reactive state."""
    loading.set(True)
    error_msg.set("")
    try:
        resp = requests.get(f"{API_BASE}/check-faces", timeout=CAMERA_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            status.set("error")
            error_msg.set(data["error"])
        else:
            fc = data.get("faces_detected", 0)
            br = data.get("brightness_set", 0)
            faces_detected.set(fc)
            brightness_set.set(br)
            status.set("active" if fc >= 1 else "idle")
            last_checked.set(time.strftime("%H:%M:%S"))

    except requests.exceptions.ConnectionError:
        status.set("error")
        error_msg.set("Cannot reach API - is the backend running on port 8000?")
    except Exception as exc:
        status.set("error")
        error_msg.set(str(exc))
    finally:
        loading.set(False)


def _monitor_loop(stop):
    while not stop.is_set():
        _fetch_faces()
        stop.wait(POLL_INTERVAL)


def _start_monitor():
    global _monitor_thread, _stop_event
    _stop_event = threading.Event()
    _monitor_thread = threading.Thread(
        target=_monitor_loop, args=(_stop_event,), daemon=True
    )
    _monitor_thread.start()


def _stop_monitor():
    global _monitor_thread
    _stop_event.set()
    if _monitor_thread:
        _monitor_thread.join(timeout=2)
        _monitor_thread = None


def toggle_auto_monitor(value):
    auto_monitor.set(value)
    if value:
        _start_monitor()
    else:
        _stop_monitor()


def _speak(text):
    """Speak the given text using pyttsx3."""
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception:
        pass  


def _announcement_worker(message, delay_seconds, stop_event):
    """Background thread: count down, then speak."""
    ann_status.set("waiting")
    target = time.time() + delay_seconds

    while not stop_event.is_set():
        remaining = target - time.time()
        if remaining <= 0:
            break
        mins, secs = divmod(int(remaining), 60)
        ann_remaining.set(f"{mins:02d}:{secs:02d}")
        stop_event.wait(1)

    if stop_event.is_set():
        ann_status.set("idle")
        ann_remaining.set("")
        return

    # Time to speak
    ann_status.set("speaking")
    ann_remaining.set("00:00")
    _speak(message)

    # Record in history
    entry = f"[{time.strftime('%H:%M:%S')}]  {message[:80]}{'…' if len(message) > 80 else ''}"
    ann_history.set(ann_history.value + [entry])

    ann_status.set("done")
    ann_remaining.set("")


def schedule_announcement():
    global _ann_thread, _ann_stop
    if ann_status.value == "waiting":
        return  
    _ann_stop = threading.Event()
    delay = max(0.1, ann_delay_min.value) * 60
    _ann_thread = threading.Thread(
        target=_announcement_worker,
        args=(ann_message.value, delay, _ann_stop),
        daemon=True,
    )
    _ann_thread.start()


def cancel_announcement():
    global _ann_thread
    _ann_stop.set()
    if _ann_thread:
        _ann_thread.join(timeout=2)
        _ann_thread = None
    ann_status.set("idle")
    ann_remaining.set("")


@solara.component
def StatusBadge():
    s = status.value

    labels = {"active": "Face Detected", "idle": "No Face", "error": "Error"}
    colors = {"active": "#4fc3f7", "idle": "#90caf9", "error": "#ef5350"}
    backs  = {"active": "#102027",  "idle": "#1c313a",  "error": "#3e2723"}
    dots   = {"active": "#03a9f4",  "idle": "#81d4fa",  "error": "#e53935"}

    label = labels.get(s, "Unknown")
    color = colors.get(s, "#4fc3f7")
    bg    = backs.get(s, "#102027")
    dot   = dots.get(s, "#03a9f4")

    with solara.v.Html(
        tag="span",
        style_=(
            f"display:inline-flex;align-items:center;gap:7px;"
            f"padding:4px 13px;border-radius:20px;"
            f"font-size:13px;font-weight:600;letter-spacing:0.3px;"
            f"color:{color};background:{bg};border:1px solid {color}44;"
        ),
    ):
        solara.v.Html(
            tag="span",
            style_=(
                f"width:8px;height:8px;border-radius:50%;"
                f"background:{dot};flex-shrink:0;"
            ),
            children=[],
        )
        solara.v.Html(tag="span", children=[label], style_="")


@solara.component
def BrightnessBar():
    br = brightness_set.value
    if br < 0:
        return

    pct  = max(0, min(100, br))
    fill = "#03a9f4" if pct > 0 else "#37474f"
    lbl  = f"{pct}%" if pct > 0 else "Off (0%)"

    with solara.Column(style={"gap": "6px"}):
        solara.Text(
            "Brightness level",
            style={
                "font-size": "11px",
                "color": "#81d4fa",
                "font-weight": "600",
                "text-transform": "uppercase",
                "letter-spacing": "0.8px",
            },
        )
        with solara.v.Html(
            tag="div",
            style_="background:#1c313a;border-radius:6px;height:14px;width:100%;overflow:hidden",
        ):
            solara.v.Html(
                tag="div",
                style_=(
                    f"background:{fill};width:{pct}%;height:100%;"
                    f"border-radius:6px;transition:width 0.5s ease;"
                ),
                children=[],
            )
        solara.Text(
            lbl,
            style={"font-size": "14px", "color": "#e1f5fe", "font-weight": "700"},
        )
        
@solara.component
def StatCard(title, value, sub=""):
    with solara.v.Html(
        tag="div",
        style_=(
            "background:#102027;border:1px solid #03a9f4;"
            "border-radius:10px;padding:18px 24px;min-width:140px;"
            "box-shadow:0 1px 4px rgba(3,169,244,0.3);"
        ),
    ):
        solara.Text(
            title,
            style={
                "font-size": "11px",
                "color": "#81d4fa",
                "text-transform": "uppercase",
                "letter-spacing": "0.9px",
                "font-weight": "600",
            },
        )
        solara.Text(
            value,
            style={
                "font-size": "38px",
                "font-weight": "700",
                "color": "#e1f5fe",
                "line-height": "1.1",
                "margin": "6px 0 3px",
            },
        )
        if sub:
            solara.Text(sub, style={"font-size": "12px", "color": "#03a9f4"})


@solara.component
def Dashboard():
    fc   = faces_detected.value
    br   = brightness_set.value
    ts   = last_checked.value
    err  = error_msg.value
    busy = loading.value
    mon  = auto_monitor.value

    with solara.v.Html(
        tag="main",
        style_="max-width:720px;margin:40px auto;padding:0 24px",
    ):
        solara.Text(
            "Detects faces via your webcam and adjusts screen brightness automatically.",
            style={"color": "#81d4fa", "margin-bottom": "28px", "font-size": "14px"},
        )

        with solara.v.Html(
            tag="div",
            style_="display:flex;align-items:center;gap:14px;margin-bottom:32px;flex-wrap:wrap",
        ):
            if not mon:
                btn_text = "Starting..." if busy else "Start Monitoring"
                solara.Button(
                    btn_text,
                    on_click=lambda: toggle_auto_monitor(True),
                    disabled=busy,
                    color="primary"
                )
            else:
                with solara.v.Html(
                    tag="div",
                    style_=(
                        "display:inline-flex;align-items:center;gap:8px;"
                        "padding:6px 16px;border-radius:6px;"
                        "background:#102027;border:1px solid #03a9f4;"
                        "font-size:14px;color:#4fc3f7;font-weight:600;"
                    ),
                ):
                    solara.v.Html(
                        tag="span",
                        style_=(
                            "width:8px;height:8px;border-radius:50%;"
                            "background:#03a9f4;animation:pulse 1.4s infinite;"
                        ),
                        children=[],
                    )
                    solara.v.Html(
                        tag="span",
                        children=[f"Monitoring every {POLL_INTERVAL}s"],
                        style_="",
                    )

                with solara.v.Html(
                    tag="label",
                    style_=(
                        "display:flex;align-items:center;gap:8px;"
                        "cursor:pointer;font-size:14px;color:#81d4fa;font-weight:500;"
                    ),
                ):
                    solara.Checkbox(value=True, on_value=lambda v: toggle_auto_monitor(v))
                    solara.Text(
                        "Uncheck to stop",
                        style={"font-size": "14px"},
                    )

            if ts:
                solara.Text(
                    f"Last checked  {ts}",
                    style={"font-size": "12px", "color": "#4fc3f7", "margin-left": "auto"},
                )

        if err:
            with solara.v.Html(
                tag="div",
                style_=(
                    "background:#3e2723;border:1px solid #ef5350;"
                    "border-radius:8px;padding:12px 16px;margin-bottom:24px;"
                    "color:#ef5350;font-size:13px;"
                ),
            ):
                solara.Text(f"Error: {err}")

        if br >= 0:
            with solara.v.Html(
                tag="div",
                style_="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px",
            ):
                if fc == 0:
                    face_label = "Nobody detected"
                elif fc == 1:
                    face_label = "1 person"
                else:
                    face_label = f"{fc} people"

                StatCard("Faces", str(fc), face_label)
                StatCard("Brightness", f"{br}%", "Screen level")

            with solara.v.Html(
                tag="div",
                style_=(
                    "background:#102027;border:1px solid #03a9f4;"
                    "border-radius:10px;padding:20px 24px;"
                    "box-shadow:0 1px 4px rgba(3,169,244,0.3);"
                ),
            ):
                BrightnessBar()

        else:
            with solara.v.Html(
                tag="div",
                style_=(
                    "background:#000000;border:1px dashed #03a9f4;"
                    "border-radius:10px;padding:44px 24px;"
                    "text-align:center;color:#81d4fa;"
                ),
            ):
                solara.Text(
                    'Click "Check Now" or turn on Auto-monitor to begin.',
                    style={"font-size": "14px"},
                )

        with solara.v.Html(
            tag="div",
            style_=(
                "margin-top:48px;border-top:1px solid #1c313a;padding-top:16px;"
            ),
        ):
            solara.Text(
                f"Backend: {API_BASE}   |   OpenCV Haar Cascade   |   screen_brightness_control",
                style={"font-size": "11px", "color": "#4fc3f7"},
            )



@solara.component
def AnnouncerView():
    st   = ann_status.value
    rem  = ann_remaining.value
    hist = ann_history.value

    with solara.v.Html(
        tag="main",
        style_="max-width:720px;margin:40px auto;padding:0 24px",
    ):
        
        solara.Text(
            "📢  Exam Announcer",
            style={
                "font-size": "22px",
                "font-weight": "700",
                "color": "#4fc3f7",
                "margin-bottom": "6px",
            },
        )
        solara.Text(
            "Schedule a timed voice announcement. Perfect for calling groups during practicals.",
            style={"color": "#81d4fa", "margin-bottom": "28px", "font-size": "14px"},
        )

        
        with solara.v.Html(
            tag="div",
            style_=(
                "background:#102027;border:1px solid #03a9f4;"
                "border-radius:10px;padding:24px;"
                "box-shadow:0 1px 4px rgba(3,169,244,0.3);"
                "margin-bottom:20px;"
            ),
        ):
            solara.Text(
                "Announcement Message",
                style={
                    "font-size": "11px",
                    "color": "#81d4fa",
                    "font-weight": "600",
                    "text-transform": "uppercase",
                    "letter-spacing": "0.8px",
                    "margin-bottom": "8px",
                },
            )
            solara.InputText(
                label="",
                value=ann_message.value,
                on_value=ann_message.set,
                disabled=st == "waiting",
            )

        
        with solara.v.Html(
            tag="div",
            style_=(
                "background:#102027;border:1px solid #03a9f4;"
                "border-radius:10px;padding:24px;"
                "box-shadow:0 1px 4px rgba(3,169,244,0.3);"
                "margin-bottom:24px;"
            ),
        ):
            solara.Text(
                "Delay (minutes)",
                style={
                    "font-size": "11px",
                    "color": "#81d4fa",
                    "font-weight": "600",
                    "text-transform": "uppercase",
                    "letter-spacing": "0.8px",
                    "margin-bottom": "8px",
                },
            )
            solara.InputInt(
                label="",
                value=ann_delay_min.value,
                on_value=ann_delay_min.set,
                disabled=st == "waiting",
            )

        
        with solara.v.Html(
            tag="div",
            style_="display:flex;align-items:center;gap:14px;margin-bottom:28px;flex-wrap:wrap",
        ):
            if st != "waiting":
                solara.Button(
                    "🔊  Schedule Announcement",
                    on_click=schedule_announcement,
                    color="primary",
                )
            else:
                solara.Button(
                    "✖  Cancel",
                    on_click=cancel_announcement,
                    color="error",
                )

        
        if st == "waiting" and rem:
            with solara.v.Html(
                tag="div",
                style_=(
                    "background:#0a1f2e;border:1px solid #03a9f4;"
                    "border-radius:10px;padding:32px;text-align:center;"
                    "margin-bottom:24px;"
                ),
            ):
                solara.Text(
                    "⏳  Announcing in",
                    style={
                        "font-size": "13px",
                        "color": "#81d4fa",
                        "text-transform": "uppercase",
                        "letter-spacing": "1px",
                        "font-weight": "600",
                    },
                )
                solara.Text(
                    rem,
                    style={
                        "font-size": "54px",
                        "font-weight": "700",
                        "color": "#4fc3f7",
                        "font-family": "'Courier New', monospace",
                        "margin": "8px 0",
                    },
                )

        if st == "speaking":
            with solara.v.Html(
                tag="div",
                style_=(
                    "background:#1b3a1b;border:1px solid #66bb6a;"
                    "border-radius:10px;padding:20px;text-align:center;"
                    "margin-bottom:24px;color:#a5d6a7;font-size:15px;font-weight:600;"
                ),
            ):
                solara.Text("🔈  Speaking now …")

        if st == "done":
            with solara.v.Html(
                tag="div",
                style_=(
                    "background:#102027;border:1px solid #4fc3f7;"
                    "border-radius:10px;padding:20px;text-align:center;"
                    "margin-bottom:24px;color:#4fc3f7;font-size:15px;font-weight:600;"
                ),
            ):
                solara.Text("✅  Announcement complete! You can schedule another.")

        
        if hist:
            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:12px;border-top:1px solid #1c313a;padding-top:16px;"
                ),
            ):
                solara.Text(
                    "Announcement History",
                    style={
                        "font-size": "11px",
                        "color": "#81d4fa",
                        "font-weight": "600",
                        "text-transform": "uppercase",
                        "letter-spacing": "0.8px",
                        "margin-bottom": "10px",
                    },
                )
                for entry in reversed(hist):
                    solara.Text(
                        entry,
                        style={
                            "font-size": "13px",
                            "color": "#90caf9",
                            "padding": "4px 0",
                            "font-family": "'Courier New', monospace",
                        },
                    )



@solara.component
def Page():
    tab = active_tab.value

    with solara.v.Html(
        tag="div",
        style_=(
            "min-height:100vh;background:#000000;"
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
            "color:#e1f5fe;"
        ),
    ):   
        with solara.v.Html(
            tag="header",
            style_=(
                "background:#102027;border-bottom:1px solid #03a9f4;"
                "padding:14px 32px;display:flex;align-items:center;gap:12px;"
            ),
        ):
            solara.Text(
                "Camera Automation Hub",
                style={
                    "font-size": "17px",
                    "font-weight": "700",
                    "color": "#4fc3f7",
                    "letter-spacing": "-0.2px",
                },
            )
            solara.v.Html(tag="span", style_="flex:1", children=[])
            StatusBadge()

        
        with solara.v.Html(
            tag="nav",
            style_=(
                "display:flex;gap:0;background:#0a1520;"
                "border-bottom:2px solid #03a9f433;"
            ),
        ):
            solara.Button(
                "🎥  Camera Controller",
                on_click=lambda: active_tab.set(0),
                color="#102027" if tab == 0 else None,
                dark=True,
                style={
                    "border-bottom": "2px solid #03a9f4" if tab == 0 else "2px solid transparent",
                    "border-radius": "0",
                    "color": "#4fc3f7" if tab == 0 else "#81d4fa",
                    "font-weight": "700" if tab == 0 else "500",
                    "letter-spacing": "0.2px",
                    "text-transform": "none",
                    "padding": "12px 28px",
                },
            )
            solara.Button(
                "📢  Exam Announcer",
                on_click=lambda: active_tab.set(1),
                color="#102027" if tab == 1 else None,
                dark=True,
                style={
                    "border-bottom": "2px solid #03a9f4" if tab == 1 else "2px solid transparent",
                    "border-radius": "0",
                    "color": "#4fc3f7" if tab == 1 else "#81d4fa",
                    "font-weight": "700" if tab == 1 else "500",
                    "letter-spacing": "0.2px",
                    "text-transform": "none",
                    "padding": "12px 28px",
                },
            )

        
        if tab == 0:
            Dashboard()
        else:
            AnnouncerView()
