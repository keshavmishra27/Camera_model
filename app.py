import time
import threading
import requests
import solara

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


@solara.component
def StatusBadge():
    s = status.value

    labels = {"active": "Face Detected", "idle": "No Face", "error": "Error"}
    colors = {"active": "#2e7d32", "idle": "#546e7a", "error": "#b71c1c"}
    backs  = {"active": "#e8f5e9",  "idle": "#eceff1",  "error": "#ffebee"}
    dots   = {"active": "#43a047",  "idle": "#90a4ae",  "error": "#e53935"}

    label = labels.get(s, "Unknown")
    color = colors.get(s, "#333")
    bg    = backs.get(s, "#f5f5f5")
    dot   = dots.get(s, "#aaa")

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
    fill = "#1565c0" if pct > 0 else "#bdbdbd"
    lbl  = f"{pct}%" if pct > 0 else "Off (0%)"

    with solara.Column(style={"gap": "6px"}):
        solara.Text(
            "Brightness level",
            style={
                "font-size": "11px",
                "color": "#90a4ae",
                "font-weight": "600",
                "text-transform": "uppercase",
                "letter-spacing": "0.8px",
            },
        )
        with solara.v.Html(
            tag="div",
            style_="background:#e0e0e0;border-radius:6px;height:14px;width:100%;overflow:hidden",
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
            style={"font-size": "14px", "color": "#37474f", "font-weight": "700"},
        )


@solara.component
def StatCard(title, value, sub=""):
    with solara.v.Html(
        tag="div",
        style_=(
            "background:#fff;border:1px solid #e0e0e0;"
            "border-radius:10px;padding:18px 24px;min-width:140px;"
            "box-shadow:0 1px 4px rgba(0,0,0,0.07);"
        ),
    ):
        solara.Text(
            title,
            style={
                "font-size": "11px",
                "color": "#90a4ae",
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
                "color": "#263238",
                "line-height": "1.1",
                "margin": "6px 0 3px",
            },
        )
        if sub:
            solara.Text(sub, style={"font-size": "12px", "color": "#90a4ae"})


@solara.component
def Dashboard():
    fc   = faces_detected.value
    br   = brightness_set.value
    ts   = last_checked.value
    err  = error_msg.value
    busy = loading.value
    mon  = auto_monitor.value

    with solara.v.Html(
        tag="div",
        style_=(
            "min-height:100vh;background:#f5f7fa;"
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
            "color:#263238;"
        ),
    ):
        with solara.v.Html(
            tag="header",
            style_=(
                "background:#fff;border-bottom:1px solid #e0e0e0;"
                "padding:14px 32px;display:flex;align-items:center;gap:12px;"
            ),
        ):
            solara.Text(
                "Face Brightness Controller",
                style={
                    "font-size": "17px",
                    "font-weight": "700",
                    "color": "#1a237e",
                    "letter-spacing": "-0.2px",
                },
            )
            solara.v.Html(tag="span", style_="flex:1", children=[])
            StatusBadge()

        with solara.v.Html(
            tag="main",
            style_="max-width:720px;margin:40px auto;padding:0 24px",
        ):
            solara.Text(
                "Detects faces via your webcam and adjusts screen brightness automatically.",
                style={"color": "#546e7a", "margin-bottom": "28px", "font-size": "14px"},
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
                    )
                else:
                    with solara.v.Html(
                        tag="div",
                        style_=(
                            "display:inline-flex;align-items:center;gap:8px;"
                            "padding:6px 16px;border-radius:6px;"
                            "background:#e3f2fd;border:1px solid #90caf9;"
                            "font-size:14px;color:#1565c0;font-weight:600;"
                        ),
                    ):
                        solara.v.Html(
                            tag="span",
                            style_=(
                                "width:8px;height:8px;border-radius:50%;"
                                "background:#1565c0;animation:pulse 1.4s infinite;"
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
                            "cursor:pointer;font-size:14px;color:#546e7a;font-weight:500;"
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
                        style={"font-size": "12px", "color": "#b0bec5", "margin-left": "auto"},
                    )

            if err:
                with solara.v.Html(
                    tag="div",
                    style_=(
                        "background:#ffebee;border:1px solid #ef9a9a;"
                        "border-radius:8px;padding:12px 16px;margin-bottom:24px;"
                        "color:#b71c1c;font-size:13px;"
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
                        "background:#fff;border:1px solid #e0e0e0;"
                        "border-radius:10px;padding:20px 24px;"
                        "box-shadow:0 1px 4px rgba(0,0,0,0.07);"
                    ),
                ):
                    BrightnessBar()

            else:
                with solara.v.Html(
                    tag="div",
                    style_=(
                        "background:#fff;border:1px dashed #cfd8dc;"
                        "border-radius:10px;padding:44px 24px;"
                        "text-align:center;color:#90a4ae;"
                    ),
                ):
                    solara.Text(
                        'Click "Check Now" or turn on Auto-monitor to begin.',
                        style={"font-size": "14px"},
                    )

            with solara.v.Html(
                tag="div",
                style_=(
                    "margin-top:48px;border-top:1px solid #eceff1;padding-top:16px;"
                ),
            ):
                solara.Text(
                    f"Backend: {API_BASE}   |   OpenCV Haar Cascade   |   screen_brightness_control",
                    style={"font-size": "11px", "color": "#b0bec5"},
                )


Page = Dashboard
