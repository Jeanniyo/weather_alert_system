# FILE: email_html.py
# PURPOSE: Rich HTML email — table-based 2x2 grid (email-client compatible),
#          CSS animations, precipitation bars, professional signature.

import datetime
from config import RAINFALL_MM_THRESHOLD

# ── Signature ─────────────────────────────────────────────────────────────────
SIG_NAME     = "Jean De Dieu Niyogisubizo"
SIG_TITLE    = "BSc. Environmental Planning and Management"
SIG_ROLE     = "Training Officer, GEOSAR | University of Rwanda – CST"
SIG_PHONE    = "+250 791 117 367"
SIG_EMAIL    = "niyogisubizo_224009788@stud.ur.ac.rw"
SIG_LINKEDIN = "https://www.linkedin.com/in/jean-de-dieu-niyogisubizo/"

# ── Shared CSS ────────────────────────────────────────────────────────────────
_CSS = """<style>
body,table,td,p,a{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}
table,td{mso-table-lspace:0;mso-table-rspace:0}
img{-ms-interpolation-mode:bicubic;border:0;outline:none;text-decoration:none}
body{margin:0;padding:0;background:#e8edf5;font-family:'Segoe UI',Helvetica,Arial,sans-serif}

/* Animations — work in Gmail, Apple Mail, iOS Mail */
@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
@keyframes sway{0%,100%{transform:rotate(-8deg) translateY(0)}50%{transform:rotate(8deg) translateY(6px)}}
@keyframes flash{0%,85%,100%{opacity:1}87%,95%{opacity:.2}}
@keyframes drift{0%,100%{transform:translateX(0)}50%{transform:translateX(10px)}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.14)}}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes growBar{from{width:0}to{width:var(--w)}}

.icon-rain{display:inline-block;animation:sway 1.8s ease-in-out infinite}
.icon-sun{display:inline-block;animation:spin 8s linear infinite}
.icon-storm{display:inline-block;animation:flash 2.2s infinite}
.icon-cloud{display:inline-block;animation:drift 4s ease-in-out infinite}
.icon-heat{display:inline-block;animation:pulse 1.6s ease-in-out infinite}
.icon-snow{display:inline-block;animation:drift 3s ease-in-out infinite}

.fade-card{animation:fadeUp .5s ease both}
.fade-card:nth-child(2){animation-delay:.1s}
.fade-card:nth-child(3){animation-delay:.2s}
.fade-card:nth-child(4){animation-delay:.3s}

/* Responsive */
@media only screen and (max-width:480px){
  .card-cell{display:block!important;width:100%!important}
  .wrap-table{width:100%!important}
}
</style>"""


# ── Theme ─────────────────────────────────────────────────────────────────────
def _theme(condition: str, temp: float) -> dict:
    c = condition.lower()
    if "thunder" in c or "storm" in c:
        return {"grad1":"#0d0d2b","grad2":"#1a1a4e","grad3":"#2d1b69",
                "accent":"#e94560","light":"#ffd6df","icon":"⛈️","anim":"icon-storm","label":"Storm Alert"}
    if "snow" in c:
        return {"grad1":"#1a3a5c","grad2":"#2e6da4","grad3":"#89c4f4",
                "accent":"#60b8ff","light":"#dbeafe","icon":"❄️","anim":"icon-snow","label":"Snow"}
    if "rain" in c or "drizzle" in c or "shower" in c:
        return {"grad1":"#0f2d5c","grad2":"#1a5276","grad3":"#2471a3",
                "accent":"#3b82f6","light":"#dbeafe","icon":"🌧️","anim":"icon-rain","label":"Rainy"}
    if "clear" in c or "sun" in c:
        if temp >= 35:
            return {"grad1":"#7b1515","grad2":"#c0392b","grad3":"#e67e22",
                    "accent":"#f59e0b","light":"#fef3c7","icon":"🔥","anim":"icon-heat","label":"Extreme Heat"}
        return {"grad1":"#b7410e","grad2":"#e67e22","grad3":"#f4d03f",
                "accent":"#f59e0b","light":"#fef9c3","icon":"☀️","anim":"icon-sun","label":"Clear & Sunny"}
    if "cloud" in c or "overcast" in c:
        return {"grad1":"#2d3748","grad2":"#4a5568","grad3":"#718096",
                "accent":"#90cdf4","light":"#ebf8ff","icon":"☁️","anim":"icon-cloud","label":"Cloudy"}
    return {"grad1":"#1e3a5f","grad2":"#2563eb","grad3":"#3b82f6",
            "accent":"#60a5fa","light":"#dbeafe","icon":"🌦️","anim":"icon-cloud","label":"Variable"}


def _bar_colour(pct: int) -> str:
    if pct >= 80: return "linear-gradient(90deg,#f87171,#dc2626)"
    if pct >= 40: return "linear-gradient(90deg,#fbbf24,#f59e0b)"
    return "linear-gradient(90deg,#34d399,#059669)"


def _card(label: str, value: str, unit: str, icon: str, accent: str, light: str) -> str:
    return f"""
    <td class="card-cell fade-card" width="50%" valign="top"
        style="padding:6px">
      <table width="100%" cellpadding="0" cellspacing="0" border="0"
             style="background:#ffffff;border-radius:14px;
                    box-shadow:0 4px 16px rgba(0,0,0,.08);
                    border-top:4px solid {accent};overflow:hidden">
        <tr>
          <td style="padding:20px 18px 18px;text-align:center">
            <div style="font-size:28px;margin-bottom:6px">{icon}</div>
            <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;
                        letter-spacing:.8px;font-weight:600">{label}</div>
            <div style="font-size:34px;font-weight:800;color:#0f172a;
                        margin:6px 0 2px;line-height:1">{value}</div>
            <div style="font-size:13px;color:#64748b;font-weight:500">{unit}</div>
          </td>
        </tr>
        <tr>
          <td style="background:{light};padding:8px 18px;
                     text-align:center;border-radius:0 0 14px 14px">
            <span style="font-size:11px;color:{accent};font-weight:700">LIVE</span>
          </td>
        </tr>
      </table>
    </td>"""


def _precip_block(rain_1h: float, rain_3h: float, accent: str, light: str) -> str:
    thr   = RAINFALL_MM_THRESHOLD
    p1    = min(100, int((rain_1h / thr) * 100))
    p3    = min(100, int((rain_3h / thr) * 100))
    c1    = _bar_colour(p1)
    c3    = _bar_colour(p3)
    status = "⚠️ NEAR THRESHOLD" if max(p1, p3) >= 70 else ("🟡 MODERATE" if max(p1, p3) >= 35 else "🟢 NORMAL")

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background:{light};border-radius:14px;margin:14px 0;
                  border-left:5px solid {accent}">
      <tr>
        <td style="padding:18px 20px">
          <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td>
                <span style="font-size:14px;font-weight:700;color:#1e40af">
                  💧 Precipitation Level
                </span>
                &nbsp;&nbsp;
                <span style="font-size:11px;font-weight:700;
                             background:{accent};color:#fff;
                             padding:2px 8px;border-radius:20px">{status}</span>
              </td>
              <td align="right" style="font-size:11px;color:#64748b">
                Emergency threshold: <b>{thr:.0f} mm</b>
              </td>
            </tr>
          </table>
          <!-- 1h bar -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:14px">
            <tr>
              <td style="font-size:12px;color:#475569;padding-bottom:5px">
                <b>Last 1 hour</b>
              </td>
              <td align="right" style="font-size:12px;color:#1e40af;font-weight:700;padding-bottom:5px">
                {rain_1h:.1f} mm &nbsp;({p1}%)
              </td>
            </tr>
            <tr>
              <td colspan="2">
                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="background:#dbeafe;border-radius:6px;height:10px;overflow:hidden">
                      <div style="height:10px;width:{p1}%;background:{c1};
                                  border-radius:6px;min-width:4px"></div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
          <!-- 3h bar -->
          <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:12px">
            <tr>
              <td style="font-size:12px;color:#475569;padding-bottom:5px">
                <b>Last 3 hours</b>
              </td>
              <td align="right" style="font-size:12px;color:#1e40af;font-weight:700;padding-bottom:5px">
                {rain_3h:.1f} mm &nbsp;({p3}%)
              </td>
            </tr>
            <tr>
              <td colspan="2">
                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="background:#dbeafe;border-radius:6px;height:10px;overflow:hidden">
                      <div style="height:10px;width:{p3}%;background:{c3};
                                  border-radius:6px;min-width:4px"></div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>"""


def _tip_row(icon: str, text: str) -> str:
    return f"""
    <tr>
      <td style="padding:0 0 10px 0">
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="background:#f8fafc;border-radius:10px;
                      border-left:4px solid #94a3b8">
          <tr>
            <td width="44" style="padding:14px 10px 14px 16px;font-size:22px">{icon}</td>
            <td style="padding:14px 16px 14px 6px;font-size:14px;
                       color:#334155;line-height:1.5">{text}</td>
          </tr>
        </table>
      </td>
    </tr>"""


def _signature_block() -> str:
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
           style="border-top:2px solid #e2e8f0;margin-top:28px;padding-top:20px">
      <tr><td style="padding-top:22px">
        <!-- Name & titles -->
        <div style="font-size:18px;font-weight:800;color:#0f172a;
                    letter-spacing:-.2px">{SIG_NAME}</div>
        <div style="font-size:13px;color:#3b82f6;font-weight:600;
                    margin-top:3px">{SIG_TITLE}</div>
        <div style="font-size:13px;color:#64748b;margin-top:2px">{SIG_ROLE}</div>

        <!-- Divider -->
        <div style="height:1px;background:#e2e8f0;margin:14px 0"></div>

        <!-- Contacts -->
        <table cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="padding:4px 20px 4px 0;font-size:13px;color:#475569">
              📞 <a href="tel:{SIG_PHONE.replace(' ','')}"
                    style="color:#475569;text-decoration:none">{SIG_PHONE}</a>
            </td>
            <td style="padding:4px 0;font-size:13px;color:#475569">
              ✉️ <a href="mailto:{SIG_EMAIL}"
                    style="color:#3b82f6;text-decoration:none">{SIG_EMAIL}</a>
            </td>
          </tr>
        </table>

        <!-- LinkedIn button -->
        <div style="margin-top:14px">
          <a href="{SIG_LINKEDIN}" target="_blank"
             style="display:inline-block;background:linear-gradient(135deg,#0a66c2,#0077b5);
                    color:#ffffff;padding:10px 22px;border-radius:25px;
                    font-size:13px;font-weight:700;text-decoration:none;
                    letter-spacing:.4px;box-shadow:0 4px 12px rgba(10,102,194,.3)">
            🔗 &nbsp;Connect on LinkedIn
          </a>
        </div>
      </td></tr>
    </table>"""


# ── Public builders ───────────────────────────────────────────────────────────

def build_normal_html(forecast: dict, tips: tuple) -> str:
    now  = datetime.datetime.now().strftime("%A, %d %B %Y · %H:%M")
    th   = _theme(forecast["condition"], forecast["temp"])
    rain_1h = forecast.get("rain_1h", 0.0)
    rain_3h = forecast.get("rain_3h", 0.0)
    clouds  = forecast.get("clouds", 0)

    card_row1 = f"""<tr>
      {_card("Temperature", f"{forecast['temp']:.1f}", "°C", "🌡️", th['accent'], th['light'])}
      {_card("Humidity",    f"{forecast['humidity']}", "%",  "💧", th['accent'], th['light'])}
    </tr>"""
    card_row2 = f"""<tr>
      {_card("Wind Speed",  f"{forecast['wind']:.1f}", "m/s", "🌬️", th['accent'], th['light'])}
      {_card("Cloud Cover", f"{clouds}",               "%",   "☁️", th['accent'], th['light'])}
    </tr>"""

    precip  = _precip_block(rain_1h, rain_3h, th["accent"], th["light"])
    sig     = _signature_block()
    tip_rows = "".join(_tip_row(th["icon"], t) for t in tips)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Weather Update — {forecast['city']}</title>
{_CSS}
</head>
<body>
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:#e8edf5;padding:30px 0">
  <tr><td align="center">
  <table class="wrap-table" width="600" cellpadding="0" cellspacing="0" border="0"
         style="border-radius:20px;overflow:hidden;
                box-shadow:0 20px 60px rgba(0,0,0,.18)">

    <!-- HEADER -->
    <tr>
      <td style="background:linear-gradient(160deg,{th['grad1']},{th['grad2']},{th['grad3']});
                 padding:48px 30px 36px;text-align:center;position:relative">
        <div class="{th['anim']}" style="font-size:80px;line-height:1;margin-bottom:12px">{th['icon']}</div>
        <div style="color:rgba(255,255,255,.55);font-size:12px;font-weight:600;
                    text-transform:uppercase;letter-spacing:2px;margin-bottom:6px">{th['label']}</div>
        <div style="color:#ffffff;font-size:32px;font-weight:900;letter-spacing:-0.5px;
                    text-shadow:0 2px 12px rgba(0,0,0,.4)">🌍 {forecast['city']}</div>
        <div style="color:rgba(255,255,255,.85);font-size:16px;
                    margin-top:8px;font-style:italic">{forecast['condition'].capitalize()}</div>
        <div style="color:rgba(255,255,255,.55);font-size:12px;margin-top:8px">🕒 {now}</div>
      </td>
    </tr>

    <!-- BODY -->
    <tr>
      <td style="background:#f0f4f8;padding:28px 24px">

        <!-- 2x2 DATA CARDS -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          {card_row1}
          <tr><td colspan="2" height="4"></td></tr>
          {card_row2}
        </table>

        <!-- PRECIPITATION -->
        {precip}

        <!-- TIPS -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:6px">
          {tip_rows}
        </table>

        <!-- SIGNATURE -->
        {sig}
      </td>
    </tr>

    <!-- FOOTER -->
    <tr>
      <td style="background:linear-gradient(135deg,{th['grad1']},{th['grad2']});
                 padding:18px;text-align:center">
        <span style="font-size:11px;color:rgba(255,255,255,.6)">
          Automated Weather Alert System &nbsp;·&nbsp; Kigali, Rwanda
          &nbsp;·&nbsp; Powered by OpenWeatherMap
        </span>
      </td>
    </tr>

  </table>
  </td></tr>
</table>
</body></html>"""


def build_emergency_html(forecast: dict, reason: str, metric: float) -> str:
    now  = datetime.datetime.now().strftime("%A, %d %B %Y · %H:%M")
    th   = _theme(forecast["condition"], forecast["temp"])
    rain_1h = forecast.get("rain_1h", 0.0)
    rain_3h = forecast.get("rain_3h", 0.0)
    clouds  = forecast.get("clouds", 0)

    labels = {
        "heavy_rain_3h":  ("‼️ FLOOD ALERT",    f"{metric:.1f} mm rain in 3 hours detected",   "Move to higher ground immediately · Avoid flooded routes"),
        "heavy_rain_1h":  ("‼️ FLOOD ALERT",    f"{metric:.1f} mm rain in 1 hour detected",    "Move to higher ground immediately · Avoid flooded routes"),
        "storm_with_wind":("⚡ STORM ALERT",    f"Dangerous wind: {metric:.1f} m/s",           "Stay indoors · Secure loose items · Unplug electronics"),
        "extreme_heat":   ("🔥 HEAT EMERGENCY", f"Extreme temperature: {metric:.1f} °C",       "Hydrate frequently · Avoid outdoor activity · Seek shade"),
    }
    title, sub, action = labels.get(reason, ("⚠️ WEATHER EMERGENCY", reason, "Follow local guidance"))

    card_row1 = f"""<tr>
      {_card("Temperature", f"{forecast['temp']:.1f}", "°C", "🌡️", "#dc2626", "#fee2e2")}
      {_card("Humidity",    f"{forecast['humidity']}", "%",  "💧", "#dc2626", "#fee2e2")}
    </tr>"""
    card_row2 = f"""<tr>
      {_card("Wind Speed",  f"{forecast['wind']:.1f}", "m/s", "🌬️", "#dc2626", "#fee2e2")}
      {_card("Cloud Cover", f"{clouds}",               "%",   "☁️", "#dc2626", "#fee2e2")}
    </tr>"""

    precip = _precip_block(rain_1h, rain_3h, "#dc2626", "#fee2e2")
    sig    = _signature_block()

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — {forecast['city']}</title>
{_CSS}
</head>
<body>
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background:#e8edf5;padding:30px 0">
  <tr><td align="center">
  <table class="wrap-table" width="600" cellpadding="0" cellspacing="0" border="0"
         style="border-radius:20px;overflow:hidden;
                box-shadow:0 20px 60px rgba(0,0,0,.22)">

    <!-- HEADER -->
    <tr>
      <td style="background:linear-gradient(160deg,{th['grad1']},{th['grad2']},{th['grad3']});
                 padding:48px 30px 36px;text-align:center">
        <div class="{th['anim']}" style="font-size:80px;line-height:1;margin-bottom:12px">{th['icon']}</div>
        <div style="color:rgba(255,255,255,.6);font-size:12px;font-weight:700;
                    text-transform:uppercase;letter-spacing:2px;margin-bottom:8px">Emergency Alert</div>
        <div style="color:#ffffff;font-size:32px;font-weight:900;
                    text-shadow:0 2px 12px rgba(0,0,0,.5)">🌍 {forecast['city']}</div>
        <div style="color:rgba(255,255,255,.8);font-size:15px;
                    margin-top:8px;font-style:italic">{forecast['condition'].capitalize()}</div>
        <div style="color:rgba(255,255,255,.5);font-size:12px;margin-top:6px">🕒 {now}</div>
      </td>
    </tr>

    <!-- EMERGENCY BANNER -->
    <tr>
      <td style="background:linear-gradient(135deg,#7f1d1d,#dc2626);
                 padding:22px 28px;text-align:center;animation:flash 2s infinite">
        <div style="font-size:24px;font-weight:900;color:#ffffff;
                    letter-spacing:.5px">{title}</div>
        <div style="font-size:14px;color:rgba(255,255,255,.9);margin-top:6px">{sub}</div>
        <div style="font-size:13px;font-weight:700;color:#fbbf24;margin-top:10px">
          ⚡ ACTION REQUIRED: {action}
        </div>
      </td>
    </tr>

    <!-- BODY -->
    <tr>
      <td style="background:#f0f4f8;padding:28px 24px">

        <!-- 2x2 CARDS -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          {card_row1}
          <tr><td colspan="2" height="4"></td></tr>
          {card_row2}
        </table>

        {precip}
        {sig}
      </td>
    </tr>

    <!-- FOOTER -->
    <tr>
      <td style="background:linear-gradient(135deg,#7f1d1d,#991b1b);
                 padding:18px;text-align:center">
        <span style="font-size:11px;color:rgba(255,255,255,.6)">
          ⚠️ Emergency Alert · Weather Alert System · Kigali, Rwanda
        </span>
      </td>
    </tr>

  </table>
  </td></tr>
</table>
</body></html>"""
