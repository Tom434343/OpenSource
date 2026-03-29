"""
VeilleNumerique — Mailer générique
Envoie les rapports par email : 1 email JOUR (avec articles) + 1 email par consolidation.
"""

import os
import re
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ─── Config couleurs par couche ──────────────────────────────────────────────

COUCHE_STYLE = {
    "jour":       {"color": "#e94560", "icon": "📰", "label": "Synthèse du jour"},
    "semaine":    {"color": "#7c3aed", "icon": "📊", "label": "Synthèse hebdomadaire"},
    "mois":       {"color": "#1d4ed8", "icon": "📅", "label": "Synthèse mensuelle"},
    "trimestre":  {"color": "#15803d", "icon": "📈", "label": "Synthèse trimestrielle"},
    "annee":      {"color": "#b45309", "icon": "🏆", "label": "Bilan annuel"},
    "cumul":      {"color": "#374151", "icon": "🧠", "label": "Mémoire cumulative"},
}


def _md_to_html(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace('\n', '<br>')
    return text


def _source_badge(name, colors):
    color = colors.get(name, "#64748b")
    return (
        f'<span style="display:inline-block;background:{color};color:#fff;'
        f'font-size:10px;padding:2px 10px;border-radius:12px;'
        f'font-family:Arial,sans-serif;font-weight:bold;">{name}</span>'
    )


def _send_email(subject, html, log_fn, conteneur_name):
    """Envoie un email HTML via SMTP."""
    email_to = os.environ.get("VEILLE_EMAIL_TO", "")
    email_from = os.environ.get("VEILLE_EMAIL_FROM", "")
    smtp_host = os.environ.get("VEILLE_SMTP_HOST", "127.0.0.1")
    smtp_port = int(os.environ.get("VEILLE_SMTP_PORT", "1026"))
    smtp_user = os.environ.get("VEILLE_SMTP_USER", "")
    smtp_pass = os.environ.get("VEILLE_SMTP_PASS", "")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = email_from
        msg["To"] = email_to
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.sendmail(email_from, email_to, msg.as_string())
        log_fn(f"  Email envoyé à {email_to} [{conteneur_name}]")
        return True
    except Exception as e:
        log_fn(f"  ERREUR email [{conteneur_name}]: {e}")
        return False


# ─── EMAIL JOUR (avec articles) ─────────────────────────────────────────────

def send_report(articles, analyse, config, log_fn):
    """Email quotidien avec articles + analyse du jour."""
    conteneur_name = config.get("name", "Veille")
    colors = config.get("source_colors", {})
    prefix = config.get("email_subject_prefix", f"🔍 Veille [{conteneur_name}]")

    alert_articles = [a for a in articles if a.get("alert")]
    other_articles = [a for a in articles if not a.get("alert")]
    alert_count = len(alert_articles)
    sources_active = len(set(a["source"] for a in articles))
    date_str = datetime.now().strftime('%d %B %Y')
    date_short = datetime.now().strftime('%d/%m/%Y')

    subject = f"📰 {prefix} — {date_short} — {len(articles)} articles ({alert_count} alerte{'s' if alert_count != 1 else ''})"

    analyse_html = _md_to_html(analyse) if analyse else "<em>Analyse non disponible</em>"

    # Cartes alertes
    alerts_section = ""
    if alert_articles:
        cards = ""
        for a in alert_articles:
            badge = _source_badge(a["source"], colors)
            cards += f"""
      <div style="background:#fff5f5;border:1px solid #fecaca;border-left:4px solid #dc2626;border-radius:0 8px 8px 0;padding:16px;margin-bottom:12px;">
        <div style="margin-bottom:8px;">
          <span style="display:inline-block;background:#dc2626;color:#fff;font-size:10px;padding:2px 9px;border-radius:4px;font-family:Arial,sans-serif;font-weight:bold;letter-spacing:1px;text-transform:uppercase;margin-right:6px;">🚨 Alerte</span>
          {badge}
        </div>
        <div style="font-size:15px;font-weight:bold;margin:8px 0 6px;line-height:1.4;">
          <a href="{a['link']}" style="color:#1a1a2e;text-decoration:none;">{a['title']}</a>
        </div>
        <div style="font-size:12px;color:#6b7280;line-height:1.5;font-family:Arial,sans-serif;">{a['summary'][:220]}</div>
        <div style="font-size:11px;color:#9ca3af;margin-top:8px;font-family:Arial,sans-serif;">{a['date']}</div>
      </div>"""

        alerts_section = f"""
  <tr>
    <td style="padding:0 35px 10px;">
      <div style="font-size:10px;letter-spacing:3px;text-transform:uppercase;color:#dc2626;font-family:Arial,sans-serif;margin-bottom:15px;border-bottom:1px solid #fecaca;padding-bottom:8px;">🚨 Alertes prioritaires</div>
      {cards}
    </td>
  </tr>"""

    # Liste articles normaux
    others_html = ""
    for a in other_articles:
        badge = _source_badge(a["source"], colors)
        others_html += f"""
      <div style="border-bottom:1px solid #f1f5f9;padding:12px 0;">
        <div style="margin-bottom:6px;">{badge}</div>
        <div style="font-size:14px;font-weight:bold;margin:4px 0 3px;line-height:1.4;">
          <a href="{a['link']}" style="color:#1e293b;text-decoration:none;">{a['title']}</a>
        </div>
        <div style="font-size:11px;color:#94a3b8;font-family:Arial,sans-serif;">{a['date']}</div>
      </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f0f4f8;">
<tr><td align="center" style="padding:24px 10px;">

<table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden;">

  <!-- HEADER -->
  <tr>
    <td style="background:#1a1a2e;padding:28px 35px;">
      <div style="color:#e94560;font-size:10px;letter-spacing:3px;text-transform:uppercase;font-family:Arial,sans-serif;margin-bottom:8px;">VeilleNumerique · {conteneur_name}</div>
      <div style="color:#ffffff;font-size:22px;font-weight:bold;font-family:Arial,sans-serif;">📰 {conteneur_name} — Rapport du jour</div>
      <div style="color:#64748b;font-size:13px;margin-top:6px;font-family:Arial,sans-serif;">{date_str}</div>
    </td>
  </tr>

  <!-- STATS -->
  <tr>
    <td style="background:#16213e;padding:14px 35px;">
      <span style="display:inline-block;background:#e94560;color:#fff;padding:5px 14px;border-radius:20px;font-size:12px;font-family:Arial,sans-serif;margin-right:8px;">🚨 {alert_count} alerte{"s" if alert_count != 1 else ""}</span>
      <span style="display:inline-block;background:#2d3748;color:#a0aec0;padding:5px 14px;border-radius:20px;font-size:12px;font-family:Arial,sans-serif;margin-right:8px;">📰 {len(articles)} articles</span>
      <span style="display:inline-block;background:#2d3748;color:#a0aec0;padding:5px 14px;border-radius:20px;font-size:12px;font-family:Arial,sans-serif;">⚡ {sources_active} source{"s" if sources_active != 1 else ""}</span>
    </td>
  </tr>

  <!-- ANALYSE IA -->
  <tr>
    <td style="padding:30px 35px 20px;">
      <div style="font-size:10px;letter-spacing:3px;text-transform:uppercase;color:#e94560;font-family:Arial,sans-serif;margin-bottom:15px;">▌ Analyse IA — Synthèse du jour</div>
      <div style="background:#f8fafc;border-left:4px solid #e94560;padding:20px;border-radius:0 8px 8px 0;color:#374151;font-size:14px;line-height:1.8;font-family:Arial,sans-serif;">
        {analyse_html}
      </div>
    </td>
  </tr>

  <!-- ALERTES -->
  {alerts_section}

  <!-- ARTICLES -->
  <tr>
    <td style="padding:10px 35px 30px;">
      <div style="font-size:10px;letter-spacing:3px;text-transform:uppercase;color:#64748b;font-family:Arial,sans-serif;margin-bottom:4px;border-bottom:1px solid #e2e8f0;padding-bottom:8px;">📰 Articles</div>
      {others_html}
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:20px 35px;text-align:center;">
      <div style="color:#94a3b8;font-size:11px;font-family:Arial,sans-serif;">VeilleNumerique · {conteneur_name} · {date_str}</div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return _send_email(subject, html, log_fn, conteneur_name)


# ─── EMAIL CONSOLIDATION (semaine/mois/trimestre/annee) ──────────────────────

def send_synthese_report(couche, analyse, config, log_fn, periode_label=""):
    """
    Email de synthèse pour une couche de consolidation.

    Args:
        couche: "semaine", "mois", "trimestre", "annee"
        analyse: texte de la synthèse
        config: config.json du conteneur
        log_fn: fonction de log
        periode_label: ex "S11 (16/03 → 22/03)" ou "Mars 2026"
    """
    conteneur_name = config.get("name", "Veille")
    style = COUCHE_STYLE.get(couche, COUCHE_STYLE["jour"])
    accent = style["color"]
    icon = style["icon"]
    label = style["label"]

    date_str = datetime.now().strftime('%d %B %Y')
    date_short = datetime.now().strftime('%d/%m/%Y')

    subject = f"{icon} {conteneur_name} — {label}"
    if periode_label:
        subject += f" — {periode_label}"

    analyse_html = _md_to_html(analyse) if analyse else "<em>Synthèse non disponible</em>"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f0f4f8;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f0f4f8;">
<tr><td align="center" style="padding:24px 10px;">

<table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden;">

  <!-- HEADER -->
  <tr>
    <td style="background:#1a1a2e;padding:28px 35px;">
      <div style="color:{accent};font-size:10px;letter-spacing:3px;text-transform:uppercase;font-family:Arial,sans-serif;margin-bottom:8px;">VeilleNumerique · {conteneur_name} · {label}</div>
      <div style="color:#ffffff;font-size:22px;font-weight:bold;font-family:Arial,sans-serif;">{icon} {label}</div>
      <div style="color:#64748b;font-size:13px;margin-top:6px;font-family:Arial,sans-serif;">{periode_label if periode_label else date_str}</div>
    </td>
  </tr>

  <!-- BANDEAU COUCHE -->
  <tr>
    <td style="background:{accent};padding:10px 35px;">
      <span style="color:#fff;font-size:13px;font-family:Arial,sans-serif;font-weight:bold;letter-spacing:1px;">{icon} {label.upper()}</span>
    </td>
  </tr>

  <!-- SYNTHÈSE -->
  <tr>
    <td style="padding:30px 35px 30px;">
      <div style="background:#f8fafc;border-left:4px solid {accent};padding:20px;border-radius:0 8px 8px 0;color:#374151;font-size:14px;line-height:1.8;font-family:Arial,sans-serif;">
        {analyse_html}
      </div>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:20px 35px;text-align:center;">
      <div style="color:#94a3b8;font-size:11px;font-family:Arial,sans-serif;">VeilleNumerique · {conteneur_name} · {label} · {date_str}</div>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    return _send_email(subject, html, log_fn, f"{conteneur_name}/{couche}")
