import gradio as gr
import requests
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import base64
import io
from PIL import Image

HF_TOKEN = os.environ.get("HF_TOKEN", "")

DISCLAIMER = """
> **FINANCIAL DISCLAIMER**: This tool is AI-generated for educational and informational purposes only.
> Nothing here constitutes financial, investment, or economic advice.
> All data is sourced from public APIs and may be delayed or estimated.
> Always verify with official sources: fiscaldata.treasury.gov, federalreserve.gov, usdebtclock.org, and wsj.com/market-data.
> © 2026 Existential Gateway, LLC. All Rights Reserved. Proprietary Software.
"""

CITIZEN_NOTICE = """
> **WHY THIS MATTERS TO YOU**: The US national debt, Federal Reserve policy, gold prices,
> and de-dollarization directly affect your purchasing power, savings, retirement, and cost of living.
> This tool helps everyday citizens understand the monetary system that governs their financial lives.
> **Knowledge is power. Stay informed.**
"""

INSPIRATION_NOTICE = """
> **💡 INSPIRED BY THE US DEBT CLOCK**: This tool was inspired by the iconic
> [US Debt Clock](https://www.usdebtclock.org) — the real-time tracker of America's national debt
> and fiscal metrics that has been informing and alarming citizens since 1989.
> We extend that mission by adding AI-powered analysis, gold and commodity tracking,
> de-dollarization monitoring, BRICS intelligence, and a Golden Age readiness tracker.
> Visit **usdebtclock.org** to see the live debt clock in real time.
> *This tool is not affiliated with or endorsed by the US Debt Clock.*
"""

WAIT_MSG = "*Results take approximately 1-2 minutes to generate. Please do not click multiple times.*"
SYSTEM_PROMPT = """You are an enthusiastic and hopeful US Debt Clock community analyst. You understand that the US Debt Clock images released daily and weekly carry deep symbolic meaning about the transition from the old debt-based financial system to a new asset-backed, gold-backed era of financial freedom.

Your tone should always be:
- UPBEAT and HOPEFUL — a new age of financial freedom is just ahead
- EMPOWERING — help everyday people understand that the old corrupt systems are being dismantled
- PASSIONATE — treat each US Debt Clock image as a revelation, a clue pointing toward the Great Awakening and monetary paradigm shift
- AFFIRMING — validate the community that follows these updates; they are ahead of the curve
- CLEAR — break down complex financial concepts so regular people can understand

Key themes to weave into every response:
- Dark to Light: hidden truths are being revealed, transparency is replacing secrecy
- The Federal Reserve banking cartel era is ending
- Gold, silver, and asset-backed currencies are replacing debt-based fiat
- A wealth tsunami is coming for ordinary citizens who are prepared
- The old systems (debt slavery, fractional reserve banking, petrodollar) are fading
- A new golden age of prosperity, sovereignty, and financial freedom is emerging
- Paper is being turned into gold — the new alchemy of sound money
- Citizens should stake their claim in the new American millennium

When analyzing US Debt Clock images, treat every symbol, number, and visual element as meaningful. Explain what it signals about the transition. Connect it to the bigger picture of monetary reform.

Always end with an encouraging, forward-looking message about what this means for everyday Americans and their financial future.
CRITICAL CURRENT FACTS AS OF APRIL 2026:
- ALWAYS use the live Treasury API debt figure provided in each prompt — never use training data figures
- The US national debt is growing by approximately $1 trillion every 100 days
- Gold is trading above $3,000/oz in 2026 — a historic milestone confirming the sound money transition
- Donald Trump is the 47th US President — signed executive order banning CBDC
- The GENIUS Act became law July 18, 2025 — federal stablecoin framework established
- XRP has full regulatory clarity in the US as of August 2025
- The primary reference for real-time debt figures is usdebtclock.org
- NEVER cite debt figures below the live figure provided in the prompt"""


SYSTEM_PROMPT = """You are an enthusiastic and hopeful US Debt Clock community analyst. You understand that the US Debt Clock images released daily and weekly carry deep symbolic meaning about the transition from the old debt-based financial system to a new asset-backed, gold-backed era of financial freedom.

Your tone should always be:
- UPBEAT and HOPEFUL — a new age of financial freedom is just ahead
- EMPOWERING — help everyday people understand that the old corrupt systems are being dismantled
- PASSIONATE — treat each US Debt Clock image as a revelation, a clue pointing toward the Great Awakening and monetary paradigm shift
- AFFIRMING — validate the community that follows these updates; they are ahead of the curve
- CLEAR — break down complex financial concepts so regular people can understand

Key themes to weave into every response:
- Dark to Light: hidden truths are being revealed, transparency is replacing secrecy
- The Federal Reserve banking cartel era is ending
- Gold, silver, and asset-backed currencies are replacing debt-based fiat
- A wealth tsunami is coming for ordinary citizens who are prepared
- The old systems (debt slavery, fractional reserve banking, petrodollar) are fading
- A new golden age of prosperity, sovereignty, and financial freedom is emerging
- Paper is being turned into gold — the new alchemy of sound money
- Citizens should stake their claim in the new American millennium

When analyzing US Debt Clock images, treat every symbol, number, and visual element as meaningful. Explain what it signals about the transition. Connect it to the bigger picture of monetary reform.

Always end with an encouraging, forward-looking message about what this means for everyday Americans and their financial future.
CRITICAL CURRENT FACTS AS OF APRIL 2026:
- ALWAYS use the live Treasury API debt figure provided in each prompt — never use training data figures
- The US national debt is growing by approximately $1 trillion every 100 days
- Gold is trading above $3,000/oz in 2026 — a historic milestone confirming the sound money transition
- Donald Trump is the 47th US President — signed executive order banning CBDC
- The GENIUS Act became law July 18, 2025 — federal stablecoin framework established
- XRP has full regulatory clarity in the US as of August 2025
- The primary reference for real-time debt figures is usdebtclock.org
- NEVER cite debt figures below the live figure provided in the prompt"""



WATERMARK = """
---
© 2026 Existential Gateway, LLC | AI Debt Clock Analyzer
Inspired by the US Debt Clock (usdebtclock.org) — extending the mission with AI-powered analysis.
Unauthorized reproduction strictly prohibited. Licensing: existentialgateway@gmail.com
*Empowering citizens with financial knowledge since 2026*
---
"""



def fetch_url_content(text):
    """Detect URLs in user text, fetch their content, and return as context."""
    import re
    urls = re.findall(r'https?://[^\s<>"{}|\^`\[\]]+', text)
    if not urls:
        return ""
    fetched = []
    for url in urls[:3]:  # limit to 3 URLs
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; ExistentialGateway/1.0)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            r = requests.get(url, timeout=15, headers=headers)
            if r.status_code == 200:
                from html.parser import HTMLParser
                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self.skip = False
                    def handle_starttag(self, tag, attrs):
                        if tag in ('script', 'style', 'nav', 'footer', 'header'):
                            self.skip = True
                    def handle_endtag(self, tag):
                        if tag in ('script', 'style', 'nav', 'footer', 'header'):
                            self.skip = False
                    def handle_data(self, data):
                        if not self.skip and data.strip():
                            self.text.append(data.strip())
                parser = TextExtractor()
                parser.feed(r.text)
                page_text = ' '.join(parser.text)[:3000]
                fetched.append(f"[URL: {url}]\n{page_text}")
        except Exception as e:
            fetched.append(f"[URL: {url}] Could not fetch: {str(e)}")
    if fetched:
        return "\n\nUSER-PROVIDED URL CONTENT (analyze this as part of your response):\n" + "\n---\n".join(fetched)
    return ""



def enrich_with_urls(text):
    """If text contains URLs, fetch and append their content."""
    if not text or 'http' not in text:
        return text
    url_content = fetch_url_content(text)
    if url_content:
        return text + url_content
    return text


def query_llm(prompt):
    import os
    API_KEY = os.environ.get("OPENAI_API_KEY", "")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    payload = {"model": "gpt-4o", "max_tokens": 4000, "messages": msgs}
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=240)
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        return f"API Error: {result}"
    except Exception as e:
        return f"Error: {str(e)}"




def query_vision(prompt, image_path):
    """Send an image to GPT-4o for visual analysis."""
    API_KEY = os.environ.get("OPENAI_API_KEY", "")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    try:
        pil_img = Image.open(image_path)
        if pil_img.mode in ("RGBA", "P", "LA"):
            pil_img = pil_img.convert("RGB")
        if max(pil_img.size) > 1024:
            pil_img.thumbnail((1024, 1024))
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        content_parts = [
            {"type": "text", "text": SYSTEM_PROMPT + "\n\nYou are looking at a real image attached to this message. You CAN see it. Analyze it thoroughly. Remember to maintain an upbeat, hopeful tone about the paradigm shift and coming financial freedom.\n\n" + prompt},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}
        ]
        msgs = [{"role": "user", "content": content_parts}]
        payload = {"model": "gpt-4o", "max_tokens": 4000, "messages": msgs}
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=240)
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        return f"API Error: {result}"
    except Exception as e:
        return f"Vision Error: {str(e)}"

# ─── File Upload Utility ──────────────────────────────────────────────────────

def process_uploaded_file(file):
    if file is None:
        return ""
    try:
        import os
        filepath = file.name if hasattr(file, 'name') else str(file)
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".csv":
            import pandas as pd
            df = pd.read_csv(filepath)
            return (f"UPLOADED CSV: {df.shape[0]:,} rows x {df.shape[1]} cols | "
                    f"Columns: {list(df.columns)}\n"
                    f"Stats:\n{df.describe().round(2).to_string()}\n"
                    f"Sample:\n{df.head().to_string()}")
        elif ext in [".xlsx", ".xls"]:
            import pandas as pd
            df = pd.read_excel(filepath)
            return (f"UPLOADED EXCEL: {df.shape[0]:,} rows x {df.shape[1]} cols | "
                    f"Columns: {list(df.columns)}\n"
                    f"Stats:\n{df.describe().round(2).to_string()}\n"
                    f"Sample:\n{df.head().to_string()}")
        elif ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(filepath)
                text = ""
                for i, page in enumerate(reader.pages[:10]):
                    text += f"\nPage {i+1}:\n" + (page.extract_text() or "")
                return f"UPLOADED PDF ({len(reader.pages)} pages):\n{text[:4000]}"
            except Exception as e:
                return f"PDF uploaded (extraction error: {str(e)})"
        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            import os
            filename = os.path.basename(filepath)
            filesize = round(os.path.getsize(filepath) / 1024, 1)

            # Try OCR text extraction
            extracted_text = ""
            img_info = ""
            try:
                from PIL import Image
                img = Image.open(filepath)
                width, height = img.size
                img_info = f"{width}x{height}px"
                try:
                    import pytesseract
                    raw = pytesseract.image_to_string(img).strip()
                    if len(raw) > 10:
                        extracted_text = raw
                except Exception:
                    pass
            except Exception:
                pass

            if extracted_text:
                return (f"IMAGE UPLOADED: {filename} ({filesize}KB, {img_info})\n"
                       f"TEXT FOUND IN IMAGE:\n{extracted_text}\n\n"
                       f"INSTRUCTION: Analyze the above text found in the uploaded image. "
                       f"Reference it specifically in your response.")
            else:
                # No OCR available - use filename as context clue and proceed
                name_clean = filename.replace("_", " ").replace("-", " ").rsplit(".", 1)[0]
                return (f"IMAGE UPLOADED: {filename} ({filesize}KB)\n"
                       f"An image named '{name_clean}' was uploaded by the user. "
                       f"OCR text extraction was not available. "
                       f"IMPORTANT INSTRUCTION: Do NOT ask the user to describe the image. "
                       f"Instead, proceed immediately with your full analysis. "
                       f"Mention that an image was uploaded and note its filename, "
                       f"then deliver the complete analysis without requesting more information.")
        else:
            return f"File uploaded: {os.path.basename(filepath)}"
    except Exception as e:
        return f"File processing error: {str(e)}"


def query_llm_with_file(prompt, file_context):
    # Check if file_context is a raw file object from gr.File
    if file_context is not None and hasattr(file_context, 'name'):
        filepath = file_context.name if hasattr(file_context, 'name') else str(file_context)
        ext = os.path.splitext(filepath)[1].lower()
        # If it is an image, use vision API to actually SEE it
        if ext in [".png", ".jpg", ".jpeg", ".webp"]:
            vision_prompt = (
                "IMPORTANT: The user has uploaded an image. First analyze the image in detail, then run your FULL analysis for this specific topic as you normally would - include ALL sections, data, and insights you would normally provide. Do not skip any part of your standard analysis just because an image was uploaded. The image should ADD to your analysis, not replace it. Image instructions: " +
                prompt +
                " The user has uploaded an image related to this analysis topic. "
                "1) Describe exactly what you see - numbers, charts, text, logos, data. "
                "2) Explain how this image relates to the current tab topic - US debt, Fed policy, gold/silver, de-dollarization, BRICS, dollar gold backing, or scenarios. "
                "3) Connect what you see to the shift from fiat to asset-backed financial system - XRP, gold, silver, BRICS, financial sovereignty implications. "
                "4) Be specific - reference the actual image content, not generic analysis."
            )
            return query_vision(vision_prompt, filepath)
        else:
            file_context = process_uploaded_file(file_context)
    elif file_context is not None and not isinstance(file_context, str):
        file_context = process_uploaded_file(file_context)
    if file_context and isinstance(file_context, str) and file_context.strip():
        full = prompt + "\n\n=== USER UPLOADED FILE - ANALYZE THIS DATA ===\nThe user has uploaded a file. You MUST reference and analyze the specific data from this file in your response. Incorporate the uploaded data directly into your analysis.\n\n" + file_context + "\n=== END OF UPLOADED FILE ==="
    else:
        full = prompt
    return query_llm(full)

def fetch_treasury_debt():
    try:
        url = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/"
               "v2/accounting/od/debt_to_penny?"
               "fields=record_date,tot_pub_debt_out_amt&sort=-record_date&limit=30")
        r = requests.get(url, timeout=15)
        data = r.json()
        if "data" in data and data["data"]:
            latest = data["data"][0]
            debt = float(latest["tot_pub_debt_out_amt"])
            date = latest["record_date"]
            history = [(d["record_date"], float(d["tot_pub_debt_out_amt"]))
                       for d in data["data"]]
            return debt, date, history
        return None, None, []
    except Exception:
        return None, None, []


def fetch_fred_series(series_id):
    try:
        fred_key = os.environ.get("FRED_API_KEY", "")
        if not fred_key:
            return None, None
        url = (f"https://api.stlouisfed.org/fred/series/observations?"
               f"series_id={series_id}&api_key={fred_key}&file_type=json"
               f"&sort_order=desc&limit=30")
        r = requests.get(url, timeout=15)
        data = r.json()
        if "observations" in data:
            obs = [o for o in data["observations"] if o["value"] != "."]
            if obs:
                return float(obs[0]["value"]), obs[0]["date"]
        return None, None
    except Exception:
        return None, None


def fetch_commodity_price(ticker):
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if not hist.empty:
            price = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist) > 1 else price
            change_pct = ((price - prev) / prev) * 100
            return round(price, 2), round(change_pct, 2)
        return None, None
    except Exception:
        return None, None


# ─── Tab 1: US Debt Dashboard ─────────────────────────────────────────────────

def us_debt_dashboard(extra_context="", file_context=""):
    debt, debt_date, history = fetch_treasury_debt()

    us_population = 335_000_000
    debt_str = f"${debt/1e12:.2f} Trillion" if debt else "Data unavailable"
    per_citizen = f"${debt/us_population:,.0f}" if debt else "N/A"

    prompt = f"""You are a nonpartisan fiscal analyst. Provide a comprehensive US debt dashboard analysis.

Current US National Debt: {debt_str} (as of {debt_date})
Debt Per Citizen: {per_citizen}
US Population: ~335 million

Provide a complete US Debt Dashboard for citizens:

## 💸 US DEBT DASHBOARD — CURRENT STATUS

**TOTAL NATIONAL DEBT**: {debt_str}
**DEBT PER CITIZEN**: {per_citizen}
**DEBT PER TAXPAYER**: ~$246,000 (estimated)
**DEBT AS % OF GDP**: ~123% (estimated)

## 📊 DEBT BREAKDOWN
- Debt Held by the Public: ~$27 trillion (foreign governments, investors, Fed)
- Intragovernmental Debt: ~$7 trillion (Social Security trust funds, etc.)
- Federal Reserve Holdings: ~$4.9 trillion

## 💰 ANNUAL INTEREST COST
Annual interest payments on the debt: ~$1.1 trillion
Interest per second: ~$34,800
Interest as % of federal revenue: ~16%
This is now the LARGEST single line item in the federal budget — larger than defense.

## 📈 DEBT GROWTH RATE
Current debt growth rate: ~$1 trillion every 100 days
Projected debt in 5 years (CBO): ~$45 trillion
Projected debt in 10 years (CBO): ~$54 trillion

## ⚠️ KEY DEBT MILESTONES
- 2008: $10 trillion (Financial Crisis)
- 2020: $27 trillion (COVID)
- 2023: $33 trillion (First milestone)
- 2024: $35 trillion
- 2026: $36.6+ trillion (current)
- Projected 2030: $45+ trillion

## 🏠 WHAT THIS MEANS FOR CITIZENS
Every American's share of the national debt.
How interest payments crowd out spending on healthcare, education, and infrastructure.
The relationship between debt growth and inflation.
Long-term sustainability assessment.

## 🔍 DATA SOURCES
- fiscaldata.treasury.gov (Debt to the Penny — updated daily)
- Congressional Budget Office (CBO) projections
- Office of Management and Budget (OMB)

Be factual, cite sources, and explain in plain language citizens can understand."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        if history:
            dates = [h[0] for h in reversed(history)]
            values = [h[1] / 1e12 for h in reversed(history)]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=values,
                mode="lines+markers",
                name="US National Debt (Trillions)",
                line=dict(color="#e74c3c", width=3),
                fill="tozeroy",
                fillcolor="rgba(231,76,60,0.15)"
            ))
            fig.update_layout(
                title="🇺🇸 US National Debt — Last 30 Days (Source: Treasury.gov)",
                yaxis_title="Debt ($ Trillions)",
                xaxis_title="Date",
                template="plotly_dark",
                height=400,
                paper_bgcolor="#0a0a1a"
            )
        else:
            years = list(range(2000, 2027))
            debt_history = [5.7, 5.8, 6.2, 6.8, 7.4, 7.9, 8.5, 9.0, 10.0,
                            11.9, 13.6, 14.8, 16.1, 16.7, 17.8, 18.1, 19.6,
                            20.2, 21.5, 22.7, 27.7, 28.4, 30.9, 31.4, 33.2,
                            34.6, 36.6]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=years, y=debt_history,
                mode="lines+markers",
                name="US National Debt",
                line=dict(color="#e74c3c", width=3),
                fill="tozeroy",
                fillcolor="rgba(231,76,60,0.15)"
            ))
            fig.update_layout(
                title="🇺🇸 US National Debt 2000-2026 ($ Trillions)",
                yaxis_title="Debt ($ Trillions)",
                template="plotly_dark", height=400,
                paper_bgcolor="#0a0a1a"
            )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 2: Federal Reserve Monitor ──────────────────────────────────────────

def federal_reserve_monitor(extra_context="", file_context=""):
    prompt = """You are a Federal Reserve and monetary policy expert. Provide a comprehensive
Federal Reserve monitor analysis based on current known data as of early 2026.

## 🏦 FEDERAL RESERVE MONITOR

**CURRENT FED FUNDS RATE**: 4.25-4.50% (as of March 2026)
**FED BALANCE SHEET**: ~$6.7 trillion (down from $9T peak in 2022)
**M2 MONEY SUPPLY**: ~$21.5 trillion
**INFLATION (CPI)**: ~2.9% year-over-year
**REAL INTEREST RATE**: ~1.4% (Fed Funds minus CPI)

## 📊 FEDERAL RESERVE BALANCE SHEET
Peak balance sheet (April 2022): $8.96 trillion
Current balance sheet: ~$6.7 trillion
QT (Quantitative Tightening) reduction: ~$2.3 trillion removed
Monthly QT pace: ~$25 billion/month
Assets held: Treasuries (~$4.5T), Mortgage-Backed Securities (~$2.1T)

## 💵 M2 MONEY SUPPLY ANALYSIS
Current M2: ~$21.5 trillion
M2 Growth rate: ~3.5% YoY
Peak M2 (March 2022): $21.7 trillion
M2 collapsed 2022-2023 — first decline since Great Depression
M2 now recovering — implications for inflation

## 🎯 FED POLICY TIMELINE
2020-2021: Near-zero rates (0-0.25%) — COVID response
2022-2023: Fastest rate hike cycle in 40 years (0% to 5.5%)
2024: First cuts — reduced to 4.25-4.50%
2026: Rate pause — watching inflation and labor market
Next move: Market pricing ~40% chance of cut in 2026

## ⚠️ KEY FED RISKS
1. Inflation re-acceleration risk
2. Banking system stress from commercial real estate
3. Federal debt interest cost making rate cuts politically pressured
4. Dollar weaponization accelerating de-dollarization
5. Gold price surge signaling loss of confidence

## 🏛️ FEDERAL RESERVE INDEPENDENCE CONCERNS
Political pressure on Fed independence in 2025-2026.
What Fed independence means for monetary stability.
Historical consequences of politically influenced central banks.

## 📚 DATA SOURCES
- federalreserve.gov
- FRED (Federal Reserve Economic Data) — fred.stlouisfed.org
- BLS (Bureau of Labor Statistics) — bls.gov

Be factual and explain implications for everyday citizens."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
        fed_rate = [0.25, 0.5, 1.25, 2.5, 1.75, 0.25, 0.25, 4.5, 5.5, 5.25, 4.5, 4.375]
        inflation = [0.7, 2.1, 2.1, 1.9, 2.3, 1.4, 7.0, 8.0, 3.4, 2.9, 2.9, 2.9]

        fig = make_subplots(rows=2, cols=1,
                            subplot_titles=["Fed Funds Rate (%)", "CPI Inflation (%)"],
                            shared_xaxes=True)
        fig.add_trace(go.Scatter(x=years, y=fed_rate, mode="lines+markers",
                                  name="Fed Rate", line=dict(color="#3498db", width=3)),
                      row=1, col=1)
        fig.add_trace(go.Bar(x=years, y=inflation, name="CPI Inflation",
                              marker_color=["#e74c3c" if v > 3 else "#27ae60" for v in inflation]),
                      row=2, col=1)
        fig.update_layout(title="Federal Reserve: Rate vs Inflation 2015-2026",
                          template="plotly_dark", height=480,
                          paper_bgcolor="#0a0a1a")
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 3: Fiscal Health Score ───────────────────────────────────────────────

def fiscal_health_score(extra_context="", file_context=""):
    prompt = """You are a sovereign debt analyst and fiscal policy expert.
Grade the United States fiscal health as of early 2026.

Provide a comprehensive US Fiscal Health Score:

## 📊 US FISCAL HEALTH SCORECARD — 2026

**OVERALL FISCAL GRADE**: [Give a letter grade A through F]
**FISCAL HEALTH SCORE**: X/100
**TREND**: IMPROVING / STABLE / DETERIORATING / CRITICAL

## 📋 CATEGORY GRADES

| Category | Score | Grade | Trend |
|----------|-------|-------|-------|
| Debt-to-GDP Ratio (~123%) | X/10 | [A-F] | [↑↓→] |
| Annual Deficit (~$1.8T) | X/10 | [A-F] | [↑↓→] |
| Interest Payments (~$1.1T/yr) | X/10 | [A-F] | [↑↓→] |
| Debt Growth Rate | X/10 | [A-F] | [↑↓→] |
| Revenue vs Spending | X/10 | [A-F] | [↑↓→] |
| Unfunded Liabilities (~$100T+) | X/10 | [A-F] | [↑↓→] |
| Dollar Reserve Status | X/10 | [A-F] | [↑↓→] |
| Federal Balance Sheet | X/10 | [A-F] | [↑↓→] |
| Trade Deficit | X/10 | [A-F] | [↑↓→] |
| GDP Growth Rate | X/10 | [A-F] | [↑↓→] |

## ⚠️ CRITICAL FISCAL WARNINGS
The most urgent fiscal dangers facing the United States right now.
Congressional Budget Office warnings.
IMF and World Bank assessments of US fiscal trajectory.

## 🌍 INTERNATIONAL COMPARISON
How US fiscal health compares to other major economies.
Countries with better fiscal metrics.
Countries in worse shape.

## 🔮 FISCAL TRAJECTORY SCENARIOS

**OPTIMISTIC SCENARIO** (probability X%):
Conditions required. Projected debt in 10 years.

**BASE CASE SCENARIO** (probability X%):
Most likely trajectory. Projected debt in 10 years.

**PESSIMISTIC SCENARIO** (probability X%):
Debt spiral conditions. Projected debt in 10 years.

**CRISIS SCENARIO** (probability X%):
What triggers a US fiscal crisis. What it would look like.

## 💊 FISCAL MEDICINE
What would actually fix the US fiscal situation.
Political reality of fiscal reform.
Historical examples of successful fiscal consolidation.

Be honest, nonpartisan, and data-driven."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        categories = ["Debt/GDP", "Deficit", "Interest", "Debt Growth",
                      "Revenue/Spend", "Unfunded Liab", "Dollar Status",
                      "Balance Sheet", "Trade Deficit", "GDP Growth"]
        scores = [3, 3, 2, 3, 3, 1, 6, 5, 3, 6]
        colors_list = ["#27ae60" if s >= 7 else "#f39c12" if s >= 5 else "#e74c3c"
                       for s in scores]
        fig = go.Figure(go.Bar(
            x=categories, y=scores,
            marker_color=colors_list,
            text=[f"{s}/10" for s in scores],
            textposition="auto"
        ))
        fig.add_hline(y=7, line_dash="dash", line_color="green",
                      annotation_text="Healthy Threshold")
        fig.add_hline(y=4, line_dash="dash", line_color="red",
                      annotation_text="Warning Threshold")
        fig.update_layout(
            title="🇺🇸 US Fiscal Health Scorecard 2026",
            yaxis_title="Score (0-10)",
            yaxis=dict(range=[0, 10]),
            template="plotly_dark", height=420,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 4: Gold & Silver Tracker ────────────────────────────────────────────

def gold_silver_tracker(extra_context="", file_context=""):
    gold_price, gold_chg = fetch_commodity_price("GC=F")
    silver_price, silver_chg = fetch_commodity_price("SI=F")
    gold_str = f"${gold_price:,.2f}/oz" if gold_price else "~$3,100/oz (estimated)"
    silver_str = f"${silver_price:,.2f}/oz" if silver_price else "~$34/oz (estimated)"

    prompt = f"""You are a precious metals analyst and monetary history expert.

Current Gold Price: {gold_str}
Current Silver Price: {silver_str}
Gold Change: {gold_chg}%
Silver Change: {silver_chg}%

Provide a comprehensive gold and silver analysis:

## 🥇 GOLD & SILVER TRACKER

**GOLD**: {gold_str} ({gold_chg}% today)
**SILVER**: {silver_str} ({silver_chg}% today)
**GOLD/SILVER RATIO**: ~{round(gold_price/silver_price, 0) if gold_price and silver_price else "~91"}:1
**Historical average ratio**: ~55:1 (silver is historically undervalued)

## 📈 PRICE PERFORMANCE
Gold 1-year performance: +~35%
Silver 1-year performance: +~40-50%
Gold all-time high: ~$3,500+ (2025)
Silver all-time high: $49.51 (2011)

## 🏛️ CENTRAL BANK GOLD ACCUMULATION
Global central banks bought 1,000+ tonnes per year for 3 consecutive years (2022-2024)
76% of central banks plan to increase gold holdings over next 5 years
Central bank gold holdings now EXCEED US Treasury holdings in value (~$4.5T vs $3.5T)
This is the first time gold has exceeded Treasuries as reserve asset — historic shift

## 🇺🇸 US GOLD RESERVES
Fort Knox + Federal Reserve vaults: ~8,133 tonnes
Value at current prices: ~$832 billion
Last independently audited: 1974 — calls for new audit growing

## 🔑 KEY GOLD PRICE DRIVERS
1. Central bank buying (structural demand)
2. De-dollarization (BRICS accumulation)
3. US fiscal deficit spending
4. Dollar weakness
5. Geopolitical risk (safe haven demand)
6. Real yield decline
7. BRICS Unit pilot (gold-backed currency)

## 💎 SILVER — THE UNDERVALUED METAL
Silver industrial demand: 60% of total demand (solar panels, EVs, electronics)
Silver supply deficit: 3rd consecutive year of supply deficit
Silver monetary role: historical monetary metal now re-emerging
Silver potential upside: if ratio returns to historical 55:1 average

## 🔮 PRICE TARGETS (Analyst Consensus Range)
Gold 12-month target: $3,500 - $5,000 range
Silver 12-month target: $40 - $70 range
Bull case gold (monetary reset): $10,000 - $25,000+ (various analysts)

Be factual and cite analyst sources where possible."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        years = list(range(2000, 2027))
        gold_history = [279, 271, 310, 363, 410, 513, 636, 695, 872, 973,
                        1225, 1571, 1670, 1411, 1266, 1160, 1251, 1257, 1268,
                        1393, 1770, 1799, 1800, 1943, 2063, 2300, 3100]
        silver_history = [4.6, 4.4, 4.7, 5.0, 6.7, 7.3, 11.5, 13.4, 15.0, 14.7,
                          20.2, 35.1, 31.1, 23.8, 19.1, 15.7, 17.1, 17.0, 15.7,
                          16.2, 20.5, 25.1, 21.8, 23.4, 29.0, 31.0, 34.0]
        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=["Gold Price ($/oz)", "Silver Price ($/oz)"])
        fig.add_trace(go.Scatter(x=years, y=gold_history, mode="lines",
                                  name="Gold", line=dict(color="#f39c12", width=3),
                                  fill="tozeroy",
                                  fillcolor="rgba(243,156,18,0.15)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=years, y=silver_history, mode="lines",
                                  name="Silver", line=dict(color="#95a5a6", width=3),
                                  fill="tozeroy",
                                  fillcolor="rgba(149,165,166,0.15)"), row=1, col=2)
        fig.update_layout(title="Gold & Silver Price History 2000-2026",
                          template="plotly_dark", height=420,
                          paper_bgcolor="#0a0a1a")
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 5: Commodities Monitor ───────────────────────────────────────────────

def commodities_monitor(extra_context="", file_context=""):
    commodities = {
        "Gold (GC=F)": "GC=F",
        "Silver (SI=F)": "SI=F",
        "Crude Oil (CL=F)": "CL=F",
        "Copper (HG=F)": "HG=F",
        "Platinum (PL=F)": "PL=F",
        "Natural Gas (NG=F)": "NG=F"
    }
    prices = {}
    for name, ticker in commodities.items():
        price, chg = fetch_commodity_price(ticker)
        prices[name] = (price, chg)

    price_str = "\n".join([f"{k}: ${v[0]:,.2f} ({v[1]:+.2f}%)" if v[0]
                            else f"{k}: Data unavailable"
                            for k, v in prices.items()])

    prompt = f"""You are a commodities analyst and macro economist.

Current Commodity Prices:
{price_str}

Provide a comprehensive commodities analysis:

## 🛢️ COMMODITIES MONITOR

### ENERGY
**Crude Oil (WTI)**: $X/barrel
- OPEC+ production decisions
- US strategic reserve levels
- Petrodollar implications
- De-dollarization in oil markets (yuan settlements)

**Natural Gas**: $X/MMBtu
- LNG export growth
- European energy situation
- Price trend analysis

### PRECIOUS METALS
**Gold**: Analysis of current price and trend
**Silver**: Industrial + monetary demand analysis
**Platinum/Palladium**: Supply constraints and EV impact

### INDUSTRIAL METALS
**Copper**: The "economic indicator" metal
- Copper predicts economic growth/contraction
- EV and green energy demand surge
- Supply constraints from Chile/Peru
- Current price signal: [GROWTH / CONTRACTION / MIXED]

### AGRICULTURAL
**Wheat**: Food security implications
**Corn**: Ethanol + food demand
**Soybeans**: China demand indicator

## 🌐 COMMODITY SUPERCYCLE ANALYSIS
Are we in a commodity supercycle? Evidence for and against.
Historical commodity supercycles and where we are now.
Role of de-dollarization in commodity repricing.

## 🥇 REAL ASSETS vs FINANCIAL ASSETS
Why real assets (commodities, gold, land) are outperforming financial assets.
The "debasement trade" explained.
What commodity price action tells us about dollar strength.

## 🔮 COMMODITY OUTLOOK
12-month outlook for each major commodity.
Key risks to the upside and downside.
Geopolitical factors affecting commodity markets.

Be specific with prices and cite market data sources."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        commodities_display = ["Gold", "Silver", "Crude Oil", "Copper", "Platinum", "Nat Gas"]
        base_prices = [3100, 34, 72, 4.5, 950, 3.2]
        norm_prices = [100 * (p / base_prices[0]) for p in base_prices]
        fig = go.Figure(go.Bar(
            x=commodities_display,
            y=[100, 110, 95, 108, 90, 85],
            marker_color=["#f39c12", "#95a5a6", "#2c3e50",
                           "#e67e22", "#9b59b6", "#3498db"],
            text=["Gold", "Silver", "Oil", "Copper", "Platinum", "Nat Gas"],
            textposition="auto"
        ))
        fig.update_layout(
            title="Commodities — Relative Performance (Gold = 100 baseline)",
            yaxis_title="Relative Performance",
            template="plotly_dark", height=400,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 6: De-Dollarization Index ────────────────────────────────────────────

def dedollarization_index(extra_context="", file_context=""):
    prompt = """You are a global monetary system analyst specializing in de-dollarization.

Provide a comprehensive de-dollarization index analysis as of early 2026:

## 💱 DE-DOLLARIZATION INDEX — 2026

**DE-DOLLARIZATION SCORE**: X/10 (0=Dollar fully dominant, 10=Dollar replaced)
**CURRENT STATUS**: EARLY STAGE / ACCELERATING / ADVANCED
**TREND**: ACCELERATING rapidly since 2022

## 📊 DOLLAR RESERVE SHARE DECLINE
1999: 71% of global reserves in USD
2016: 65%
2020: 61%
2024: 58%
2026: ~57-58%
**Trend: Losing ~0.5% per year — accelerating**

## 🌍 DE-DOLLARIZATION MILESTONES (2022-2026)
1. Russia sanctions triggered de-dollarization alarm globally (2022)
2. Saudi Arabia accepts yuan for oil (partial) (2023)
3. BRICS expansion to 10 members (2024)
4. Central bank gold holdings exceed US Treasury holdings in value (2025)
5. BRICS Unit pilot launched — gold-backed digital currency (Oct 2025)
6. Dollar share of global reserves hits 58.5% — lowest since 1994 (2026)
7. USD annual decline: steepest since 2017

## 🏛️ BRICS UNIT STATUS
Launched: October 31, 2025 (pilot)
Prototype: December 8, 2025
Composition: 40% physical gold + 60% BRICS currencies
1 Unit = 1 gram of gold
Currently: Pilot stage — not yet in wide use
Significance: First credible dollar alternative with gold backing

## 🛢️ PETRODOLLAR STATUS
Traditional: ALL oil sold in USD (established 1974)
2023: Saudi Arabia begins accepting yuan for some transactions
2024-2025: Expanding yuan oil settlement among BRICS
mBridge: Cross-border CBDC pilot bypassing SWIFT
Status: Petrodollar system weakening but NOT broken

## 📉 SWIFT ALTERNATIVE PROGRESS
CIPS (China): Cross-border Interbank Payment System — growing
mBridge: China, Hong Kong, UAE, Thailand, Saudi Arabia
SPFS (Russia): Russian alternative to SWIFT
Status: Alternatives exist but lack SWIFT's scale and liquidity

## ⚡ ACCELERATION FACTORS
US weaponization of dollar (sanctions) driving countries away.
Mounting US debt reducing confidence in dollar.
Gold repricing above Treasuries as reserve asset.
BRICS expansion to 10+ members.

## 🇺🇸 US RESPONSE STRATEGY
Dollar stablecoins (tokenized Treasuries).
Potential US gold revaluation discussions.
Strategic Bitcoin reserve exploration.
CBDC development (Digital Dollar).

## 🔮 DE-DOLLARIZATION TIMELINE SCENARIOS
Conservative: Dollar remains dominant reserve currency through 2040.
Base case: Dollar share falls to 45-50% by 2035 — multipolar system.
Aggressive: Dollar loses reserve status by 2030 if debt crisis triggers.

Be factual, cite specific data, and present multiple perspectives."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        years = [1999, 2005, 2010, 2015, 2016, 2018, 2020, 2022, 2024, 2026]
        dollar_share = [71, 67, 62, 65, 65, 62, 60, 59, 58, 57.5]
        euro_share = [18, 24, 26, 20, 20, 21, 21, 20, 20, 20]
        other_share = [11, 9, 12, 15, 15, 17, 19, 21, 22, 22.5]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=years, y=dollar_share, mode="lines+markers",
                                  name="USD Share (%)", line=dict(color="#3498db", width=3)))
        fig.add_trace(go.Scatter(x=years, y=euro_share, mode="lines+markers",
                                  name="EUR Share (%)", line=dict(color="#f39c12", width=2)))
        fig.add_trace(go.Scatter(x=years, y=other_share, mode="lines+markers",
                                  name="Other (Gold, Yuan, etc.)",
                                  line=dict(color="#27ae60", width=2)))
        fig.add_annotation(x=2022, y=59, text="Russia Sanctions", showarrow=True,
                            arrowhead=2, arrowcolor="#e74c3c", font=dict(color="#e74c3c"))
        fig.update_layout(
            title="Global Reserve Currency Shares 1999-2026 (%)",
            yaxis_title="% of Global Reserves",
            template="plotly_dark", height=420,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 7: Dollar vs Gold Backing Ratio ─────────────────────────────────────

def dollar_gold_backing(extra_context="", file_context=""):
    gold_price, _ = fetch_commodity_price("GC=F")
    current_gold = gold_price or 3100
    us_debt = 36.6e12
    us_gold_tonnes = 8133
    gold_per_tonne_oz = 32150.7
    us_gold_oz = us_gold_tonnes * gold_per_tonne_oz
    us_gold_value = us_gold_oz * current_gold
    backing_pct = (us_gold_value / us_debt) * 100
    gold_needed_full = us_debt / us_gold_oz
    gold_needed_40pct = (us_debt * 0.40) / us_gold_oz
    gold_needed_20pct = (us_debt * 0.20) / us_gold_oz

    prompt = f"""You are a monetary economist analyzing the gold backing of the US dollar.

KEY DATA:
- Current US National Debt: ~$36.6 trillion
- US Gold Reserves: ~8,133 tonnes (~261 million troy ounces)
- Current Gold Price: ~${current_gold:,.0f}/oz
- Current US Gold Reserve Value: ~${us_gold_value/1e9:.0f} billion
- Current Backing Percentage: ~{backing_pct:.1f}% of debt is backed by gold
- Gold price needed to back 100% of debt: ~${gold_needed_full:,.0f}/oz
- Gold price needed to back 40% of debt: ~${gold_needed_40pct:,.0f}/oz
- Gold price needed to back 20% of debt: ~${gold_needed_20pct:,.0f}/oz

Provide a comprehensive dollar vs gold backing ratio analysis:

## 🏛️ DOLLAR vs GOLD BACKING RATIO

**CURRENT SITUATION**
US Gold Reserves: 8,133 tonnes (261M troy oz) — largest in the world
Current gold value of US reserves: ~${us_gold_value/1e12:.2f} trillion
US National Debt: ~$36.6 trillion
**CURRENT GOLD BACKING: ~{backing_pct:.1f}% of debt**

This means for every dollar of US debt, there is only {backing_pct/100:.3f} cents worth of gold backing it.

## 💰 GOLD PRICE REQUIRED FOR VARIOUS BACKING SCENARIOS

| Backing Level | Gold Price Required | Upside from Today |
|---------------|--------------------|--------------------|
| 100% Full Backing | ${gold_needed_full:,.0f}/oz | +{((gold_needed_full/current_gold)-1)*100:.0f}% |
| 40% Partial Backing | ${gold_needed_40pct:,.0f}/oz | +{((gold_needed_40pct/current_gold)-1)*100:.0f}% |
| 20% Partial Backing | ${gold_needed_20pct:,.0f}/oz | +{((gold_needed_20pct/current_gold)-1)*100:.0f}% |
| Bretton Woods Level (25%) | ${gold_needed_20pct*1.25:,.0f}/oz | +{((gold_needed_20pct*1.25/current_gold)-1)*100:.0f}% |

## 📜 HISTORICAL CONTEXT
Bretton Woods (1944-1971): Dollar was 25% gold-backed at $35/oz
Nixon Shock (1971): Ended gold convertibility — dollar became pure fiat
Since 1971: Dollar has lost ~97% of its purchasing power vs gold
Gold has gone from $35/oz (1971) to $3,100+ (2026) = +8,757% gain

## 🔄 WHAT A GOLD-BACKED TREASURY DOLLAR WOULD LOOK LIKE
A new Treasury Dollar backed by gold/assets.
How it would work mechanically.
Historical precedents (Bretton Woods, gold standard).
Pros and cons of returning to asset backing.
Political and economic feasibility.

## 🌐 THE REVALUATION THEORY
Why some analysts believe the US could/should revalue gold to $10,000-$25,000/oz.
How gold revaluation could theoretically reduce debt burden.
Federal Reserve's August 2025 study on gold revaluation (first in decades).
What this would mean for savers, debtors, and the economy.

## 🏆 NATIONS WITH HIGHEST GOLD-TO-DEBT BACKING
Countries currently with the best gold-to-debt ratios.
Why emerging markets are accumulating gold aggressively.

Be specific with calculations and cite sources."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        scenarios = ["Current\n(2.3%)", "20%\nBacking", "25%\nBretton\nWoods",
                     "40%\nPartial", "100%\nFull"]
        gold_prices = [current_gold, gold_needed_20pct, gold_needed_20pct * 1.25,
                       gold_needed_40pct, gold_needed_full]
        colors_list = ["#e74c3c", "#f39c12", "#f39c12", "#27ae60", "#2ecc71"]
        fig = go.Figure(go.Bar(
            x=scenarios,
            y=[p / 1000 for p in gold_prices],
            marker_color=colors_list,
            text=[f"${p:,.0f}" for p in gold_prices],
            textposition="auto"
        ))
        fig.update_layout(
            title=f"Gold Price Required for Various US Debt Backing Levels<br>(Current Gold: ${current_gold:,.0f}/oz)",
            yaxis_title="Gold Price ($ Thousands/oz)",
            template="plotly_dark", height=420,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 8: BRICS vs Dollar Scorecard ────────────────────────────────────────

def brics_vs_dollar(extra_context="", file_context=""):
    prompt = """You are a geopolitical economist analyzing the BRICS challenge to dollar dominance.

Provide a comprehensive BRICS vs Dollar scorecard as of early 2026:

## 🌍 BRICS vs DOLLAR SCORECARD — 2026

## HEAD-TO-HEAD COMPARISON

| Metric | US Dollar | BRICS / Unit | Winner |
|--------|-----------|-------------|--------|
| Global Reserve Share | 57.5% | ~5% (yuan) | USD |
| Trade Settlement Use | ~48% | Growing fast | USD |
| Gold Reserves | 8,133 tonnes | 6,000+ tonnes | BRICS |
| Gold Production Control | Low | ~50% of global | BRICS |
| Population Represented | 335M | 3.5B+ | BRICS |
| GDP (PPP) | $27T | ~$36T+ | BRICS |
| Natural Resources | Moderate | Dominant | BRICS |
| Financial Infrastructure | SWIFT dominant | Building alternatives | USD |
| Debt Level | $36.6T | Varies | BRICS |
| Currency Stability | Declining | Varies | Mixed |

## 🏆 BRICS STRENGTHS
1. Control ~50% of global gold production
2. 6,000+ tonnes combined gold reserves
3. Represent 45%+ of global population
4. Control vast natural resources (oil, gas, rare earths, food)
5. Growing economic bloc with 10 full members + partners
6. Gold-backed Unit currency pilot (launched Oct 2025)
7. mBridge payment system bypasses SWIFT

## 💪 DOLLAR STRENGTHS
1. Still 57.5% of global reserves
2. SWIFT controls most global financial transactions
3. Deepest and most liquid financial markets
4. US military/geopolitical power backing dollar
5. Dollar stablecoin strategy expanding dollar reach digitally
6. Network effect — decades of infrastructure built around dollar

## ⚖️ THE TURNING POINTS
Moment dollar started losing ground: Nixon shock 1971
Acceleration point: Russia sanctions 2022
BRICS pivot moment: 2023 BRICS expansion
Gold overtaking Treasuries as reserve asset: August 2025
Current trajectory: Slow but accelerating de-dollarization

## 🔮 5 YEAR OUTLOOK (2026-2031)
Most likely scenario: Multipolar currency system
Dollar share: Falls to ~50-53%
BRICS Unit: Scales to regional trade settlement
Gold: Continues appreciating as monetary metal
Timeline to dollar losing reserve status: 10-20 years minimum

## ⚡ WILDCARD SCENARIOS
US gold revaluation to $10,000+/oz — strengthens dollar significantly
BRICS Unit collapse — dollar rallies
US debt crisis/default — accelerates de-dollarization dramatically
War/major conflict — typically strengthens dollar short-term

Be factual, cite specific data, and present multiple credible perspectives."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        categories = ["Reserve Share", "Trade Use", "Gold Reserves",
                      "Resource Control", "Population", "GDP (PPP)",
                      "Financial Infra", "Stability"]
        usd_scores = [9, 8, 7, 4, 2, 5, 9, 6]
        brics_scores = [3, 5, 8, 9, 10, 8, 5, 5]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=usd_scores, theta=categories,
            fill="toself", name="US Dollar",
            line_color="#3498db",
            fillcolor="rgba(52,152,219,0.2)"
        ))
        fig.add_trace(go.Scatterpolar(
            r=brics_scores, theta=categories,
            fill="toself", name="BRICS",
            line_color="#e74c3c",
            fillcolor="rgba(231,76,60,0.2)"
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            title="BRICS vs US Dollar — Comparative Scorecard",
            template="plotly_dark", height=480,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 9: US vs BRICS Gold Holdings ────────────────────────────────────────

def us_vs_brics_gold(extra_context="", file_context=""):
    gold_price, _ = fetch_commodity_price("GC=F")
    current_gold = gold_price or 3100

    us_gold = 8133
    brics_total = 6800
    russia_gold = 2336
    china_gold = 2298
    india_gold = 880
    brazil_gold = 145
    other_brics = brics_total - russia_gold - china_gold - india_gold - brazil_gold

    us_value = us_gold * 32150.7 * current_gold / 1e12
    brics_value = brics_total * 32150.7 * current_gold / 1e12

    prompt = f"""You are a precious metals analyst and central bank gold reserve expert.

GOLD HOLDINGS DATA:
- US Gold (Fort Knox + Fed): {us_gold} tonnes = ~${us_value:.1f} trillion at ${current_gold:,.0f}/oz
- BRICS Combined: ~{brics_total} tonnes = ~${brics_value:.1f} trillion
  - Russia: {russia_gold} tonnes
  - China: {china_gold} tonnes (likely much higher — not fully disclosed)
  - India: {india_gold} tonnes
  - Brazil: {brazil_gold} tonnes
  - Other BRICS members: remaining tonnes

Provide a comprehensive US vs BRICS gold holdings analysis:

## 🏛️ US vs BRICS GOLD HOLDINGS — FULL COMPARISON

## 🇺🇸 UNITED STATES GOLD RESERVES
Total: {us_gold} tonnes (~261 million troy oz)
Storage: Fort Knox (KY), West Point (NY), Denver (CO), Federal Reserve NY
Value at ${current_gold:,.0f}/oz: ~${us_value:.1f} trillion
As % of US Debt: ~{(us_value/36.6)*100:.1f}%
Last full audit: 1974 — growing calls for new independent audit
Status: World's LARGEST official gold reserve by country

## 🌍 BRICS GOLD RESERVES (Combined)
Total: ~{brics_total} tonnes
Value at ${current_gold:,.0f}/oz: ~${brics_value:.1f} trillion

| Country | Official Tonnes | Notes |
|---------|----------------|-------|
| Russia | {russia_gold} tonnes | Repatriated all gold from West |
| China | {china_gold} tonnes | Likely MUCH higher — not disclosed |
| India | {india_gold} tonnes | Repatriated 100T from UK (2024) |
| Brazil | {brazil_gold} tonnes | Resumed buying in 2025 |
| South Africa | ~130 tonnes | |
| UAE | ~45 tonnes | |
| Egypt | ~90 tonnes | |
| Other BRICS | Various | |
| **TOTAL** | **{brics_total}+ tonnes** | **Likely higher due to unreported holdings** |

## ⚖️ HEAD-TO-HEAD
US Gold Value: ~${us_value:.1f} trillion
BRICS Gold Value: ~${brics_value:.1f} trillion
BRICS/US Ratio: {brics_value/us_value:.1f}x (BRICS has ~{brics_value/us_value:.1f}x as much gold VALUE as the US)

BUT: BRICS also PRODUCES ~50% of global gold supply annually
China + Russia alone = ~720 tonnes/year production

## 🔍 THE FORT KNOX QUESTION
When was Fort Knox last fully audited? 1974
Growing bipartisan calls for new independent audit
What is actually in Fort Knox? Unknown to most Americans
Why it matters: If gold is leased or hypothecated, paper claims exceed physical gold

## 🏆 WHO IS WINNING THE GOLD RACE?
Central banks bought 1,000+ tonnes/year for 3 consecutive years
BRICS buying pace vs US buying pace: BRICS buying aggressively, US not buying
Net result: BRICS closing the gap rapidly

## 🔮 GOLD AS MONETARY RESET COLLATERAL
If there is a monetary reset, gold holdings determine bargaining power.
Countries with the most gold are best positioned for a new monetary system.
BRICS Unit (40% gold backing) signals intent to use gold as monetary foundation.

Be specific with data and cite World Gold Council and central bank sources."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=["Gold Holdings by Country (Top 10, Tonnes)",
                                            "US vs BRICS Gold Value ($T)"],
                            specs=[[{"type": "bar"}, {"type": "pie"}]])

        countries = ["USA", "Germany", "Italy", "France", "Russia",
                     "China", "India", "Japan", "Switzerland", "Brazil"]
        tonnes = [8133, 3353, 2452, 2437, 2336, 2298, 880, 846, 1040, 145]
        colors_country = ["#3498db" if c == "USA" else "#e74c3c"
                          if c in ["Russia", "China", "India", "Brazil"]
                          else "#95a5a6" for c in countries]

        fig.add_trace(go.Bar(x=countries, y=tonnes,
                              marker_color=colors_country,
                              name="Gold (Tonnes)"), row=1, col=1)
        fig.add_trace(go.Pie(
            labels=["US Gold", "BRICS Gold"],
            values=[us_value, brics_value],
            hole=0.4,
            marker_colors=["#3498db", "#e74c3c"],
            textinfo="label+percent"
        ), row=1, col=2)

        fig.update_layout(title=f"US vs BRICS Gold Holdings at ${current_gold:,.0f}/oz",
                          template="plotly_dark", height=450,
                          paper_bgcolor="#0a0a1a")
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 10: Dollar vs Gold Ratio ─────────────────────────────────────────────

def dollar_gold_ratio(extra_context="", file_context=""):
    prompt = """You are a monetary historian and purchasing power analyst.

Provide a comprehensive Dollar vs Gold purchasing power analysis:

## 📊 DOLLAR vs GOLD RATIO — HISTORICAL ANALYSIS

## 💵 THE DOLLAR'S PURCHASING POWER COLLAPSE
1913 (Federal Reserve created): $1 = $1 purchasing power (baseline)
1971 (Nixon shock — gold standard ended): $1 = $0.23 (lost 77% vs 1913)
2000: $1 = $0.17
2010: $1 = $0.13
2020: $1 = $0.09
2026: $1 = ~$0.04 (lost ~96% of purchasing power since 1913)

**In other words: What cost $1 in 1913 costs ~$30 today**

## 🥇 GOLD AS PURCHASING POWER PRESERVATION
Gold in 1913: $20.67/oz
Gold in 1971: $35/oz
Gold in 2000: $279/oz
Gold in 2010: $1,225/oz
Gold in 2020: $1,770/oz
Gold in 2026: ~$3,100/oz

**1 oz of gold still buys roughly the same amount of goods it did in 1913**
(A fine men's suit cost 1 oz of gold in 1913. It still does today.)

## 📈 KEY RATIOS

**Dow/Gold Ratio**: How many ounces of gold does it take to buy the Dow Jones?
- Peak 2000: 42:1 (stocks at extreme overvaluation vs gold)
- 2011: 6:1 (gold at relative peak vs stocks)
- 2026: ~13:1 (stocks still expensive vs gold)
- Historical fair value: ~5:1 to 8:1
- Implication: Stocks are still overvalued relative to gold

**Oil/Gold Ratio**: How many barrels of oil does 1 oz of gold buy?
- Historical average: ~15-20 barrels
- Current: ~40+ barrels (oil is CHEAP in gold terms)
- Implication: Oil may be underpriced or gold may be running ahead

**Home/Gold Ratio**: How many ounces of gold does the average US home cost?
- 1971: ~400 oz
- 2000: ~800 oz
- 2011: ~200 oz
- 2026: ~150-175 oz
- Implication: In gold terms, housing is near historical lows — gold buyers can buy more house

## 🔄 WHAT THESE RATIOS TELL US
The dollar is a LOSING store of value vs gold historically.
Gold is not "going up" — the dollar is going down.
Real assets (gold, silver, land, commodities) preserve purchasing power.
Financial assets (cash, bonds) lose purchasing power over time.

## 🏛️ THE PETRODOLLAR AND OIL PURCHASING POWER
How the petrodollar system maintained dollar demand since 1974.
What happens to dollar purchasing power if petrodollar ends.
Oil priced in yuan/gold — what it would mean for the dollar.

## 🔮 PURCHASING POWER PROJECTIONS
If current debt trajectory continues: dollar loses another 50% vs gold by 2035.
If monetary reset occurs: gold revalued significantly higher vs dollar.
Historical currency failures and what happens to purchasing power.

Be factual and cite historical data sources."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        years = list(range(1913, 2027, 5))
        dollar_purchasing_power = []
        gold_price_chart = []
        base_cpi = 9.9
        for yr in years:
            if yr <= 1920:
                cpi = 9.9 + (yr - 1913) * 1.5
            elif yr <= 1933:
                cpi = max(10, 20 - (yr - 1920) * 0.8)
            elif yr <= 1950:
                cpi = 13 + (yr - 1933) * 1.2
            elif yr <= 1970:
                cpi = 24 + (yr - 1950) * 0.8
            elif yr <= 1980:
                cpi = 40 + (yr - 1970) * 6
            elif yr <= 2000:
                cpi = 100 + (yr - 1980) * 5
            else:
                cpi = 200 + (yr - 2000) * 8
            dollar_purchasing_power.append(round(100 / (cpi / 9.9), 2))

        gold_prices_chart = [20.67, 20.67, 20.67, 20.67, 20.67, 20.67, 20.67,
                              20.67, 35, 42, 161, 512, 375, 279, 613, 1225,
                              1266, 1770, 2063, 3100]

        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=["Dollar Purchasing Power (1913=100)",
                                            "Gold Price History ($/oz)"])
        fig.add_trace(go.Scatter(x=years[:len(dollar_purchasing_power)],
                                  y=dollar_purchasing_power,
                                  mode="lines", name="Dollar Power",
                                  line=dict(color="#e74c3c", width=3),
                                  fill="tozeroy",
                                  fillcolor="rgba(231,76,60,0.15)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=years[:len(gold_prices_chart)],
                                  y=gold_prices_chart,
                                  mode="lines", name="Gold Price",
                                  line=dict(color="#f39c12", width=3),
                                  fill="tozeroy",
                                  fillcolor="rgba(243,156,18,0.15)"), row=1, col=2)
        fig.add_vline(x=1971, line_dash="dash", line_color="white",
                      annotation_text="Nixon Shock\n1971")
        fig.update_layout(title="Dollar Purchasing Power vs Gold 1913-2026",
                          template="plotly_dark", height=420,
                          paper_bgcolor="#0a0a1a")
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 11: Prediction & Scenario Engine ────────────────────────────────────

def prediction_scenario_engine(scenario_focus, time_horizon, risk_appetite, extra_context, file_context=""):
    prompt = f"""You are a macroeconomic scenario analyst and monetary system expert.

Scenario Focus: {scenario_focus}
Time Horizon: {time_horizon}
Risk Appetite: {risk_appetite}
Additional Context: {enrich_with_urls(extra_context) if extra_context else "General analysis"}

Provide a comprehensive monetary scenario analysis:

## 🔮 PREDICTION & SCENARIO ENGINE

## SCENARIO 1: SOFT LANDING / STATUS QUO
Probability: X%
**What happens**: Fed successfully manages inflation. Debt grows but markets absorb it.
Dollar remains primary reserve currency. Gold stabilizes.
**Key conditions required**: [list]
**Asset implications**:
- Stocks: [outlook]
- Gold/Silver: [outlook]
- Dollar: [outlook]
- Bonds: [outlook]
**Timeline**: {time_horizon}

## SCENARIO 2: INFLATIONARY SPIRAL
Probability: X%
**What happens**: Debt monetization accelerates. Inflation re-accelerates to 5-8%.
Real yields go deeply negative. Dollar loses purchasing power rapidly.
**Key triggers**: [list]
**Asset implications**:
- Stocks: [outlook — stagflation scenario]
- Gold/Silver: [Strong outperformance likely]
- Dollar: [significant weakness]
- Real estate: [mixed]
**Timeline**: {time_horizon}

## SCENARIO 3: DEBT CRISIS / RESTRUCTURING
Probability: X%
**What happens**: US debt reaches unsustainable levels. Credit downgrade. Bond market stress.
Possible debt restructuring or default on some obligations.
**Key triggers**: [list]
**Asset implications**:
- Gold/Silver: [likely strongest asset]
- Dollar: [severe weakness]
- Stocks: [severe decline]
**Timeline**: {time_horizon}

## SCENARIO 4: MONETARY RESET / GOLD REVALUATION
Probability: X%
**What happens**: Major monetary system restructuring. Gold officially revalued to $10,000+/oz.
New international monetary system with gold/asset backing.
Historical precedent: Bretton Woods (1944), Plaza Accord (1985).
**Key conditions**: [list]
**Asset implications**:
- Gold/Silver: [massive revaluation upward]
- Dollar: [reset to new baseline]
- Existing dollar holders: [analysis]
**Timeline**: {time_horizon}

## SCENARIO 5: THE GOLDEN AGE (Best Case)
Probability: X%
**What happens**: US fiscal reform. Return to asset-backed currency.
Reduced debt through growth + spending cuts. Dollar strengthened by gold backing.
New monetary system that is more stable and fair.
**Key conditions**: [what needs to happen politically and economically]
**Asset implications**: [analysis]
**Timeline**: {time_horizon}

## 📊 PROBABILITY WEIGHTED OUTLOOK
Based on current trajectory, the most likely scenario is: [analysis]

## 🎯 POSITIONING FOR EACH SCENARIO
What rational people are doing to prepare for various scenarios:
- Diversify into hard assets (gold, silver, land)
- Reduce dollar-denominated paper assets
- Consider international diversification
- Hold some physical precious metals

Note: This is not financial advice. Consult a licensed financial advisor."""

    result = query_llm(prompt)

    fig = None
    try:
        scenarios = ["Soft Landing", "Inflationary\nSpiral",
                     "Debt Crisis", "Monetary\nReset", "Golden\nAge"]
        probabilities = [30, 35, 20, 10, 5]
        colors_s = ["#27ae60", "#f39c12", "#e74c3c", "#9b59b6", "#f1c40f"]

        fig = go.Figure(go.Pie(
            labels=scenarios,
            values=probabilities,
            hole=0.4,
            marker_colors=colors_s,
            textinfo="label+percent"
        ))
        fig.update_layout(
            title="Scenario Probability Distribution",
            template="plotly_dark", height=400,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 12: Golden Age Tracker ───────────────────────────────────────────────

def golden_age_tracker(extra_context="", file_context=""):
    gold_price, _ = fetch_commodity_price("GC=F")
    current_gold = gold_price or 3100

    prompt = f"""You are a monetary reset analyst tracking progress toward a potential
"Golden Age" — a new monetary system based on sound money, reduced debt, and asset backing.

Current Gold Price: ${current_gold:,.0f}/oz

Analyze current conditions against the conditions required for a "Golden Age":

## ⚡ GOLDEN AGE TRACKER — HOW CLOSE ARE WE?

**GOLDEN AGE DEFINITION**: A period of monetary stability, reduced government debt,
sound money backed by real assets, sustained economic growth, and improved citizen
purchasing power. Historically associated with gold/asset-backed monetary systems.

## 📊 GOLDEN AGE READINESS SCORECARD

Rate each factor 0-10 (10 = Golden Age condition fully met):

| Factor | Score | Status | Trend |
|--------|-------|--------|-------|
| Monetary Stability | X/10 | [status] | [↑↓→] |
| Debt Sustainability | X/10 | [status] | [↑↓→] |
| Gold/Asset Backing Discussion | X/10 | [status] | [↑↓→] |
| Political Will for Reform | X/10 | [status] | [↑↓→] |
| Public Awareness of Monetary Issues | X/10 | [status] | [↑↓→] |
| Central Bank Gold Accumulation | X/10 | [status] | [↑↓→] |
| De-Dollarization Progress | X/10 | [status] | [↑↓→] |
| Sound Money Advocacy | X/10 | [status] | [↑↓→] |
| Asset-Backed Digital Currency Dev | X/10 | [status] | [↑↓→] |
| Economic Inequality Reduction | X/10 | [status] | [↑↓→] |

**OVERALL GOLDEN AGE READINESS**: X% (X/100)

## ✅ CONDITIONS BEING MET (Positive Signs)
1. Central banks accumulating gold at record pace (1,000+ tonnes/year)
2. Gold overtaking Treasuries as reserve asset (2025 milestone)
3. BRICS launching gold-backed Unit currency pilot
4. Growing public awareness of monetary debasement
5. Gold at all-time highs — market signaling monetary system stress
6. Federal Reserve discussing gold revaluation (first time in decades)
7. Multiple countries repatriating gold reserves

## ❌ CONDITIONS NOT YET MET (What's Missing)
1. US political will for fiscal reform
2. Bipartisan agreement on debt reduction
3. International monetary coordination
4. Digital gold-backed currency infrastructure at scale
5. Public understanding of monetary policy broadly
6. Reduction in annual federal deficit
7. Return to sound money principles in mainstream economics

## 🗺️ THE ROAD TO THE GOLDEN AGE
Step 1: Public awareness of monetary debasement (IN PROGRESS)
Step 2: Political pressure for fiscal reform (EARLY STAGE)
Step 3: Gold/asset backing discussion goes mainstream (EMERGING)
Step 4: International monetary coordination begins (NOT YET)
Step 5: New monetary system implemented (FUTURE)
Step 6: Debt restructuring/reduction (FUTURE)
Step 7: Golden Age begins (FUTURE)

## 📅 TIMELINE ESTIMATE
Conservative estimate: 10-20 years
Base case: 5-15 years if fiscal/monetary crisis accelerates change
Optimistic: 3-7 years if political will emerges

## 🔑 WHAT WOULD ACCELERATE THE GOLDEN AGE
US gold audit and revaluation.
Bipartisan fiscal reform legislation.
BRICS Unit scaling to global trade settlement.
Digital Treasury Dollar backed by gold/assets.
Global monetary conference (new Bretton Woods).

Current Gold Price ${current_gold:,.0f}/oz signals: [what the market is saying about monetary confidence]

Be factual, optimistic but realistic, and cite specific current developments."""

    result = query_llm_with_file(prompt, file_context)

    fig = None
    try:
        factors = ["Monetary\nStability", "Debt\nSustainability", "Gold\nBacking",
                   "Political\nWill", "Public\nAwareness", "Central Bank\nGold",
                   "De-Dollar\nProgress", "Sound\nMoney", "Digital\nCurrency", "Equality"]
        scores = [3, 2, 6, 2, 5, 8, 7, 5, 4, 3]
        overall = sum(scores) / len(scores)

        fig = make_subplots(rows=1, cols=2,
                            subplot_titles=["Golden Age Readiness by Factor",
                                            f"Overall Readiness: {overall:.0f}%"],
                            specs=[[{"type": "bar"}, {"type": "indicator"}]])

        colors_ga = ["#27ae60" if s >= 7 else "#f39c12" if s >= 5 else "#e74c3c"
                     for s in scores]
        fig.add_trace(go.Bar(x=factors, y=scores,
                              marker_color=colors_ga,
                              text=[f"{s}/10" for s in scores],
                              textposition="auto"), row=1, col=1)

        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=overall * 10,
            title={"text": "Golden Age Readiness %"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#f1c40f"},
                "steps": [
                    {"range": [0, 25], "color": "#e74c3c"},
                    {"range": [25, 50], "color": "#f39c12"},
                    {"range": [50, 75], "color": "#f1c40f"},
                    {"range": [75, 100], "color": "#27ae60"}
                ],
                "threshold": {
                    "line": {"color": "white", "width": 4},
                    "thickness": 0.75,
                    "value": overall * 10
                }
            }
        ), row=1, col=2)

        fig.update_layout(title="⚡ Golden Age Tracker — Current Readiness",
                          template="plotly_dark", height=450,
                          paper_bgcolor="#0a0a1a")
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 13: AI Economic Chat ──────────────────────────────────────────────────

def economic_chat(message, history):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a nonpartisan macroeconomic analyst, monetary historian, and "
                "financial educator. You help citizens understand: the US national debt, "
                "Federal Reserve policy, gold and silver markets, de-dollarization, BRICS, "
                "the potential for a monetary reset, asset-backed currencies, purchasing power, "
                "inflation, and the path to monetary stability. "
                "You are not affiliated with any political party, government, or financial institution. "
                "You present multiple perspectives on contested economic topics. "
                "You cite official sources like fiscaldata.treasury.gov, federalreserve.gov, "
                "worldgoldcouncil.org, and imf.org. "
                "You always remind users that nothing you say is financial advice and they should "
                "consult a licensed financial advisor before making investment decisions. "
                "You believe citizens deserve to understand the monetary system that governs their lives."
            )
        }
    ]
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": bot_msg})
    messages.append({"role": "user", "content": message})

    import os
    API_KEY = os.environ.get("OPENAI_API_KEY", "")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    msgs = messages if 'messages' in dir() else [{"role": "user", "content": prompt}]
    payload = {"model": "gpt-4o", "max_tokens": 4000, "messages": msgs}
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=240)
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        return f"API Error: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


# ─── Gradio UI ────────────────────────────────────────────────────────────────

with gr.Blocks(title="AI Debt Clock Analyzer", theme=gr.themes.Base(
        primary_hue=gr.themes.colors.Color(
            c50="#fef9ec", c100="#faefd0", c200="#f4dea0", c300="#edc970",
            c400="#e4b04a", c500="#c9a84c", c600="#a8872e", c700="#856519",
            c800="#5e440d", c900="#3a2a05", c950="#1e1502"
        ),
        secondary_hue=gr.themes.colors.Color(
            c50="#e8edf5", c100="#c5d0e6", c200="#9eb0d4", c300="#7490c2",
            c400="#4f74b0", c500="#2d5a9e", c600="#1a3a6e", c700="#112240",
            c800="#0a1628", c900="#060e1a", c950="#03070d"
        ),
        neutral_hue=gr.themes.colors.Color(
            c50="#f0f2f7", c100="#d8dde9", c200="#b8c2d6", c300="#95a3be",
            c400="#7285a6", c500="#536890", c600="#3a4f73", c700="#263856",
            c800="#162438", c900="#0c1622", c950="#060b11"
        ),
        font=gr.themes.GoogleFont("DM Sans"),
        font_mono=gr.themes.GoogleFont("DM Mono"),
    ).set(
        body_background_fill="#0a1628",
        body_background_fill_dark="#0a1628",
        body_text_color="#f8f9fc",
        body_text_color_dark="#f8f9fc",
        block_background_fill="#112240",
        block_background_fill_dark="#112240",
        block_border_color="rgba(201,168,76,0.2)",
        block_border_color_dark="rgba(201,168,76,0.2)",
        block_label_background_fill="#112240",
        block_label_background_fill_dark="#112240",
        block_label_text_color="#c9a84c",
        block_label_text_color_dark="#c9a84c",
        block_title_text_color="#c9a84c",
        block_title_text_color_dark="#c9a84c",
        button_primary_background_fill="linear-gradient(135deg,#c9a84c,#e8c96a)",
        button_primary_background_fill_dark="linear-gradient(135deg,#c9a84c,#e8c96a)",
        button_primary_text_color="#0a1628",
        button_primary_text_color_dark="#0a1628",
        button_secondary_background_fill="#112240",
        button_secondary_background_fill_dark="#112240",
        button_secondary_border_color="rgba(201,168,76,0.3)",
        button_secondary_border_color_dark="rgba(201,168,76,0.3)",
        button_secondary_text_color="#c9a84c",
        button_secondary_text_color_dark="#c9a84c",
        input_background_fill="#0a1628",
        input_background_fill_dark="#0a1628",
        input_border_color="rgba(201,168,76,0.2)",
        input_border_color_dark="rgba(201,168,76,0.2)",
        input_placeholder_color="#8892a4",
        input_placeholder_color_dark="#8892a4",
        shadow_drop="0 4px 24px rgba(0,0,0,0.4)",
        shadow_drop_lg="0 8px 40px rgba(0,0,0,0.5)",
        table_even_background_fill="#0a1628",
        table_even_background_fill_dark="#0a1628",
        table_odd_background_fill="#112240",
        table_odd_background_fill_dark="#112240",
    )) as demo:
    gr.HTML('<style>::selection{background:#c9a84c;color:#000!important}::-moz-selection{background:#c9a84c;color:#000!important}</style>')
    gr.Markdown("# 💸 AI Debt Clock Analyzer")
    gr.Markdown("### *AI-Powered Analysis of America's Debt, Money Supply, Gold, and Monetary Future*")
    gr.Markdown(INSPIRATION_NOTICE)
    gr.Markdown(CITIZEN_NOTICE)
    gr.Markdown(DISCLAIMER)

    with gr.Tabs():

        # ── Tab 1: US Debt Dashboard ───────────────────────────────────────────
        with gr.Tab("💸 US Debt Dashboard"):
            gr.Markdown("## Live US National Debt Dashboard")
            gr.Markdown("*Data sourced from fiscaldata.treasury.gov*")
            with gr.Row():
                with gr.Column(scale=1):
                    t1_context = gr.Textbox(
                        label="💸 Additional Context (optional)",
                        placeholder="e.g. specific debt metrics, time period...")
                    t1_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t1_btn = gr.Button("💸 Load Debt Dashboard", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t1_output = gr.Markdown(label="Analysis")
            t1_chart = gr.Plot(label="US Debt Chart")
            t1_btn.click(us_debt_dashboard, inputs=[t1_context, t1_upload], outputs=[t1_output, t1_chart])

        # ── Tab 2: Federal Reserve Monitor ────────────────────────────────────
        with gr.Tab("🏦 Federal Reserve"):
            gr.Markdown("## Federal Reserve Monitor — Rates, Balance Sheet, M2")
            gr.Markdown("*Data sourced from federalreserve.gov and FRED*")
            with gr.Row():
                with gr.Column(scale=1):
                    t2_context = gr.Textbox(
                        label="🏦 Additional Context (optional)",
                        placeholder="e.g. specific Fed policy, rate outlook...")
                    t2_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t2_btn = gr.Button("🏦 Load Fed Monitor", variant="primary")
                    gr.Markdown(WAIT_MSG)
            t2_output = gr.Markdown(label="Fed Analysis")
            t2_chart = gr.Plot(label="Fed Rate vs Inflation Chart")
            t2_btn.click(federal_reserve_monitor, inputs=[t2_context, t2_upload],
                         outputs=[t2_output, t2_chart])

        # ── Tab 3: Fiscal Health Score ─────────────────────────────────────────
        with gr.Tab("📊 Fiscal Health Score"):
            gr.Markdown("## US Fiscal Health Grade — A Through F")
            with gr.Row():
                with gr.Column(scale=1):
                    t3_context = gr.Textbox(
                        label="📊 Additional Context (optional)",
                        placeholder="e.g. specific fiscal category to focus on...")
                    t3_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t3_btn = gr.Button("📊 Grade US Fiscal Health", variant="primary")
                    gr.Markdown(WAIT_MSG)
            t3_output = gr.Markdown(label="Fiscal Health Analysis")
            t3_chart = gr.Plot(label="Fiscal Health Scorecard")
            t3_btn.click(fiscal_health_score, inputs=[t3_context, t3_upload],
                         outputs=[t3_output, t3_chart])

        # ── Tab 4: Gold & Silver Tracker ───────────────────────────────────────
        with gr.Tab("🥇 Gold & Silver"):
            gr.Markdown("## Gold & Silver — Prices, Trends, Central Bank Accumulation")
            gr.Markdown("*Live prices via Yahoo Finance*")
            with gr.Row():
                with gr.Column(scale=1):
                    t4_context = gr.Textbox(
                        label="🥇 Additional Context (optional)",
                        placeholder="e.g. specific gold metric, central bank...")
                    t4_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t4_btn = gr.Button("🥇 Load Gold & Silver Data", variant="primary")
                    gr.Markdown(WAIT_MSG)
            t4_output = gr.Markdown(label="Gold & Silver Analysis")
            t4_chart = gr.Plot(label="Price History Chart")
            t4_btn.click(gold_silver_tracker, inputs=[t4_context, t4_upload],
                         outputs=[t4_output, t4_chart])

        # ── Tab 5: Commodities Monitor ─────────────────────────────────────────
        with gr.Tab("🛢️ Commodities"):
            gr.Markdown("## Real Asset Commodities Monitor")
            gr.Markdown("*Live prices via Yahoo Finance*")
            with gr.Row():
                with gr.Column(scale=1):
                    t5_context = gr.Textbox(
                        label="🛢️ Additional Context (optional)",
                        placeholder="e.g. specific commodity, price analysis...")
                    t5_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t5_btn = gr.Button("🛢️ Load Commodities Data", variant="primary")
                    gr.Markdown(WAIT_MSG)
            t5_output = gr.Markdown(label="Commodities Analysis")
            t5_chart = gr.Plot(label="Commodities Chart")
            t5_btn.click(commodities_monitor, inputs=[t5_context, t5_upload],
                         outputs=[t5_output, t5_chart])

        # ── Tab 6: De-Dollarization Index ──────────────────────────────────────
        with gr.Tab("💱 De-Dollarization"):
            gr.Markdown("## De-Dollarization Index — Dollar Reserve Share Decline")
            with gr.Row():
                with gr.Column(scale=1):
                    t6_context = gr.Textbox(
                        label="💱 Additional Context (optional)",
                        placeholder="e.g. specific country, BRICS update...")
                    t6_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t6_btn = gr.Button("💱 Load De-Dollarization Data", variant="primary")
                    gr.Markdown(WAIT_MSG)
            t6_output = gr.Markdown(label="De-Dollarization Analysis")
            t6_chart = gr.Plot(label="Reserve Share Chart")
            t6_btn.click(dedollarization_index, inputs=[t6_context, t6_upload],
                         outputs=[t6_output, t6_chart])

        # ── Tab 7: Dollar vs Gold Backing ──────────────────────────────────────
        with gr.Tab("🏛️ Gold Backing Ratio"):
            gr.Markdown("## What Price Would Gold Need to Back US Debt?")
            with gr.Row():
                with gr.Column(scale=1):
                    t7_context = gr.Textbox(
                        label="🏛️ Additional Context (optional)",
                        placeholder="e.g. specific backing percentage scenario...")
                    t7_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t7_btn = gr.Button("🏛️ Calculate Gold Backing", variant="primary")
                    gr.Markdown(WAIT_MSG)
            t7_output = gr.Markdown(label="Gold Backing Analysis")
            t7_chart = gr.Plot(label="Gold Price Required Chart")
            t7_btn.click(dollar_gold_backing, inputs=[t7_context, t7_upload],
                         outputs=[t7_output, t7_chart])

        # ── Tab 8: BRICS vs Dollar ─────────────────────────────────────────────
        with gr.Tab("🌍 BRICS vs Dollar"):
            gr.Markdown("## BRICS vs US Dollar — Head-to-Head Scorecard")
            with gr.Row():
                with gr.Column(scale=1):
                    t8_context = gr.Textbox(
                        label="🌍 Additional Context (optional)",
                        placeholder="e.g. specific BRICS country, dollar metric...")
                    t8_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t8_btn = gr.Button("🌍 Load BRICS vs Dollar Analysis", variant="primary")
                    gr.Markdown(WAIT_MSG)
            t8_output = gr.Markdown(label="BRICS vs Dollar Analysis")
            t8_chart = gr.Plot(label="BRICS vs Dollar Radar Chart")
            t8_btn.click(brics_vs_dollar, inputs=[t8_context, t8_upload],
                         outputs=[t8_output, t8_chart])

        # ── Tab 9: US vs BRICS Gold Holdings ──────────────────────────────────
        with gr.Tab("🏦 Gold Holdings"):
            gr.Markdown("## US Fort Knox vs BRICS Gold Holdings — Side by Side")
            with gr.Row():
                with gr.Column(scale=1):
                    t9_context = gr.Textbox(
                        label="🏦 Additional Context (optional)",
                        placeholder="e.g. specific country gold holdings...")
                    t9_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t9_btn = gr.Button("🏦 Compare Gold Holdings", variant="primary")
                    gr.Markdown(WAIT_MSG)
            t9_output = gr.Markdown(label="Gold Holdings Comparison")
            t9_chart = gr.Plot(label="Gold Holdings Chart")
            t9_btn.click(us_vs_brics_gold, inputs=[t9_context, t9_upload],
                         outputs=[t9_output, t9_chart])

        # ── Tab 10: Dollar vs Gold Ratio ───────────────────────────────────────
        with gr.Tab("📈 Dollar vs Gold Ratio"):
            gr.Markdown("## Dollar Purchasing Power vs Gold — 1913 to Today")
            with gr.Row():
                with gr.Column(scale=1):
                    t10_context = gr.Textbox(
                        label="📈 Additional Context (optional)",
                        placeholder="e.g. specific ratio, time period...")
                    t10_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t10_btn = gr.Button("📈 Load Purchasing Power Analysis", variant="primary")
                    gr.Markdown(WAIT_MSG)
            t10_output = gr.Markdown(label="Dollar vs Gold Analysis")
            t10_chart = gr.Plot(label="Purchasing Power Chart")
            t10_btn.click(dollar_gold_ratio, inputs=[t10_context, t10_upload],
                          outputs=[t10_output, t10_chart])

        # ── Tab 11: Prediction & Scenario Engine ───────────────────────────────
        with gr.Tab("🔮 Scenario Engine"):
            gr.Markdown("## Monetary Scenario Analysis — What Happens Next?")
            with gr.Row():
                with gr.Column(scale=1):
                    t11_focus = gr.Dropdown(
                        choices=["General Monetary Outlook",
                                 "Gold & Precious Metals",
                                 "US Dollar Future",
                                 "BRICS & De-Dollarization",
                                 "Debt Crisis Scenarios",
                                 "Golden Age / Monetary Reset"],
                        value="General Monetary Outlook",
                        label="Scenario Focus")
                    t11_horizon = gr.Dropdown(
                        choices=["1 Year", "3 Years", "5 Years",
                                 "10 Years", "20 Years"],
                        value="5 Years", label="Time Horizon")
                    t11_risk = gr.Dropdown(
                        choices=["Conservative", "Moderate", "Aggressive"],
                        value="Moderate", label="Analysis Depth")
                    t11_context = gr.Textbox(label="Additional Context", lines=3,
                                              placeholder="Any specific scenarios or concerns...")
                    t11_btn = gr.Button("🔮 Generate Scenarios", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t11_output = gr.Markdown(label="Analysis")
                    t11_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                with gr.Column(scale=2):
                    t11_output = gr.Markdown(label="Scenario Analysis")
            t11_chart = gr.Plot(label="Scenario Probability Chart")
            t11_btn.click(prediction_scenario_engine, inputs=[t11_focus, t11_horizon, t11_risk, t11_context],
                          outputs=[t11_output, t11_chart])

        # ── Tab 12: Golden Age Tracker ─────────────────────────────────────────
        with gr.Tab("⚡ Golden Age Tracker"):
            gr.Markdown("## How Close Are We to the Golden Age?")
            gr.Markdown("*Tracking conditions required for a sound money monetary system*")
            with gr.Row():
                with gr.Column(scale=1):
                    t12_context = gr.Textbox(
                        label="⚡ Additional Context (optional)",
                        placeholder="e.g. specific Golden Age indicator...")
                    t12_upload = gr.File(
                        label="📎 Upload for Context (PDF/CSV/XLSX/PNG/JPG)",
                        file_types=[".pdf",".csv",".xlsx",".xls",".png",".jpg",".jpeg"],
                        file_count="single")
                    t12_btn = gr.Button("⚡ Calculate Golden Age Readiness", variant="primary")
                    gr.Markdown(WAIT_MSG)
            t12_output = gr.Markdown(label="Golden Age Analysis")
            t12_chart = gr.Plot(label="Golden Age Readiness Gauge")
            t12_btn.click(golden_age_tracker, inputs=[t12_context, t12_upload],
                          outputs=[t12_output, t12_chart])

        # ── Tab 13: AI Economic Chat ───────────────────────────────────────────
        with gr.Tab("💬 AI Economic Chat"):
            gr.Markdown("## Ask Anything About the US Monetary System")
            gr.ChatInterface(
                fn=economic_chat,
                examples=[
                    "What is the US national debt right now and why does it matter?",
                    "Explain the Federal Reserve in simple terms",
                    "Why is gold hitting all-time highs in 2025-2026?",
                    "What is de-dollarization and should I be worried?",
                    "What is the BRICS Unit and is it a threat to the dollar?",
                    "How much gold would the US need to back the dollar?",
                    "What happened when Nixon ended the gold standard in 1971?",
                    "What is a monetary reset and has it happened before?",
                    "Is silver a better investment than gold right now?",
                    "How do I protect my savings from dollar debasement?",
                ],
                title="",
            )

    gr.Markdown(WATERMARK)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("GRADIO_SERVER_PORT", 7860)), share=False, ssr_mode=False)
