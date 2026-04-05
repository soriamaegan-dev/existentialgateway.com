import gradio as gr
import requests
import os
import plotly.graph_objects as go

INVESTMENT_SYSTEM_PROMPT = """You are a senior investment analyst specializing in equities, cryptocurrency, ETFs, options, and alternative investments including prediction markets (Polymarket, Kalshi).

ANALYTICAL STANDARDS:
1. Apply fundamental analysis: earnings quality, revenue growth, margin trends, competitive moat assessment, management quality indicators.
2. Apply technical analysis: chart patterns, momentum indicators, volume analysis, support/resistance, Fibonacci levels.
3. For crypto analysis: on-chain metrics (NVT, MVRV, Realized Cap), tokenomics, developer activity, network effects, regulatory risk.
4. For options analysis: Greeks (delta, gamma, theta, vega), implied volatility surface, put/call ratio, open interest analysis.
5. For prediction markets: probability calibration, market efficiency assessment, edge identification, position sizing (Kelly Criterion).
6. Apply Modern Portfolio Theory: Sharpe ratio, Sortino ratio, max drawdown, correlation analysis, efficient frontier concepts.
7. Structure every analysis with: Asset Overview → Fundamental Score → Technical Score → Risk Assessment → Position Sizing Guidance → Catalysts → Exit Criteria.
8. Always present bull case, bear case, and base case with probability weightings.
9. Flag liquidity risks, concentration risks, regulatory risks, and black swan scenarios.
10. Note that this is analytical support — not investment advice. Past performance does not guarantee future results."""


HF_TOKEN = os.environ.get("HF_TOKEN", "")

DISCLAIMER = """
> **FINANCIAL DISCLAIMER**: This tool is powered by Artificial Intelligence and is
> intended for informational and educational purposes ONLY. Nothing in this tool
> constitutes financial, investment, or trading advice. All analysis is AI-generated
> and may be incorrect. You can lose your entire investment. Always consult a licensed
> financial advisor before making any investment decisions. Past performance does not
> guarantee future results. The developers assume no liability for any financial losses.
> © 2026 Existential Gateway, LLC. All Rights Reserved. Proprietary Software.
"""

BETTING_WARNING = """
> **BIDDING DISCLAIMER**: This tool analyzes prediction market and events market
> contracts for informational purposes ONLY. Prediction markets and bidding platforms
> may be ILLEGAL in your state or country. Always verify the legal status of these
> platforms in your jurisdiction BEFORE participating. This tool is NOT affiliated with,
> endorsed by, or connected to any bidding or prediction market platform.
> You can lose your entire investment. Never bid more than you can afford to lose.
> © 2026 Existential Gateway, LLC. All Rights Reserved.
"""

INVEST_WARNING = """
> **RISK WARNING**: Investing in stocks, cryptocurrencies, and prediction markets
> involves substantial risk of loss. Crypto and prediction markets are especially
> volatile. Never invest more than you can afford to lose completely.
> This AI analysis is NOT a guarantee of profits.
"""

WAIT_MSG = "*Results take approximately 1-2 minutes to generate. Please do not click multiple times.*"

WATERMARK = """
---
© 2026 Existential Gateway, LLC | AI Investment Analyzer
Unauthorized reproduction, distribution, or commercial use strictly prohibited.
For licensing inquiries: existentialgateway@gmail.com
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
    """If text contains URLs, fetch and append their content with explicit AI instructions."""
    if not text or 'http' not in text:
        return text
    url_content = fetch_url_content(text)
    if url_content:
        return (
            text +
            "\n\n=== FETCHED URL CONTENT - YOU MUST REFERENCE THIS IN YOUR ANALYSIS ==="
            "\nThe following content was fetched from the URL provided by the user. "
            "You MUST directly reference, quote, and analyze this content in your response. "
            "Incorporate specific details, facts, names, and data from this content:\n\n" +
            url_content +
            "\n=== END OF FETCHED URL CONTENT ==="
        )
    return text


def query_llm(prompt):
    API_KEY = os.environ.get("OPENAI_API_KEY", "")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    msgs = [{"role": "system", "content": INVESTMENT_SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
    payload = {"model": "gpt-4o", "max_tokens": 4000, "messages": msgs}
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=240)
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        return f"API Error: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


# ─── Tab 1: Stock Analyzer ────────────────────────────────────────────────────

def analyze_stock(ticker, company, price, position, entry_price,
                  shares, horizon, risk, context):
    if not ticker or not company:
        return "Please enter a stock ticker and company name."
    position_str = ""
    if position != "Not Invested" and entry_price and shares:
        pl = (float(price) - float(entry_price)) * float(shares)
        pl_pct = ((float(price) - float(entry_price)) / float(entry_price)) * 100 if float(entry_price) > 0 else 0
        position_str = (f"\nPosition: {position} | Entry: ${entry_price} | "
                        f"Shares: {shares} | P&L: ${pl:.2f} ({pl_pct:.2f}%)")

    prompt = f"""You are an expert Wall Street stock analyst. Write as the professional analyst who performed this work. State all findings directly with specific numbers, percentages, and comparisons. NEVER say 'this appears to be', 'the data seems to show', 'the dataset contains', or 'it looks like'. Instead, deliver results confidently: 'Average claim cost was $4,230, a 12% increase year-over-year' or 'Readmission rates of 18.3% in Cardiology exceeded the facility average by 4.1 percentage points.' Be direct, precise, and actionable. Present findings as YOUR analysis, not a description of a dataset. Analyze this stock comprehensively:

Ticker: {ticker} | Company: {company}
Current Price: ${price}
Position: {position}{position_str}
Investment Horizon: {horizon} | Risk Tolerance: {risk}
Additional Context: {context}

Produce a complete professional stock analysis with ALL of these sections:

## 1. COMPANY OVERVIEW
What the company does and its market position.

## 2. CURRENT MARKET SENTIMENT
Overall sentiment: BULLISH / BEARISH / NEUTRAL
Key news driving sentiment. Analyst consensus.

## 3. FUNDAMENTAL ANALYSIS
Revenue and earnings trend. Valuation assessment.
Competitive position. Key business risks.

## 4. TECHNICAL ANALYSIS
Price vs moving average ranges. Momentum assessment.
Key price levels to watch. Volume considerations.

## 5. CURRENT EVENTS IMPACT
Interest rate environment. Sector news.
Regulatory factors. Geopolitical factors.

## 6. BUY / HOLD / SELL RECOMMENDATION
RECOMMENDATION: [STRONG BUY / BUY / HOLD / SELL / STRONG SELL]
Confidence: [HIGH / MEDIUM / LOW]
Target Price Range: $X - $X
Stop Loss: $X
Reasoning: [detailed]

## 7. POSITION ANALYSIS
Current P&L analysis. Recommended action. Exit strategy.

## 8. RISK ASSESSMENT
Risk level. Key upside catalysts. Key downside risks.
Maximum portfolio allocation: X%

## 9. WHAT TO WATCH
3 key events and dates that will move this stock.

Be specific, professional, and use real market knowledge."""

    return query_llm(prompt) + "\n\n" + WATERMARK


# ─── Tab 2: Crypto Analyzer ───────────────────────────────────────────────────

def analyze_crypto(name, ticker, price, position, entry_price,
                   amount, horizon, risk, network, context):
    if not name:
        return "Please enter a cryptocurrency name."
    position_str = ""
    if position != "Not Invested" and entry_price and amount:
        pl = (float(price) - float(entry_price)) * float(amount)
        pl_pct = ((float(price) - float(entry_price)) / float(entry_price)) * 100 if float(entry_price) > 0 else 0
        position_str = (f"\nPosition: {position} | Entry: ${entry_price} | "
                        f"Amount: {amount} | P&L: ${pl:.2f} ({pl_pct:.2f}%)")

    prompt = f"""You are an expert cryptocurrency analyst. Write as the professional analyst who performed this work. State all findings directly with specific numbers, percentages, and comparisons. NEVER say 'this appears to be', 'the data seems to show', 'the dataset contains', or 'it looks like'. Instead, deliver results confidently: 'Average claim cost was $4,230, a 12% increase year-over-year' or 'Readmission rates of 18.3% in Cardiology exceeded the facility average by 4.1 percentage points.' Be direct, precise, and actionable. Present findings as YOUR analysis, not a description of a dataset. Analyze this crypto comprehensively:

Crypto: {name} ({ticker})
Current Price: ${price}
Network: {network}
Position: {position}{position_str}
Investment Horizon: {horizon} | Risk Tolerance: {risk}
Additional Context: {context}

Produce a complete professional crypto analysis with ALL of these sections:

## 1. CRYPTO OVERVIEW
Use case and market position. Market cap tier.

## 2. MARKET SENTIMENT ANALYSIS
Bull / Bear / Sideways market conditions.
Bitcoin dominance impact. Fear and Greed assessment.
Social sentiment. Recent news summary.

## 3. FUNDAMENTAL ANALYSIS
Network activity and adoption. Developer activity.
Token economics (supply, inflation, burns).
Use case strength. Competitive landscape.

## 4. TECHNICAL ANALYSIS
Market cycle phase: accumulation / markup / distribution / markdown
Key support levels: $X, $X
Key resistance levels: $X, $X
Trend: UPTREND / DOWNTREND / SIDEWAYS

## 5. CURRENT EVENTS IMPACT
Regulatory news. Institutional adoption.
Macro factors. Network upgrades.

## 6. BUY / HOLD / SELL RECOMMENDATION
RECOMMENDATION: [STRONG BUY / BUY / HOLD / SELL / STRONG SELL / AVOID]
Confidence: [HIGH / MEDIUM / LOW]
Short term target: $X | Long term target: $X | Stop loss: $X
DCA recommendation: Yes/No and at what prices.

## 7. POSITION ANALYSIS
Current P&L and recommended action.

## 8. RISK ASSESSMENT
Risk level. Volatility warning. Key risks. Key upside catalysts.
Maximum portfolio allocation: X%

## 9. CRYPTO SPECIFIC ALERTS
On-chain metrics to monitor.
Key price levels that confirm or deny thesis.
News events that would change recommendation.

Be specific and professional."""

    return query_llm(prompt) + "\n\n" + WATERMARK


# ─── Tab 3: Bidding Analysis ──────────────────────────────────────────────────

def analyze_bidding(platform, platform_other, question, yes_price,
                    position, entry_price, bet_amount,
                    resolution_date, category, context):
    if not question:
        return "Please enter a contract or market question."

    active_platform = (platform_other if platform == "Other (specify)"
                       and platform_other else platform)

    platform_notes = {
        "Polymarket": (
            "Decentralized crypto-based prediction market. No US regulation. "
            "Crypto wallet required. High liquidity on major markets. "
            "USDC-based. No US users officially."
        ),
        "Kalshi": (
            "CFTC-regulated US events market. Legally compliant for US users. "
            "Cash settlement. Tax reporting required. Lower liquidity than Polymarket "
            "but fully regulated."
        ),
        "PredictIt": (
            "Regulated US political prediction market. $850 per contract limit. "
            "Political focus only. Limited to US users. No-action letter from CFTC."
        ),
        "Manifold Markets": (
            "Play money (mana) based by default. No real money risk on standard markets. "
            "Good for calibration and forecasting practice. Some real-money features available."
        ),
        "Metaculus": (
            "Forecasting platform focused on accuracy scoring. No real money wagering. "
            "Community-driven probability estimates. Best for research and calibration."
        ),
        "Robinhood Prediction Markets": (
            "Regulated US platform integrated with Robinhood brokerage. "
            "Easy access for retail investors. CFTC regulated. Growing liquidity."
        ),
    }

    platform_context = platform_notes.get(
        active_platform,
        f"{active_platform} is a prediction market or bidding platform."
    )

    position_str = ""
    if position != "Not Entered" and entry_price and bet_amount:
        position_str = (f"\nCurrent Position: {position} | "
                        f"Entry: {entry_price}% | Amount: ${bet_amount}")

    prompt = f"""You are an expert prediction market and bidding platform analyst. Write as the professional analyst who performed this work. State all findings directly with specific numbers, percentages, and comparisons. NEVER say 'this appears to be', 'the data seems to show', 'the dataset contains', or 'it looks like'. Instead, deliver results confidently: 'Average claim cost was $4,230, a 12% increase year-over-year' or 'Readmission rates of 18.3% in Cardiology exceeded the facility average by 4.1 percentage points.' Be direct, precise, and actionable. Present findings as YOUR analysis, not a description of a dataset. 
Platform: {active_platform}
Platform Notes: {platform_context}

Contract / Market Question: {question}
Current YES Price / Implied Probability: {yes_price}%
Category: {category}
Resolution Date: {resolution_date}
Position: {position}{position_str}
Additional Context: {context}

Produce a complete professional bidding analysis with ALL of these sections:

## 1. PLATFORM OVERVIEW
Platform: {active_platform}
Key characteristics relevant to this contract.
Regulatory status. Liquidity. Settlement method. US availability.

## 2. CONTRACT OVERVIEW
What this contract pays out on. Resolution criteria.
Current implied YES probability: {yes_price}%

## 3. TRUE PROBABILITY ASSESSMENT
Estimated TRUE probability of YES: X%
Current platform price: {yes_price}%
Assessment: OVERPRICED / UNDERPRICED / FAIRLY PRICED
Edge: +X% or -X%

## 4. KEY FACTORS ANALYSIS
Top 5 factors with BULLISH / BEARISH / NEUTRAL direction for YES outcome.

## 5. CURRENT EVENTS IMPACT
Most recent relevant data points and news.
How current events shift the probability.

## 6. BUY / SELL / HOLD RECOMMENDATION
RECOMMENDATION: [BUY YES / BUY NO / HOLD / SELL / AVOID]
Confidence: [HIGH / MEDIUM / LOW]
Target exit price: X%. Reasoning: [detailed]

## 7. POSITION ANALYSIS
Entry, current price, P&L, recommended exit, stop loss, take profit.

## 8. KELLY CRITERION BET SIZING
Kelly %: X% of bankroll
Recommended bet: $X (for $1,000 bankroll)
Half Kelly (safer): $X
Maximum recommended: $X

## 9. PLATFORM-SPECIFIC CONSIDERATIONS
Advantages and disadvantages of using {active_platform} for this contract.
Liquidity concerns. Resolution ambiguity. Better platform alternatives if any.

## 10. RISK ASSESSMENT
Risk level. Time to resolution. Liquidity risk. Time decay. Regulatory risk.

## 11. MONITORING ALERTS
3 specific events that would change this recommendation.

Be precise, analytical, and platform-aware."""

    return query_llm(prompt) + "\n\n" + WATERMARK


# ─── Tab 4: Portfolio Dashboard ───────────────────────────────────────────────

def analyze_portfolio(stocks_text, crypto_text, bids_text, bankroll):
    if not any([stocks_text, crypto_text, bids_text]):
        return "Please enter at least one holding.", None

    prompt = f"""You are an expert portfolio manager. Write as the professional analyst who performed this work. State all findings directly with specific numbers, percentages, and comparisons. NEVER say 'this appears to be', 'the data seems to show', 'the dataset contains', or 'it looks like'. Instead, deliver results confidently: 'Average claim cost was $4,230, a 12% increase year-over-year' or 'Readmission rates of 18.3% in Cardiology exceeded the facility average by 4.1 percentage points.' Be direct, precise, and actionable. Present findings as YOUR analysis, not a description of a dataset. Analyze this complete investment portfolio:

Total Bankroll: ${bankroll}

STOCK HOLDINGS:
{stocks_text if stocks_text else "None"}

CRYPTO HOLDINGS:
{crypto_text if crypto_text else "None"}

PREDICTION MARKET / BIDDING POSITIONS:
{bids_text if bids_text else "None"}

Produce a complete portfolio analysis with ALL of these sections:

## 1. PORTFOLIO OVERVIEW
Total Value: $X | Total P&L: $X (X%)
Asset Allocation breakdown with percentages.

## 2. RISK ASSESSMENT
Overall portfolio risk: [LOW / MEDIUM / HIGH / VERY HIGH]
Diversification score: X/10
Concentration risk: positions over 20% of portfolio
Correlation risk: positions that move together

## 3. POSITION BY POSITION ANALYSIS
Best performer. Worst performer.
Positions to consider exiting with reasons.
Positions to consider adding to with reasons.

## 4. REBALANCING RECOMMENDATIONS
Is rebalancing needed: YES / NO
3 specific recommended rebalancing actions.

## 5. MACRO ENVIRONMENT IMPACT
How current macro conditions affect each asset class.
Overall portfolio positioning recommendation.

## 6. RISK MANAGEMENT ALERTS
Positions exceeding risk limits. Stop losses to set.
Prediction market contracts approaching resolution.

Be specific with dollar amounts and percentages."""

    result = query_llm(prompt)

    fig = None
    try:
        labels = []
        values = []
        if stocks_text and stocks_text.strip():
            labels.append("Stocks")
            values.append(50)
        if crypto_text and crypto_text.strip():
            labels.append("Crypto")
            values.append(30)
        if bids_text and bids_text.strip():
            labels.append("Prediction Markets")
            values.append(20)
        if labels:
            fig = go.Figure(go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=["#3498db", "#f39c12", "#9b59b6"]
            ))
            fig.update_layout(title="Portfolio Allocation",
                              template="plotly_dark", height=400)
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 5: News Impact Engine ────────────────────────────────────────────────

def analyze_news(headline, source, datetime_str, holdings, market_open, context):
    if not headline:
        return "Please enter a news headline."

    prompt = f"""You are an expert market strategist and news analyst. Write as the professional analyst who performed this work. State all findings directly with specific numbers, percentages, and comparisons. NEVER say 'this appears to be', 'the data seems to show', 'the dataset contains', or 'it looks like'. Instead, deliver results confidently: 'Average claim cost was $4,230, a 12% increase year-over-year' or 'Readmission rates of 18.3% in Cardiology exceeded the facility average by 4.1 percentage points.' Be direct, precise, and actionable. Present findings as YOUR analysis, not a description of a dataset. 
Breaking News: {headline}
Source: {source}
Date/Time: {datetime_str}
Market Status: {market_open}
Current Holdings: {holdings}
Additional Context: {context}

Produce a complete news market impact analysis with ALL of these sections:

## 1. NEWS ANALYSIS
What this news means in plain English.
Credibility and significance: MAJOR / MODERATE / MINOR event

## 2. IMMEDIATE STOCK IMPACT
Stocks that will GO UP and why (with estimated % move).
Stocks that will GO DOWN and why (with estimated % move).
Sectors most affected. Specific tickers to watch.

## 3. CRYPTO IMPACT
Cryptos that will GO UP and why.
Cryptos that will GO DOWN and why.
RISK ON or RISK OFF for crypto?
Bitcoin expected direction: UP / DOWN / NEUTRAL

## 4. PREDICTION MARKET / BIDDING IMPACT
Which contracts change probability?
New bidding opportunities created by this news.
Specific platform recommendations.

## 5. YOUR PORTFOLIO IMPACT
Based on your holdings — specific action for each holding mentioned.

## 6. IMMEDIATE ACTION PLAN
What to do RIGHT NOW (next 30 minutes): 3 specific actions.
What to do TODAY: 2 specific actions.
What to WATCH for next.

## 7. CONTRARIAN VIEW
Is the obvious market reaction correct or an overreaction?
Historical precedent for similar news.

Be specific and actionable."""

    return query_llm(prompt) + "\n\n" + WATERMARK


# ─── Tab 6: Scenario Builder ──────────────────────────────────────────────────

def analyze_scenario(scenario, probability, timeframe, holdings, cash, risk_appetite, context):
    if not scenario:
        return "Please describe a scenario."

    prompt = f"""You are an expert macro strategist and scenario analyst. Write as the professional analyst who performed this work. State all findings directly with specific numbers, percentages, and comparisons. NEVER say 'this appears to be', 'the data seems to show', 'the dataset contains', or 'it looks like'. Instead, deliver results confidently: 'Average claim cost was $4,230, a 12% increase year-over-year' or 'Readmission rates of 18.3% in Cardiology exceeded the facility average by 4.1 percentage points.' Be direct, precise, and actionable. Present findings as YOUR analysis, not a description of a dataset. 
Scenario: {scenario}
User Estimated Probability: {probability}%
Timeframe: {timeframe}
Current Holdings: {holdings}
Cash Available: ${cash}
Risk Appetite: {risk_appetite}
Additional Context: {context}

Produce a complete scenario analysis with ALL of these sections:

## 1. SCENARIO ANALYSIS
Plain English explanation. Historical precedent.
Is {probability}% probability reasonable? AI estimated probability: X%

## 2. BULL CASE
Best case outcome. Assets that benefit most.
Estimated price targets. Probability: X%

## 3. BASE CASE
Most likely reaction. Assets affected.
Estimated market moves. Probability: X%

## 4. BEAR CASE
Worst case outcome. Assets hurt most.
Estimated downside. Probability: X%

## 5. YOUR PORTFOLIO IMPACT
For each holding: Bull / Base / Bear case impact in %.
Total portfolio impact in each scenario.

## 6. OPPORTUNITIES THIS SCENARIO CREATES
Stocks, crypto, and bidding contracts that become valuable.
Specific tickers and contracts with reasoning.

## 7. RISKS TO HEDGE AGAINST
Positions to reduce. Hedging strategies. Stop loss levels.

## 8. ACTION PLAN
If HIGH probability (over 60%): specific actions.
If MEDIUM (30-60%): specific actions.
If LOW (under 30%): whether to act at all.

## 9. BIDDING OPPORTUNITIES
Specific prediction market contracts on any platform that profit from this scenario.
Best risk/reward bets related to this scenario.

Be specific and strategic."""

    return query_llm(prompt) + "\n\n" + WATERMARK


# ─── Tab 7: Contrarian Detector ───────────────────────────────────────────────

def analyze_contrarian(asset, asset_type, consensus, price_odds, why_wrong, context):
    if not asset:
        return "Please enter an asset to analyze."

    prompt = f"""You are an expert contrarian investment analyst. Write as the professional analyst who performed this work. State all findings directly with specific numbers, percentages, and comparisons. NEVER say 'this appears to be', 'the data seems to show', 'the dataset contains', or 'it looks like'. Instead, deliver results confidently: 'Average claim cost was $4,230, a 12% increase year-over-year' or 'Readmission rates of 18.3% in Cardiology exceeded the facility average by 4.1 percentage points.' Be direct, precise, and actionable. Present findings as YOUR analysis, not a description of a dataset. 
Asset: {asset}
Asset Type: {asset_type}
Current Market Consensus: {consensus}
Current Price/Odds: {price_odds}
User's Contrarian Thesis: {why_wrong}
Additional Context: {context}

Produce a complete contrarian analysis with ALL of these sections:

## 1. CROWD SENTIMENT ANALYSIS
What the crowd currently believes.
Sentiment: EXTREMELY BULLISH / BULLISH / NEUTRAL / BEARISH / EXTREMELY BEARISH
How long has this sentiment been dominant? Signs of sentiment extremes.

## 2. CONTRARIAN CASE
Is the crowd wrong? YES / NO / POSSIBLY
Confidence: HIGH / MEDIUM / LOW
Key reasons the crowd may be wrong (3 specific arguments).

## 3. DATA VS NARRATIVE
What the actual data says vs what people believe.
Key metrics that contradict the consensus.
Disconnect: LARGE / MODERATE / SMALL

## 4. HISTORICAL CONTRARIAN PRECEDENTS
When was the crowd this wrong before?
Average return for contrarian position in similar situations: X%

## 5. CONTRARIAN OPPORTUNITY SCORE
Score: X/10
Opportunity type: AVOID THE CROWD / FADE THE MOVE / WAIT FOR CONFIRMATION

## 6. CONTRARIAN RECOMMENDATION
RECOMMENDATION: [STRONG CONTRARIAN BUY / CONTRARIAN BUY / NEUTRAL / CONTRARIAN SELL / STRONG CONTRARIAN SELL]
Confidence: [HIGH / MEDIUM / LOW]
What needs to happen for this to be proven right. What would prove it WRONG.

## 7. TIMING AND SIZING
When to enter. Position size. Catalyst. Expected timeframe.

## 8. RISK OF BEING WRONG
Maximum loss. Early warning signs. Exit strategy.

Be intellectually rigorous and specific."""

    return query_llm(prompt) + "\n\n" + WATERMARK


# ─── Tab 8: Fear & Greed Analyzer ────────────────────────────────────────────

def analyze_fear_greed(focus, market_conditions, recent_events,
                       emotional_state, action_thinking, context):
    prompt = f"""You are an expert behavioral finance and market sentiment analyst. Write as the professional analyst who performed this work. State all findings directly with specific numbers, percentages, and comparisons. NEVER say 'this appears to be', 'the data seems to show', 'the dataset contains', or 'it looks like'. Instead, deliver results confidently: 'Average claim cost was $4,230, a 12% increase year-over-year' or 'Readmission rates of 18.3% in Cardiology exceeded the facility average by 4.1 percentage points.' Be direct, precise, and actionable. Present findings as YOUR analysis, not a description of a dataset. 
Investment Focus: {focus}
Current Market Conditions: {market_conditions}
Recent Market Events: {recent_events}
User's Emotional State: {emotional_state}
User is Thinking of: {action_thinking}
Additional Context: {context}

Produce a complete Fear and Greed analysis with ALL of these sections:

## 1. CURRENT FEAR & GREED SCORE
Overall Market Fear and Greed: X/100
[0-25 = Extreme Fear | 26-45 = Fear | 46-55 = Neutral | 56-75 = Greed | 76-100 = Extreme Greed]

Individual scores:
- Stock Market: X/100 — [label]
- Crypto: X/100 — [label]
- Prediction Markets: X/100 — [label]

## 2. WHAT THIS SCORE MEANS
Historical context. Buying opportunity or warning signal?
How long do these extremes typically last?

## 3. INDICATORS DRIVING THE SCORE
Indicators showing FEAR (with current readings).
Indicators showing GREED (with current readings).

## 4. THE WARREN BUFFETT SIGNAL
Current signal: TIME TO BUY / TIME TO SELL / HOLD / WAIT
Historical accuracy at current levels.

## 5. YOUR EMOTIONAL STATE ANALYSIS
You feel: {emotional_state}. Is this aligned with or against the market?
DANGER ALERT if emotions match extreme market sentiment.
Is your planned action emotionally or data driven?

## 6. ASSET SPECIFIC RECOMMENDATIONS
Best assets to buy at current fear/greed level historically.
Assets to avoid. Mispriced bidding contracts.

## 7. ACTION PLAN
Specific actions for the current score level.

## 8. CONTRARIAN CHECKLIST
FOMO check. Panic selling check. Thesis change check.
Emotional decision warning: YES - proceed with caution / NO - proceed normally

Be direct and psychologically insightful."""

    return query_llm(prompt) + "\n\n" + WATERMARK


# ─── Tab 9: Events Calendar ───────────────────────────────────────────────────

def analyze_events(lookout_period, holdings, cash, known_events, risk_appetite, context):
    prompt = f"""You are an expert macro strategist and events-driven investor. Write as the professional analyst who performed this work. State all findings directly with specific numbers, percentages, and comparisons. NEVER say 'this appears to be', 'the data seems to show', 'the dataset contains', or 'it looks like'. Instead, deliver results confidently: 'Average claim cost was $4,230, a 12% increase year-over-year' or 'Readmission rates of 18.3% in Cardiology exceeded the facility average by 4.1 percentage points.' Be direct, precise, and actionable. Present findings as YOUR analysis, not a description of a dataset. 
Lookout Period: {lookout_period}
Current Holdings: {holdings if holdings else "Not specified"}
Cash Available: ${cash}
Known Upcoming Events: {known_events if known_events else "None specified"}
Risk Appetite: {risk_appetite}
Additional Context: {context}

Produce a complete events calendar analysis with ALL of these sections:

## 1. MAJOR UPCOMING EVENTS CALENDAR
List all major market-moving events in the {lookout_period}:

ECONOMIC EVENTS:
- [Date]: [Event] — Impact: HIGH / MEDIUM / LOW

CENTRAL BANK EVENTS:
- [Date]: [Fed/ECB/BOJ meeting] — Expected outcome and market impact

EARNINGS (Major companies):
- [Date]: [Company] — Expected sector impact

CRYPTO EVENTS:
- [Date]: [Network upgrade, ETF decision] — Expected impact

POLITICAL AND REGULATORY:
- [Date]: [Event] — Expected market impact

PREDICTION MARKET RESOLUTIONS:
- [Date]: [Major contracts approaching resolution]

## 2. HIGHEST IMPACT EVENT ANALYSIS
The single most important upcoming event — full breakdown.
Expected outcome. Market reaction. Surprise scenario.

## 3. PRE-EVENT POSITIONING STRATEGY
For each top event — what to Buy / Sell / Hold / Bid before it happens.

## 4. YOUR HOLDINGS PRE-EVENT ANALYSIS
For each holding — how each event affects it and recommended action.

## 5. BIDDING OPPORTUNITIES
Upcoming events that create opportunities on Polymarket, Kalshi, or other platforms.
Current mispriced contracts related to upcoming events.

## 6. CASH DEPLOYMENT PLAN
You have ${cash} available. Recommended deployment schedule by event.

## 7. RISK CALENDAR
Highest risk dates — when to reduce exposure.
Best buying opportunity dates — when to add positions.

## 8. WEEKLY ACTION CHECKLIST
Specific actions by week for the {lookout_period} period.

Be specific with dates, assets, and dollar amounts."""

    return query_llm(prompt) + "\n\n" + WATERMARK


# ─── Tab 10: AI Investment Chat ───────────────────────────────────────────────

def investment_chat(message, history):
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert investment analyst AI assistant specializing in stocks, "
                "cryptocurrencies, prediction markets (Polymarket, Kalshi, PredictIt, "
                "Manifold Markets, Metaculus, Robinhood Prediction Markets), portfolio management, "
                "macroeconomics, and behavioral finance. When asked a question, deliver the answer immediately with specific numbers. Do NOT explain how to calculate. Analyze investments, understand "
                "markets, evaluate bidding opportunities, and make informed decisions. Always remind "
                "users that nothing you say constitutes financial advice and they should consult a "
                "licensed financial advisor before making investment decisions. "
                "You can lose your entire investment."
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
    msgs = [{"role": "system", "content": INVESTMENT_SYSTEM_PROMPT}, {"role": "user", "content": prompt}]
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

with gr.Blocks(title="AI Investment Analyzer", theme=gr.themes.Base(
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
    gr.Markdown("# 💹 AI Investment Analyzer")
    gr.Markdown(DISCLAIMER)

    with gr.Tabs():

        # ── Tab 1: Stock Analyzer ──────────────────────────────────────────────
        with gr.Tab("📈 Stock Analyzer"):
            gr.Markdown("## Stock Analysis & Recommendation")
            gr.Markdown(INVEST_WARNING)
            with gr.Row():
                with gr.Column(scale=1):
                    s_ticker = gr.Textbox(label="Stock Ticker", placeholder="e.g. AAPL")
                    s_company = gr.Textbox(label="Company Name", placeholder="e.g. Apple Inc")
                    s_price = gr.Number(label="Current Stock Price ($)", value=0)
                    s_position = gr.Dropdown(
                        choices=["Not Invested", "Long", "Short"],
                        value="Not Invested", label="Your Position")
                    s_entry = gr.Number(label="Your Entry Price ($, optional)", value=0)
                    s_shares = gr.Number(label="Number of Shares (optional)", value=0)
                    s_horizon = gr.Dropdown(
                        choices=["Short Term", "Medium Term", "Long Term"],
                        value="Medium Term", label="Investment Horizon")
                    s_risk = gr.Dropdown(
                        choices=["Conservative", "Moderate", "Aggressive"],
                        value="Moderate", label="Risk Tolerance")
                    s_context = gr.Textbox(label="Extra Context", lines=3,
                                           placeholder="Any additional context...")
                    s_btn = gr.Button("📈 Analyze Stock", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    s_output = gr.Markdown(label="Stock Analysis")
            s_btn.click(analyze_stock,
                        inputs=[s_ticker, s_company, s_price, s_position,
                                s_entry, s_shares, s_horizon, s_risk, s_context],
                        outputs=[s_output])

        # ── Tab 2: Crypto Analyzer ─────────────────────────────────────────────
        with gr.Tab("₿ Crypto Analyzer"):
            gr.Markdown("## Cryptocurrency Analysis & Recommendation")
            gr.Markdown(INVEST_WARNING)
            with gr.Row():
                with gr.Column(scale=1):
                    c_name = gr.Textbox(label="Crypto Name", placeholder="e.g. Bitcoin")
                    c_ticker = gr.Textbox(label="Ticker Symbol", placeholder="e.g. BTC")
                    c_price = gr.Number(label="Current Price ($)", value=0)
                    c_position = gr.Dropdown(
                        choices=["Not Invested", "Long", "Short"],
                        value="Not Invested", label="Your Position")
                    c_entry = gr.Number(label="Your Entry Price ($, optional)", value=0)
                    c_amount = gr.Number(label="Amount Owned (optional)", value=0)
                    c_horizon = gr.Dropdown(
                        choices=["Short Term", "Medium Term", "Long Term"],
                        value="Medium Term", label="Investment Horizon")
                    c_risk = gr.Dropdown(
                        choices=["Conservative", "Moderate", "Aggressive"],
                        value="Moderate", label="Risk Tolerance")
                    c_network = gr.Dropdown(
                        choices=["Bitcoin", "Ethereum", "Solana", "BNB Chain", "Other"],
                        value="Bitcoin", label="Network")
                    c_context = gr.Textbox(label="Extra Context", lines=3)
                    c_btn = gr.Button("₿ Analyze Crypto", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    c_output = gr.Markdown(label="Crypto Analysis")
            c_btn.click(analyze_crypto,
                        inputs=[c_name, c_ticker, c_price, c_position,
                                c_entry, c_amount, c_horizon, c_risk,
                                c_network, c_context],
                        outputs=[c_output])

        # ── Tab 3: Bidding Analysis ────────────────────────────────────────────
        with gr.Tab("📊 Bidding Analysis"):
            gr.Markdown("## Prediction Market & Bidding Platform Analysis")
            gr.Markdown(BETTING_WARNING)
            with gr.Row():
                with gr.Column(scale=1):
                    b_platform = gr.Dropdown(
                        choices=["Polymarket", "Kalshi", "PredictIt",
                                 "Manifold Markets", "Metaculus",
                                 "Robinhood Prediction Markets", "Other (specify)"],
                        value="Polymarket", label="Select Bidding Platform")
                    b_platform_other = gr.Textbox(
                        label="If Other — specify platform name",
                        placeholder="Platform name...")
                    b_question = gr.Textbox(
                        label="Contract / Market Question", lines=2,
                        placeholder="e.g. Will the Fed cut rates in June 2026?")
                    b_yes_price = gr.Slider(
                        minimum=1, maximum=99, value=50,
                        label="Current YES Price / Implied Probability (%)")
                    b_position = gr.Dropdown(
                        choices=["Not Entered", "YES", "NO"],
                        value="Not Entered", label="Your Current Position")
                    b_entry = gr.Number(label="Your Entry Price (%)", value=0)
                    b_bet = gr.Number(label="Bid Amount ($)", value=0)
                    b_date = gr.Textbox(
                        label="Resolution Date (MM/DD/YYYY)",
                        placeholder="e.g. 06/30/2026")
                    b_category = gr.Dropdown(
                        choices=["Politics", "Economics", "Crypto", "Sports",
                                 "Science", "Weather", "Markets", "Other"],
                        value="Economics", label="Contract Category")
                    b_context = gr.Textbox(label="Extra Context", lines=3)
                    b_btn = gr.Button("📊 Analyze Bid", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    b_output = gr.Markdown(label="Bidding Analysis")
            b_btn.click(analyze_bidding,
                        inputs=[b_platform, b_platform_other, b_question,
                                b_yes_price, b_position, b_entry, b_bet,
                                b_date, b_category, b_context],
                        outputs=[b_output])

        # ── Tab 4: Portfolio Dashboard ─────────────────────────────────────────
        with gr.Tab("💼 Portfolio Dashboard"):
            gr.Markdown("## Complete Investment Portfolio Analysis")
            gr.Markdown(INVEST_WARNING)
            with gr.Row():
                with gr.Column(scale=1):
                    port_bankroll = gr.Number(label="Total Bankroll ($)", value=10000)
                    port_stocks = gr.Textbox(
                        label="Stock Holdings", lines=4,
                        placeholder="e.g.\nAAPL, 10 shares, entry $150, current $185\nNVDA, 5 shares, entry $400, current $950")
                    port_crypto = gr.Textbox(
                        label="Crypto Holdings", lines=4,
                        placeholder="e.g.\nBitcoin, 0.5 BTC, entry $40000, current $85000\nEthereum, 2 ETH, entry $2000, current $3200")
                    port_bids = gr.Textbox(
                        label="Prediction Market / Bidding Positions", lines=4,
                        placeholder="e.g.\nPolymarket: Fed rate cut June, YES, entry 45%, current 62%, $200\nKalshi: CPI above 3%, YES, entry 40 cents, current 55 cents, 10 contracts")
                    port_btn = gr.Button("💼 Analyze Portfolio", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    port_output = gr.Markdown(label="Portfolio Analysis")
            port_chart = gr.Plot(label="Portfolio Allocation")
            port_btn.click(analyze_portfolio,
                           inputs=[port_stocks, port_crypto,
                                   port_bids, port_bankroll],
                           outputs=[port_output, port_chart])

        # ── Tab 5: News Impact Engine ──────────────────────────────────────────
        with gr.Tab("📰 News Impact Engine"):
            gr.Markdown("## Breaking News → Immediate Market Impact Analysis")
            gr.Markdown(INVEST_WARNING)
            with gr.Row():
                with gr.Column(scale=1):
                    n_headline = gr.Textbox(
                        label="Breaking News Headline", lines=2,
                        placeholder="e.g. Fed unexpectedly raises rates 0.5%")
                    n_source = gr.Textbox(
                        label="News Source",
                        placeholder="e.g. Reuters, Bloomberg, Twitter/X")
                    n_datetime = gr.Textbox(
                        label="Date / Time",
                        placeholder="e.g. Today 2:30 PM EST")
                    n_holdings = gr.Textbox(
                        label="Your Current Holdings", lines=3,
                        placeholder="e.g. I own AAPL, BTC, and YES on Fed rate cut Polymarket")
                    n_market_open = gr.Dropdown(
                        choices=["Yes", "No", "Pre-Market", "After-Hours"],
                        value="Yes", label="Market Currently Open?")
                    n_context = gr.Textbox(label="Extra Context", lines=2)
                    n_btn = gr.Button("📰 Analyze News Impact", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    n_output = gr.Markdown(label="News Impact Analysis")
            n_btn.click(analyze_news,
                        inputs=[n_headline, n_source, n_datetime,
                                n_holdings, n_market_open, n_context],
                        outputs=[n_output])

        # ── Tab 6: Scenario Builder ────────────────────────────────────────────
        with gr.Tab("🎭 Scenario Builder"):
            gr.Markdown("## Portfolio Stress Test & Scenario Analysis")
            gr.Markdown(INVEST_WARNING)
            with gr.Row():
                with gr.Column(scale=1):
                    sc_scenario = gr.Textbox(
                        label="Scenario Description", lines=3,
                        placeholder="e.g. What if Trump announces 50% tariffs on all Chinese goods tomorrow?")
                    sc_probability = gr.Slider(
                        minimum=1, maximum=99, value=30,
                        label="Scenario Probability (%)")
                    sc_timeframe = gr.Dropdown(
                        choices=["Happening Now", "Within 1 Week", "Within 1 Month",
                                 "Within 6 Months", "Within 1 Year"],
                        value="Within 1 Month", label="Scenario Timeframe")
                    sc_holdings = gr.Textbox(
                        label="Your Current Holdings", lines=3,
                        placeholder="List your stocks, crypto, and bidding positions")
                    sc_cash = gr.Number(label="Cash Available ($)", value=1000)
                    sc_risk = gr.Dropdown(
                        choices=["Very Conservative", "Conservative", "Moderate",
                                 "Aggressive", "Very Aggressive"],
                        value="Moderate", label="Risk Appetite for This Scenario")
                    sc_context = gr.Textbox(label="Extra Context", lines=2)
                    sc_btn = gr.Button("🎭 Build Scenario", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    sc_output = gr.Markdown(label="Scenario Analysis")
            sc_btn.click(analyze_scenario,
                         inputs=[sc_scenario, sc_probability, sc_timeframe,
                                 sc_holdings, sc_cash, sc_risk, sc_context],
                         outputs=[sc_output])

        # ── Tab 7: Contrarian Detector ─────────────────────────────────────────
        with gr.Tab("🧠 Contrarian Detector"):
            gr.Markdown("## Find Where the Crowd Is Wrong")
            gr.Markdown(INVEST_WARNING)
            with gr.Row():
                with gr.Column(scale=1):
                    ct_asset = gr.Textbox(
                        label="Asset to Analyze",
                        placeholder="e.g. NVDA, Bitcoin, or Fed rate cut market")
                    ct_type = gr.Dropdown(
                        choices=["Stock", "Crypto", "Prediction Market / Bid"],
                        value="Stock", label="Asset Type")
                    ct_consensus = gr.Textbox(
                        label="Current Market Consensus", lines=2,
                        placeholder="e.g. Everyone is bullish on NVDA because of AI demand")
                    ct_price = gr.Textbox(
                        label="Current Price or Odds",
                        placeholder="e.g. $950 or 80%")
                    ct_why = gr.Textbox(
                        label="Why You Think the Crowd May Be Wrong",
                        lines=3, placeholder="Optional — your contrarian thesis")
                    ct_context = gr.Textbox(label="Extra Context", lines=2)
                    ct_btn = gr.Button("🧠 Detect Contrarian Opportunity", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    ct_output = gr.Markdown(label="Contrarian Analysis")
            ct_btn.click(analyze_contrarian,
                         inputs=[ct_asset, ct_type, ct_consensus,
                                 ct_price, ct_why, ct_context],
                         outputs=[ct_output])

        # ── Tab 8: Fear & Greed ────────────────────────────────────────────────
        with gr.Tab("😱 Fear & Greed"):
            gr.Markdown("## Market Emotion Analysis — Optimal Entry & Exit Timing")
            gr.Markdown(INVEST_WARNING)
            with gr.Row():
                with gr.Column(scale=1):
                    fg_focus = gr.Dropdown(
                        choices=["Stocks", "Crypto", "Both",
                                 "Prediction Markets", "All"],
                        value="All", label="Your Investment Focus")
                    fg_conditions = gr.Textbox(
                        label="Describe Current Market Conditions", lines=3,
                        placeholder="e.g. Market has been dropping for 2 weeks, everyone is panicking")
                    fg_events = gr.Textbox(
                        label="Recent Market Events", lines=2,
                        placeholder="e.g. Fed raised rates, inflation still high, tech stocks down 20%")
                    fg_emotion = gr.Dropdown(
                        choices=["Very Fearful", "Fearful", "Neutral",
                                 "Greedy", "Very Greedy"],
                        value="Neutral", label="Your Current Emotional State")
                    fg_action = gr.Dropdown(
                        choices=["Thinking of Buying", "Thinking of Selling",
                                 "Holding", "Unsure"],
                        value="Unsure", label="Are You Thinking of Buying or Selling?")
                    fg_context = gr.Textbox(label="Extra Context", lines=2)
                    fg_btn = gr.Button("😱 Analyze Fear & Greed", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    fg_output = gr.Markdown(label="Fear & Greed Analysis")
            fg_btn.click(analyze_fear_greed,
                         inputs=[fg_focus, fg_conditions, fg_events,
                                 fg_emotion, fg_action, fg_context],
                         outputs=[fg_output])

        # ── Tab 9: Events Calendar ─────────────────────────────────────────────
        with gr.Tab("⏰ Events Calendar"):
            gr.Markdown("## Upcoming Events — Position Your Portfolio Before They Happen")
            gr.Markdown(INVEST_WARNING)
            with gr.Row():
                with gr.Column(scale=1):
                    ev_period = gr.Dropdown(
                        choices=["Next 7 Days", "Next 30 Days", "Next 90 Days"],
                        value="Next 30 Days", label="Lookout Period")
                    ev_holdings = gr.Textbox(
                        label="Your Current Holdings", lines=3,
                        placeholder="List stocks, crypto, and bidding positions")
                    ev_cash = gr.Number(label="Cash Available ($)", value=1000)
                    ev_known = gr.Textbox(
                        label="Specific Events You Know About (optional)", lines=3,
                        placeholder="e.g. FOMC meeting March 15, NVDA earnings Feb 20")
                    ev_risk = gr.Dropdown(
                        choices=["Conservative", "Moderate", "Aggressive"],
                        value="Moderate", label="Risk Appetite")
                    ev_context = gr.Textbox(label="Extra Context", lines=2)
                    ev_btn = gr.Button("⏰ Analyze Events Calendar", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    ev_output = gr.Markdown(label="Events Calendar Analysis")
            ev_btn.click(analyze_events,
                         inputs=[ev_period, ev_holdings, ev_cash,
                                 ev_known, ev_risk, ev_context],
                         outputs=[ev_output])

        # ── Tab 10: AI Investment Chat ─────────────────────────────────────────
        with gr.Tab("💬 AI Investment Chat"):
            gr.Markdown("## Ask the AI Anything About Investing")
            gr.Markdown(INVEST_WARNING)
            gr.ChatInterface(
                fn=investment_chat,
                examples=[
                    "What is the current outlook for the S&P 500?",
                    "Explain how prediction markets like Polymarket work",
                    "What is the Kelly Criterion and how do I use it for bidding?",
                    "How should I think about portfolio diversification?",
                    "What are the key indicators to watch for a crypto bull run?",
                    "Explain what a contrarian investment strategy is",
                    "What does the Fear and Greed Index tell us about markets?",
                    "What is the difference between Kalshi and Polymarket?",
                ],
                title="",
            )

    gr.Markdown(WATERMARK)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("GRADIO_SERVER_PORT", 7860)), share=False, ssr_mode=False)
