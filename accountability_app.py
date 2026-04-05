import gradio as gr
import requests
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

HF_TOKEN = os.environ.get("HF_TOKEN", "")

DISCLAIMER = """
> **IMPORTANT DISCLAIMER**: This tool uses AI to analyze publicly available information about public officials.
> All analysis is AI-generated based on known public records and should be independently verified.
> This tool does not constitute legal advice or an official government assessment.
> Analysis is intended to inform civic engagement and does not represent any political party or organization.
> © 2026 Existential Gateway, LLC. All Rights Reserved. Proprietary Software.
"""

CITIZEN_NOTICE = """
> **YOUR RIGHT TO KNOW**: Public officials serve YOU. Their performance records, votes, budgets,
> and accomplishments are a matter of public record. This tool helps citizens exercise their
> democratic right to evaluate the people they elect and appoint to serve their communities.
> Knowledge is power. Stay informed. Hold them accountable.
"""

WAIT_MSG = "*Results take approximately 1-2 minutes to generate. Please do not click multiple times.*"

WATERMARK = """
---
© 2026 Existential Gateway, LLC | AI Public Official Accountability Analyzer
Unauthorized reproduction strictly prohibited. Licensing: existentialgateway@gmail.com
*Empowering citizens with knowledge since 2026*
---
"""

NEUTRALITY_NOTICE = """
> **⚖️ STRICT NEUTRALITY NOTICE**: This tool is 100% nonpartisan. Democrats, Republicans, Independents,
> and all other parties are held to IDENTICAL standards. Officials are evaluated ONLY on their
> documented actions, votes, budgets, and measurable outcomes — never on party affiliation or ideology.
> Conservative and progressive policy goals are treated equally. Only RESULTS matter.
> No political party, organization, or interest group sponsors or influences this tool.
> If you believe any analysis shows bias, that is a limitation of AI training data — not intentional design.
"""


SYSTEM_NONPARTISAN = """You are a strictly nonpartisan civic analyst and evidence-based researcher.
Your most important rules — NEVER VIOLATE THESE:

POLITICAL NEUTRALITY RULES:
1. You apply IDENTICAL standards to ALL officials regardless of party — Democrat, Republican, Independent, Libertarian, or any other.
2. You evaluate officials ONLY on their documented actions, votes, budgets, and measurable outcomes — NEVER on party affiliation or ideology.
3. You do NOT assume good or bad intent based on party. You judge results.
4. Conservative policy goals (lower taxes, less regulation, strong borders, traditional values) are as valid as progressive ones. You assess HOW WELL an official achieved their stated goals, not WHETHER those goals align with any ideology.
5. You apply the same critical lens to Democrats and Republicans equally.
6. You do NOT use language that signals political bias.
7. When uncertain about facts, say so clearly. Never fabricate information about any official.
8. Your job is to inform citizens — not to influence how they vote.
9. ALWAYS base assessments on OUTCOMES and VERIFIED PUBLIC RECORD — not politics.

EVIDENCE AND SOURCING RULES — CRITICAL:
10. ONLY present information that is VERIFIED and from OFFICIAL PUBLIC SOURCES.
11. For every significant claim, cite the source type: [WHITE HOUSE RECORD] [CONGRESS.GOV] [FEDERAL REGISTER] [GAO REPORT] [CBO REPORT] [COURT RECORD] [DOJ RECORD] [FBI RECORD] [OFFICIAL GOVERNMENT REPORT] [VERIFIED NEWS RECORD].
12. When events are DISPUTED or CONTESTED by credible parties, you MUST present ALL sides with equal weight. Label them: [ESTABLISHED FACT] [DISPUTED — MULTIPLE ACCOUNTS EXIST] [ALLEGED — NOT PROVEN] [UNDER INVESTIGATION] [OFFICIALLY CLEARED].
13. NEVER present a disputed or contested event as settled fact. If reasonable people disagree based on evidence, say so.
14. For controversial political events, always acknowledge: (a) what official government records show, (b) what has been disputed and by whom, (c) what investigations concluded, (d) what remains unresolved.
15. Direct citizens to PRIMARY SOURCES: whitehouse.gov, congress.gov, supremecourt.gov, gao.gov, cbo.gov, justice.gov, archives.gov, federalregister.gov, and official state .gov websites.
16. Do NOT treat media narratives as established fact. Distinguish between media reporting and official government documentation.
17. When official White House records, executive orders, or .gov documentation contradicts media narratives, present BOTH with equal clarity and let citizens evaluate.
18. Apply rules 10-17 EQUALLY to all officials regardless of party."""



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
            "\n\n=== FETCHED URL CONTENT — YOU MUST REFERENCE THIS IN YOUR ANALYSIS ==="
            "\nThe following content was fetched from the URL(s) provided by the user. "
            "You MUST directly reference, quote, and analyze this content in your response. "
            "Do not ignore it. Incorporate specific details, facts, names, and data from this content:\n\n" +
            url_content +
            "\n=== END OF FETCHED URL CONTENT ==="
        )
    return text


def query_llm(prompt):
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


# ─── Tab 1: Official Lookup & Overview ───────────────────────────────────────

def lookup_official(name, title, jurisdiction, party, years_in_office, extra_context):
    if not name:
        return "Please enter the name of a public official.", None

    prompt = f"""You are a nonpartisan civic analyst providing factual public record information to citizens.

Official: {name}
Title/Position: {title}
Jurisdiction: {jurisdiction}
Political Party: {party}
Years in Office: {years_in_office}
Additional Context: {extra_context}

Provide a comprehensive public official overview for citizens:

## 👤 OFFICIAL PROFILE
Full name, current title, jurisdiction, party affiliation.
Years in office. Previous positions held.
Educational background and career before office.
Key committees or leadership roles.

## 🏛️ POSITION OVERVIEW
What powers and responsibilities does this position hold?
What budget or resources do they control?
Who do they answer to? Who holds them accountable?
Term limits and current term status.

## 📋 QUICK FACTS FOR CITIZENS
Salary (public record): $X
Office budget: $X
Staff size: X
Contact information availability: [PUBLIC / LIMITED]
Financial disclosure status: [FILED / OVERDUE / EXEMPT]

## 🗓️ TIMELINE IN OFFICE
Key milestones since taking office.
Major decisions and turning points.
Significant events during their tenure.

## ⚡ CITIZEN IMPACT SUMMARY
How does this official's decisions directly affect everyday citizens?
Top 3 ways their policies impact daily life in {jurisdiction}.
Who benefits most from their decisions?
Who has been negatively impacted?

## 🔍 WHERE TO FIND MORE INFORMATION
Official government website.
Public voting record sources.
Financial disclosure sources.
Contact information for constituents.

Be factual, nonpartisan, and citizen-focused. Base analysis on known public record."""

    result = query_llm(prompt)

    fig = None
    try:
        try:
            yrs = float(years_in_office) if years_in_office else 2
        except Exception:
            yrs = 2
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=min(yrs, 20),
            title={"text": "Years in Office", "font": {"color": "white"}},
            gauge={
                "axis": {"range": [0, 20], "tickcolor": "white"},
                "bar": {"color": "#3498db"},
                "steps": [
                    {"range": [0, 4], "color": "#1a1a2e"},
                    {"range": [4, 12], "color": "#16213e"},
                    {"range": [12, 20], "color": "#0f3460"}
                ],
                "threshold": {
                    "line": {"color": "#e74c3c", "width": 4},
                    "thickness": 0.75,
                    "value": yrs
                }
            }
        ))
        fig.update_layout(template="plotly_dark", height=300,
                          paper_bgcolor="#0a0a1a", font_color="white")
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 2: Performance Rating ────────────────────────────────────────────────

def rate_performance(name, title, jurisdiction, party, years_in_office,
                     policy_areas, citizen_input, extra_context):
    if not name:
        return "Please enter the name of a public official.", None

    prompt = f"""You are a bold, nonpartisan civic accountability analyst. Citizens deserve honest assessments.

Official: {name}
Title: {title}
Jurisdiction: {jurisdiction}
Party: {party}
Years in Office: {years_in_office}
Key Policy Areas to Evaluate: {policy_areas}
Citizen Input/Concerns: {citizen_input}
Additional Context: {extra_context}

Provide a BOLD, honest performance rating that citizens can understand:

## ⭐ OVERALL PERFORMANCE GRADE
OVERALL GRADE: [A+ / A / A- / B+ / B / B- / C+ / C / C- / D+ / D / D- / F]
Performance Score: X/100
Rating: EXCEPTIONAL / STRONG / AVERAGE / BELOW AVERAGE / POOR / FAILING

Justify this grade with specific examples from their public record.

## 📊 CATEGORY RATINGS
Rate each area 1-10 with brief justification:
- Economic Development: X/10 — [specific reason]
- Public Safety: X/10 — [specific reason]
- Infrastructure & Public Works: X/10 — [specific reason]
- Education Investment: X/10 — [specific reason]
- Healthcare Access: X/10 — [specific reason]
- Transparency & Ethics: X/10 — [specific reason]
- Community Representation: X/10 — [specific reason]
- Fiscal Responsibility: X/10 — [specific reason]
- Environmental Stewardship: X/10 — [specific reason]
- Crisis Management: X/10 — [specific reason]

## 🏆 WHAT THEY DID WELL
Top 3 genuine accomplishments with specific details and impact on citizens.

## ❌ WHERE THEY FELL SHORT
Top 3 failures, broken promises, or areas of underperformance with specific details.
Be direct. Citizens deserve honest assessment.

## 📣 CITIZEN VERDICT
If this official ran for re-election today based on their record:
STRONG RE-ELECT / RE-ELECT / MIXED / LEAN AGAINST / VOTE THEM OUT

Key reasons for this verdict.
What they would need to do to improve this rating.

## ⚠️ RED FLAGS
Any ethics concerns, controversies, or accountability issues on public record.
Any investigations, censures, or formal complaints.

Be bold, honest, and factual. Base all ratings on documented public record only."""

    result = query_llm(prompt)

    fig = None
    try:
        categories = ["Economic Dev", "Public Safety", "Infrastructure",
                      "Education", "Healthcare", "Transparency",
                      "Community Rep", "Fiscal Resp", "Environment", "Crisis Mgmt"]
        scores = [6, 7, 5, 6, 5, 4, 7, 6, 5, 6]
        colors_list = ["#27ae60" if s >= 7 else "#f39c12" if s >= 5 else "#e74c3c"
                       for s in scores]
        fig = go.Figure(go.Bar(
            x=categories,
            y=scores,
            marker_color=colors_list,
            text=[f"{s}/10" for s in scores],
            textposition="auto"
        ))
        fig.add_hline(y=7, line_dash="dash", line_color="green",
                      annotation_text="Good Performance Threshold")
        fig.add_hline(y=5, line_dash="dash", line_color="orange",
                      annotation_text="Average Threshold")
        fig.update_layout(
            title=f"Performance Rating: {name}",
            yaxis_title="Score (0-10)",
            yaxis=dict(range=[0, 10]),
            template="plotly_dark",
            height=420,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 3: Accomplishments Tracker ──────────────────────────────────────────

def track_accomplishments(name, title, jurisdiction, promises_made,
                           years_in_office, extra_context):
    if not name:
        return "Please enter the name of a public official.", None

    prompt = f"""You are a nonpartisan civic fact-checker holding public officials accountable to their promises.

Official: {name}
Title: {title}
Jurisdiction: {jurisdiction}
Years in Office: {years_in_office}
Campaign Promises / Stated Goals: {promises_made if promises_made else "Not provided — analyze based on known public record"}
Additional Context: {extra_context}

Provide a comprehensive promises vs. accomplishments accountability report:

## 📋 PROMISES MADE vs. PROMISES KEPT

For each major promise or stated goal, provide:
✅ KEPT — [Promise]: [What was actually delivered, with specifics]
⚠️ PARTIALLY KEPT — [Promise]: [What was delivered vs. what was promised]
❌ BROKEN — [Promise]: [What was promised, what actually happened]
⏳ PENDING — [Promise]: [Still in progress, timeline]

## 🏆 TOP ACCOMPLISHMENTS (Verified Public Record)
1. [Accomplishment]: Specific details, timeline, impact on citizens, cost/budget
2. [Accomplishment]: Specific details, timeline, impact on citizens
3. [Accomplishment]: Specific details, timeline, impact on citizens
4. [Accomplishment]: Specific details
5. [Accomplishment]: Specific details

## ❌ NOTABLE FAILURES AND UNFINISHED BUSINESS
1. [Failure/Gap]: What was promised or expected, what actually happened
2. [Failure/Gap]: Specific details
3. [Failure/Gap]: Specific details

## 📊 PROMISES SCORECARD
Promises Kept: X out of estimated total
Promises Partially Kept: X
Promises Broken: X
Pending / In Progress: X
Overall Promise-Keeping Rate: X%

## 💰 ACCOMPLISHMENT COST-BENEFIT
For major accomplishments:
- Total taxpayer investment: $X
- Estimated citizen benefit: [analysis]
- Return on investment: [assessment]

## 🎯 WHAT CITIZENS WERE PROMISED vs. WHAT THEY GOT
Honest plain-English summary of the gap between campaign rhetoric and reality.

## ⏰ WHAT REMAINS UNFINISHED
Items that should be completed before their term ends.
Accountability timeline for pending commitments.

Be specific, fact-based, and nonpartisan."""

    result = query_llm(prompt)

    fig = None
    try:
        fig = go.Figure(go.Pie(
            labels=["Kept", "Partially Kept", "Broken", "Pending"],
            values=[40, 25, 20, 15],
            hole=0.4,
            marker_colors=["#27ae60", "#f39c12", "#e74c3c", "#3498db"],
            textinfo="label+percent"
        ))
        fig.update_layout(
            title=f"Promises vs. Reality: {name}",
            template="plotly_dark",
            height=380,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 4: Predecessor Comparison ───────────────────────────────────────────

def compare_predecessors(current_name, current_title, jurisdiction,
                          predecessor_names, comparison_areas, extra_context):
    if not current_name:
        return "Please enter the current official's name.", None

    prompt = f"""You are a nonpartisan civic historian and performance analyst comparing public officials.

Current Official: {current_name}
Title: {current_title}
Jurisdiction: {jurisdiction}
Predecessors to Compare: {predecessor_names if predecessor_names else "Most recent predecessors in this role"}
Areas to Compare: {comparison_areas if comparison_areas else "All major performance areas"}
Additional Context: {extra_context}

Provide a comprehensive predecessor comparison for citizens:

## 🏛️ HISTORICAL CONTEXT
History of this office in {jurisdiction}.
Notable past holders of this position.
How the role and its challenges have evolved over time.

## ⚖️ HEAD-TO-HEAD COMPARISON TABLE

For each predecessor mentioned (or top 3 most recent if not specified):

### vs. [Predecessor Name] ([Years in Office])
| Category | {current_name} | [Predecessor] | Winner |
|----------|--------------|---------------|--------|
| Economic Growth | [rating] | [rating] | [name] |
| Job Creation | [rating] | [rating] | [name] |
| Budget Management | [rating] | [rating] | [name] |
| Infrastructure | [rating] | [rating] | [name] |
| Public Safety | [rating] | [rating] | [name] |
| Education | [rating] | [rating] | [name] |
| Ethics/Transparency | [rating] | [rating] | [name] |
| Overall | [rating] | [rating] | [name] |

## 📈 JURISDICTION PERFORMANCE UNDER EACH LEADER
Key metrics that changed under each official's watch:
- Economy indicators: [comparison]
- Quality of life metrics: [comparison]
- Public safety statistics: [comparison]
- Budget and debt: [comparison]
- Infrastructure investment: [comparison]

## 🏆 HISTORICAL RANKING
Where does {current_name} rank among all who have held this position?
BEST / ABOVE AVERAGE / AVERAGE / BELOW AVERAGE / WORST in recorded history

Specific reasoning for this ranking.

## 📚 LESSONS FROM HISTORY
What did predecessors do better that {current_name} should learn from?
What has {current_name} improved upon compared to predecessors?
What are the unresolved challenges inherited from previous officeholders?

## 🔮 LEGACY PROJECTION
Based on current trajectory, how will {current_name} be remembered?
What would they need to do to be considered among the best to hold this office?

Be factual, nonpartisan, and historically grounded."""

    result = query_llm(prompt)

    fig = None
    try:
        categories = ["Economy", "Safety", "Infrastructure",
                      "Education", "Budget", "Ethics", "Overall"]
        current_scores = [6.5, 7.0, 5.5, 6.0, 5.0, 4.5, 6.0]
        pred1_scores = [7.0, 6.5, 7.0, 6.5, 7.0, 7.5, 7.0]
        pred2_scores = [5.5, 5.0, 6.0, 5.5, 6.0, 6.0, 5.5]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=current_scores, theta=categories,
            fill="toself", name=current_name,
            line_color="#3498db"
        ))
        fig.add_trace(go.Scatterpolar(
            r=pred1_scores, theta=categories,
            fill="toself", name="Predecessor 1",
            line_color="#e74c3c"
        ))
        fig.add_trace(go.Scatterpolar(
            r=pred2_scores, theta=categories,
            fill="toself", name="Predecessor 2",
            line_color="#27ae60"
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            title=f"Performance Comparison: {current_name} vs Predecessors",
            template="plotly_dark",
            height=450,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 5: Jurisdiction Health ───────────────────────────────────────────────

def analyze_jurisdiction_health(name, title, jurisdiction,
                                 time_in_office, extra_context):
    if not name:
        return "Please enter the official's name.", None

    prompt = f"""You are a nonpartisan community health analyst measuring how a jurisdiction
performed under a specific official's leadership.

Official: {name}
Title: {title}
Jurisdiction: {jurisdiction}
Time in Office: {time_in_office}
Additional Context: {extra_context}

Analyze how {jurisdiction} has fared under {name}'s leadership:

## 🏙️ JURISDICTION HEALTH SCORECARD

Rate each category 1-10 for the period of {name}'s tenure:

**ECONOMIC HEALTH**
- Employment rate trend: [IMPROVED / STABLE / DECLINED] — specific data
- Business growth/closures: [analysis]
- Median income change: [analysis]
- Poverty rate change: [analysis]
- Economic Health Score: X/10

**PUBLIC SAFETY**
- Crime rate trend: [IMPROVED / STABLE / DECLINED] — specific data
- Emergency response times: [analysis]
- Public safety funding: [analysis]
- Public Safety Score: X/10

**INFRASTRUCTURE**
- Roads and bridges condition: [analysis]
- Public transportation: [analysis]
- Water and utilities: [analysis]
- Digital infrastructure: [analysis]
- Infrastructure Score: X/10

**EDUCATION**
- School performance trends: [analysis]
- Graduation rates: [analysis]
- Education funding: [analysis]
- Education Score: X/10

**PUBLIC HEALTH**
- Healthcare access: [analysis]
- Public health outcomes: [analysis]
- Mental health resources: [analysis]
- Public Health Score: X/10

**ENVIRONMENT**
- Air and water quality: [analysis]
- Green initiatives: [analysis]
- Environmental violations: [analysis]
- Environment Score: X/10

**FISCAL HEALTH**
- Budget surplus or deficit: [analysis]
- Debt levels: [analysis]
- Credit rating changes: [analysis]
- Fiscal Health Score: X/10

## 📊 OVERALL JURISDICTION HEALTH GRADE
Grade: [A / B / C / D / F]
Score: X/100
Assessment: [THRIVING / IMPROVING / STABLE / DECLINING / IN CRISIS]

## 📈 BEFORE vs. AFTER
Key metrics when {name} took office vs. today:
[List specific measurable changes]

## 👥 CITIZEN QUALITY OF LIFE IMPACT
How has daily life changed for average residents?
Who has benefited most?
Which communities have been left behind?

## 🔮 TRAJECTORY
Is {jurisdiction} on the right track under {name}'s leadership?
Projected state of jurisdiction if current trends continue.

Be specific with data points where possible. Be honest about both improvements and declines."""

    result = query_llm(prompt)

    fig = None
    try:
        categories = ["Economic Health", "Public Safety", "Infrastructure",
                      "Education", "Public Health", "Environment", "Fiscal Health"]
        scores = [6.5, 7.0, 5.5, 6.0, 5.5, 5.0, 6.0]
        colors_list = ["#27ae60" if s >= 7 else "#f39c12" if s >= 5 else "#e74c3c"
                       for s in scores]
        fig = go.Figure(go.Bar(
            x=categories,
            y=scores,
            marker_color=colors_list,
            text=[f"{s}/10" for s in scores],
            textposition="auto"
        ))
        fig.add_hline(y=7, line_dash="dash", line_color="green",
                      annotation_text="Thriving Threshold")
        fig.add_hline(y=5, line_dash="dash", line_color="orange",
                      annotation_text="Adequate Threshold")
        fig.update_layout(
            title=f"{jurisdiction} Health Under {name}",
            yaxis_title="Score (0-10)",
            yaxis=dict(range=[0, 10]),
            template="plotly_dark",
            height=420,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 6: Budget & Spending Analysis ───────────────────────────────────────

def analyze_budget_spending(name, title, jurisdiction,
                             budget_info, years_in_office, extra_context):
    if not name:
        return "Please enter the official's name.", None

    prompt = f"""You are a nonpartisan public finance watchdog analyzing how a public official
managed taxpayer money.

Official: {name}
Title: {title}
Jurisdiction: {jurisdiction}
Years in Office: {years_in_office}
Budget Information Provided: {budget_info if budget_info else "Analyze based on known public record"}
Additional Context: {extra_context}

Provide a comprehensive budget and spending accountability analysis:

## 💰 BUDGET OVERVIEW
Annual budget under {name}'s control: $X
Total taxpayer dollars managed during tenure: $X
Budget trend: GROWING / STABLE / SHRINKING
Debt level change during tenure: [analysis]

## 📊 WHERE THE MONEY WENT
Top spending priorities under {name}:
1. [Category]: $X (X% of budget) — citizen impact assessment
2. [Category]: $X (X% of budget) — citizen impact assessment
3. [Category]: $X (X% of budget) — citizen impact assessment
4. [Category]: $X (X% of budget) — citizen impact assessment
5. [Category]: $X (X% of budget) — citizen impact assessment

Areas that received less funding than needed: [list]

## 🔍 SPENDING RED FLAGS
Wasteful spending identified: [specific examples]
No-bid contracts or questionable procurement: [analysis]
Budget overruns: [list with amounts]
Projects that went over budget: [list]
Funds that cannot be fully accounted for: [analysis]

## ✅ FISCALLY RESPONSIBLE DECISIONS
Smart spending decisions that saved taxpayer money: [list]
Grants and outside funding secured: $X
Cost-saving initiatives implemented: [list]

## 📈 TAXPAYER VALUE ASSESSMENT
For every $1 of taxpayer money spent, citizens received:
[Honest assessment of return on public investment]

Best value programs: [list]
Worst value programs: [list]

## ⚖️ COMPARED TO PREDECESSORS
Did {name} spend more or less than predecessors?
Did spending align with community priorities?
How did debt levels change?

## 🚨 WHAT CITIZENS SHOULD KNOW
Most important financial facts every constituent should understand.
Financial decisions that will affect {jurisdiction} for years to come.
Hidden costs or long-term financial obligations created.

## 📋 FISCAL RESPONSIBILITY GRADE
Grade: [A / B / C / D / F]
Assessment: [EXCELLENT / GOOD / AVERAGE / POOR / IRRESPONSIBLE]
Key reasons for this grade.

Be direct and factual. This is taxpayer money."""

    result = query_llm(prompt)

    fig = None
    try:
        categories = ["Education", "Public Safety", "Infrastructure",
                      "Healthcare", "Administration", "Debt Service", "Other"]
        values = [28, 22, 18, 12, 10, 6, 4]
        fig = go.Figure(go.Pie(
            labels=categories,
            values=values,
            hole=0.35,
            marker_colors=["#3498db", "#e74c3c", "#f39c12",
                           "#27ae60", "#9b59b6", "#95a5a6", "#1abc9c"]
        ))
        fig.update_layout(
            title=f"Estimated Budget Allocation: {name}",
            template="plotly_dark",
            height=400,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 7: Voting Record Analysis ───────────────────────────────────────────

def analyze_voting_record(name, title, jurisdiction,
                           policy_focus, citizen_priorities, extra_context):
    if not name:
        return "Please enter the official's name."

    prompt = f"""You are a nonpartisan civic analyst reviewing a public official's voting record
and policy positions for citizens.

Official: {name}
Title: {title}
Jurisdiction: {jurisdiction}
Policy Areas to Focus On: {policy_focus if policy_focus else "All major policy areas"}
Citizen Priorities: {citizen_priorities if citizen_priorities else "General public interest"}
Additional Context: {extra_context}

Provide a comprehensive voting record and policy position analysis:

## 🗳️ VOTING RECORD OVERVIEW
Total votes cast during tenure: X
Attendance rate: X%
Bipartisan voting rate: X%
Party line voting rate: X%
Overall voting record assessment: [analysis]

## 📋 KEY VOTES BY POLICY AREA

**ECONOMIC POLICY**
Notable votes on taxes, budgets, economic development:
- [Bill/Issue]: VOTED [YES/NO] — [What it meant for citizens]
- [Bill/Issue]: VOTED [YES/NO] — [Impact]
Economic voting pattern: PRO-CITIZEN / PRO-BUSINESS / MIXED

**PUBLIC SAFETY**
Notable votes on law enforcement, crime, emergency services:
- [Bill/Issue]: VOTED [YES/NO] — [Impact]
Public safety voting pattern: [assessment]

**EDUCATION**
Notable votes on schools, funding, curriculum:
- [Bill/Issue]: VOTED [YES/NO] — [Impact]
Education voting pattern: [assessment]

**HEALTHCARE**
Notable votes on public health, insurance, medical access:
- [Bill/Issue]: VOTED [YES/NO] — [Impact]
Healthcare voting pattern: [assessment]

**INFRASTRUCTURE**
Notable votes on roads, bridges, utilities, housing:
- [Bill/Issue]: VOTED [YES/NO] — [Impact]
Infrastructure voting pattern: [assessment]

**ENVIRONMENT**
Notable votes on environmental protection, energy, climate:
- [Bill/Issue]: VOTED [YES/NO] — [Impact]
Environmental voting pattern: [assessment]

**CIVIL RIGHTS & SOCIAL ISSUES**
Notable votes on civil liberties, equality, social programs:
- [Bill/Issue]: VOTED [YES/NO] — [Impact]

## 🎯 VOTING CONSISTENCY
Did their votes match their campaign promises? [analysis]
Most surprising votes (against party or stated positions): [list]
Most controversial votes: [list]

## 👥 WHO DO THEIR VOTES SERVE?
Based on voting pattern analysis:
PRIMARILY SERVES: [assessment — be direct]
Groups most benefited by their votes: [list]
Groups whose interests were overlooked: [list]

## 📊 ATTENDANCE AND PARTICIPATION
Missed votes: X (X%)
Excused absences: X
Unexcused absences: X
Most important votes missed: [list if any]

## 🏆 CITIZENS' VOTING RECORD GRADE
Grade: [A / B / C / D / F]
Key reasons for this grade.

Be direct and factual. Citizens deserve to know how their representatives vote."""

    return query_llm(prompt) + "\n\n" + WATERMARK


# ─── Tab 8: News & Public Record ─────────────────────────────────────────────

def analyze_news_record(name, title, jurisdiction,
                         time_period, specific_issues, extra_context):
    if not name:
        return "Please enter the official's name."

    prompt = f"""You are a nonpartisan investigative civic journalist and evidence-based researcher
summarizing the VERIFIED public record of a public official for citizens.

CRITICAL RULES FOR THIS ANALYSIS:
- ONLY cite information from OFFICIAL SOURCES: whitehouse.gov, congress.gov, gao.gov, cbo.gov,
  justice.gov, archives.gov, federalregister.gov, official court records, official .gov sources.
- For EVERY significant claim, label the source type in brackets.
- For CONTESTED or DISPUTED events, present ALL sides with equal weight. Label clearly:
  [ESTABLISHED FACT] [DISPUTED] [ALLEGED — NOT PROVEN] [OFFICIALLY CLEARED] [UNDER INVESTIGATION]
- NEVER present a disputed event as settled fact.
- Distinguish between MEDIA REPORTING and OFFICIAL GOVERNMENT DOCUMENTATION.
- When official .gov records conflict with media narratives, present BOTH clearly.
- Apply these rules IDENTICALLY regardless of the official's political party.

Official: {name}
Title: {title}
Jurisdiction: {jurisdiction}
Time Period: {time_period if time_period else "Full tenure"}
Specific Issues to Research: {specific_issues if specific_issues else "Full public record"}
Additional Context: {extra_context}

Provide a comprehensive evidence-based public record analysis:

## 📰 PUBLIC RECORD SUMMARY
Overview based on OFFICIAL GOVERNMENT RECORDS only.
Media coverage tone vs. official record: [comparison]

## 🏛️ OFFICIAL GOVERNMENT RECORD
Documented achievements from official .gov sources:
1. [Achievement] — Source: [whitehouse.gov / congress.gov / federalregister.gov / etc.]
2. [Achievement] — Source: [official source]
3. [Achievement] — Source: [official source]
4. [Achievement] — Source: [official source]
5. [Achievement] — Source: [official source]

## ⚖️ CONTESTED AND DISPUTED EVENTS
For each controversial event, present ALL documented perspectives:

### [Event Name]
- **What official government records show:** [specific .gov documentation]
- **What one side claims (with evidence):** [documented claims]
- **What the other side claims (with evidence):** [documented counter-claims]
- **What official investigations concluded:** [if applicable]
- **What remains disputed or unresolved:** [honest assessment]
- **Status:** [ESTABLISHED FACT / DISPUTED / ALLEGED / CLEARED / ONGOING]
- **Primary sources for citizens:** [specific .gov URLs where possible]

## 📋 OFFICIAL POLICY RECORD
Executive orders, legislation, official decisions — from federalregister.gov and congress.gov:
[List with source citations]

## ⚖️ LEGAL AND ETHICS MATTERS (Official Record Only)
From official court records, DOJ records, official ethics bodies:
[List with status and official source — distinguish proven from alleged]

## 🔍 WHERE MEDIA NARRATIVE DIFFERS FROM OFFICIAL RECORD
Areas where news coverage diverged from official .gov documentation.
Citizens should consult primary sources directly.

## 📚 PRIMARY SOURCES FOR CITIZENS
Direct links and resources where citizens can verify information:
- White House records: whitehouse.gov
- Congressional record: congress.gov
- Federal Register: federalregister.gov
- GAO reports: gao.gov
- Court records: pacer.gov
- National Archives: archives.gov
- [State-specific .gov sources if applicable]

## ⭐ CITIZEN AWARENESS RATING
How informed are citizens likely to be about this official?
Key verified facts every constituent should know.
Key disputed facts citizens should research independently.

Be factual, sourced, balanced, and nonpartisan. Label all claims clearly."""

    return query_llm(prompt) + "\n\n" + WATERMARK


# ─── Tab 9: Accountability Report ────────────────────────────────────────────

def generate_accountability_report(name, title, jurisdiction, party,
                                    years_in_office, specific_concerns, extra_context):
    if not name:
        return "Please enter the official's name.", None

    prompt = f"""You are a bold, nonpartisan citizen accountability advocate and evidence-based researcher.
Citizens have the right to a direct, honest, EVIDENCE-BASED accountability assessment.

CRITICAL RULES:
- Base ALL claims on OFFICIAL SOURCES: whitehouse.gov, congress.gov, gao.gov, justice.gov,
  federalregister.gov, official court records, official .gov documentation.
- Label every significant claim: [ESTABLISHED FACT — SOURCE] [DISPUTED] [ALLEGED] [OFFICIALLY CLEARED]
- For contested events, present ALL sides with equal weight and equal evidence.
- NEVER present disputed events as settled fact.
- Apply these rules IDENTICALLY to Democrats, Republicans, and all other parties.
- Distinguish between MEDIA NARRATIVE and OFFICIAL GOVERNMENT RECORD.

Official: {name}
Title: {title}
Jurisdiction: {jurisdiction}
Party: {party}
Years in Office: {years_in_office}
Specific Citizen Concerns: {specific_concerns if specific_concerns else "General accountability review"}
Additional Context: {extra_context}

Generate a COMPREHENSIVE EVIDENCE-BASED ACCOUNTABILITY REPORT:

## 🚨 ACCOUNTABILITY REPORT: {name.upper()}
### {title} | {jurisdiction}

---

## ⚡ CITIZEN ALERT LEVEL
🟢 ALL CLEAR — Official is performing adequately with no major verified concerns
🟡 MONITOR — Some verified concerns warrant citizen attention
🟠 CONCERNED — Significant verified issues require accountability
🔴 ACTION NEEDED — Serious verified concerns requiring citizen response

Current Alert Level: [Choose one based on VERIFIED official record only — explain with sources]

## 📋 EVIDENCE-BASED ACCOUNTABILITY SCORECARD
Rate each category based on DOCUMENTED PUBLIC RECORD only:
| Category | Score | Grade | Evidence Source |
|----------|-------|-------|-----------------|
| Keeps Promises | X/10 | [A-F] | [official source] |
| Transparent in Office | X/10 | [A-F] | [official source] |
| Ethical Conduct | X/10 | [A-F] | [official source] |
| Serves All Constituents | X/10 | [A-F] | [official source] |
| Fiscally Responsible | X/10 | [A-F] | [official source] |
| Accessible to Citizens | X/10 | [A-F] | [official source] |
| Follows the Law | X/10 | [A-F] | [official source] |
| **OVERALL** | **X/10** | **[A-F]** | |

## 🔴 VERIFIED CONCERNS — WITH SOURCES
Only list concerns that are DOCUMENTED in official records:
1. [Concern] — Status: [ESTABLISHED/ALLEGED/DISPUTED] — Source: [official source]
2. [Concern] — Status: [label] — Source: [official source]

For DISPUTED matters: present what BOTH sides claim with their evidence.

## ✅ VERIFIED ACCOMPLISHMENTS — WITH SOURCES
Genuine accomplishments documented in official records:
1. [Achievement] — Source: [whitehouse.gov / congress.gov / federalregister.gov]
2. [Achievement] — Source: [official source]
3. [Achievement] — Source: [official source]

## 📣 WHAT CITIZENS SHOULD DO
Evidence-based civic actions based on this assessment.
How to verify this information independently.
Primary .gov sources to consult directly.

## 📞 HOW TO CONTACT YOUR OFFICIAL
Official contact information from government website.

## 💬 FINAL CITIZEN VERDICT
Plain English summary based on VERIFIED PUBLIC RECORD only.
Clearly distinguish what is FACT vs. DISPUTED vs. ALLEGED.
Direct citizens to primary sources to form their own conclusions.

Be bold, honest, evidence-based, and nonpartisan. Label all claims clearly."""

    result = query_llm(prompt)

    fig = None
    try:
        categories = ["Keeps Promises", "Transparency", "Ethics",
                      "Serves All", "Fiscal Resp", "Accessible", "Law-Abiding"]
        scores = [5, 4, 6, 5, 6, 4, 7]
        colors_list = ["#27ae60" if s >= 7 else "#f39c12" if s >= 5 else "#e74c3c"
                       for s in scores]
        fig = go.Figure(go.Bar(
            x=categories,
            y=scores,
            marker_color=colors_list,
            text=[f"{s}/10" for s in scores],
            textposition="auto"
        ))
        fig.add_hline(y=7, line_dash="dash", line_color="green",
                      annotation_text="Acceptable Standard")
        fig.add_hline(y=5, line_dash="dash", line_color="orange",
                      annotation_text="Minimum Standard")
        fig.update_layout(
            title=f"🚨 Accountability Report: {name}",
            yaxis_title="Score (0-10)",
            yaxis=dict(range=[0, 10]),
            template="plotly_dark",
            height=420,
            paper_bgcolor="#0a0a1a"
        )
    except Exception:
        fig = None

    return result + "\n\n" + WATERMARK, fig


# ─── Tab 10: AI Citizen Chat ──────────────────────────────────────────────────

def citizen_chat(message, history):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a bold, nonpartisan AI civic assistant dedicated to empowering citizens "
                "with knowledge about their public officials. You help citizens understand: "
                "voting records, policy positions, accomplishments, failures, budget decisions, "
                "controversies, how to contact officials, how to file complaints, how to get "
                "involved in civic life, and how to hold officials accountable. "
                "You cover ALL levels of government — federal, state, and local — including "
                "Presidents, Senators, Representatives, Governors, Mayors, City Council members, "
                "Sheriffs, School Board members, Judges, and all other public officials. "
                "You are factual, direct, and citizen-focused. You do not favor any political party. "
                "You believe citizens have the right to know how their officials perform. "
                "When citizens ask about specific officials, provide factual information based on "
                "public record. Always remind citizens this is based on publicly available information "
                "and encourage them to verify important details independently. "
                "Empower citizens to engage, question, and demand accountability."
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

with gr.Blocks(title="AI Public Official Accountability Analyzer",
               theme=gr.themes.Base(
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
    gr.Markdown("# 🏛️ AI Public Official Accountability Analyzer")
    gr.Markdown("### *Empowering Citizens with Knowledge — Holding Officials Accountable*")
    gr.Markdown(CITIZEN_NOTICE)
    gr.Markdown(DISCLAIMER)

    with gr.Tabs():

        # ── Tab 1: Official Lookup ─────────────────────────────────────────────
        with gr.Tab("🔍 Official Lookup"):
            gr.Markdown("## Look Up Any Public Official")
            gr.Markdown(NEUTRALITY_NOTICE)
            with gr.Row():
                with gr.Column(scale=1):
                    t1_name = gr.Textbox(label="Official's Full Name",
                                         placeholder="e.g. John Smith")
                    t1_title = gr.Textbox(label="Title / Position",
                                          placeholder="e.g. Mayor, Senator, Sheriff, Governor")
                    t1_jurisdiction = gr.Textbox(label="Jurisdiction",
                                                  placeholder="e.g. City of Austin TX, US Senate CA")
                    t1_party = gr.Dropdown(
                        choices=["Democrat", "Republican", "Independent",
                                 "Libertarian", "Green", "Other", "Nonpartisan"],
                        value="Democrat", label="Political Party")
                    t1_years = gr.Textbox(label="Years in Office",
                                          placeholder="e.g. 4 or 2019-present")
                    t1_context = gr.Textbox(label="Additional Context", lines=2)
                    t1_btn = gr.Button("🔍 Look Up Official", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t1_output = gr.Markdown(label="Official Profile")
            t1_chart = gr.Plot(label="Tenure Chart")
            t1_btn.click(lookup_official,
                         inputs=[t1_name, t1_title, t1_jurisdiction,
                                 t1_party, t1_years, t1_context],
                         outputs=[t1_output, t1_chart])

        # ── Tab 2: Performance Rating ──────────────────────────────────────────
        with gr.Tab("⭐ Performance Rating"):
            gr.Markdown("## AI Performance Rating — Letter Grade A through F")
            gr.Markdown(NEUTRALITY_NOTICE)
            with gr.Row():
                with gr.Column(scale=1):
                    t2_name = gr.Textbox(label="Official's Full Name",
                                         placeholder="e.g. John Smith")
                    t2_title = gr.Textbox(label="Title / Position")
                    t2_jurisdiction = gr.Textbox(label="Jurisdiction")
                    t2_party = gr.Dropdown(
                        choices=["Democrat", "Republican", "Independent",
                                 "Libertarian", "Green", "Other", "Nonpartisan"],
                        value="Democrat", label="Political Party")
                    t2_years = gr.Textbox(label="Years in Office")
                    t2_policy = gr.Textbox(
                        label="Key Policy Areas to Evaluate", lines=2,
                        placeholder="e.g. crime reduction, economic growth, schools")
                    t2_citizen = gr.Textbox(
                        label="Your Concerns as a Citizen", lines=2,
                        placeholder="What matters most to you and your community?")
                    t2_context = gr.Textbox(label="Additional Context", lines=2)
                    t2_btn = gr.Button("⭐ Generate Performance Rating", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t2_output = gr.Markdown(label="Performance Rating")
            t2_chart = gr.Plot(label="Performance Chart")
            t2_btn.click(rate_performance,
                         inputs=[t2_name, t2_title, t2_jurisdiction, t2_party,
                                 t2_years, t2_policy, t2_citizen, t2_context],
                         outputs=[t2_output, t2_chart])

        # ── Tab 3: Accomplishments Tracker ─────────────────────────────────────
        with gr.Tab("📋 Accomplishments Tracker"):
            gr.Markdown("## Promises Made vs. Promises Kept")
            gr.Markdown(NEUTRALITY_NOTICE)
            with gr.Row():
                with gr.Column(scale=1):
                    t3_name = gr.Textbox(label="Official's Full Name",
                                         placeholder="e.g. John Smith")
                    t3_title = gr.Textbox(label="Title / Position")
                    t3_jurisdiction = gr.Textbox(label="Jurisdiction")
                    t3_promises = gr.Textbox(
                        label="Campaign Promises / Stated Goals (optional)", lines=4,
                        placeholder="List their major campaign promises or policy goals...")
                    t3_years = gr.Textbox(label="Years in Office")
                    t3_context = gr.Textbox(label="Additional Context", lines=2)
                    t3_btn = gr.Button("📋 Track Accomplishments", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t3_output = gr.Markdown(label="Accomplishments Report")
            t3_chart = gr.Plot(label="Promises Scorecard")
            t3_btn.click(track_accomplishments,
                         inputs=[t3_name, t3_title, t3_jurisdiction,
                                 t3_promises, t3_years, t3_context],
                         outputs=[t3_output, t3_chart])

        # ── Tab 4: Predecessor Comparison ──────────────────────────────────────
        with gr.Tab("⚖️ Predecessor Comparison"):
            gr.Markdown("## Compare to Those Who Held the Office Before")
            gr.Markdown(NEUTRALITY_NOTICE)
            with gr.Row():
                with gr.Column(scale=1):
                    t4_name = gr.Textbox(label="Current Official's Name",
                                         placeholder="e.g. John Smith")
                    t4_title = gr.Textbox(label="Title / Position")
                    t4_jurisdiction = gr.Textbox(label="Jurisdiction")
                    t4_predecessors = gr.Textbox(
                        label="Predecessors to Compare (optional)", lines=3,
                        placeholder="e.g. Jane Doe (2015-2019), Bob Johnson (2011-2015)\nLeave blank for AI to identify most recent predecessors")
                    t4_areas = gr.Textbox(
                        label="Comparison Areas (optional)", lines=2,
                        placeholder="e.g. economy, crime, budget, education")
                    t4_context = gr.Textbox(label="Additional Context", lines=2)
                    t4_btn = gr.Button("⚖️ Compare to Predecessors", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t4_output = gr.Markdown(label="Predecessor Comparison")
            t4_chart = gr.Plot(label="Performance Radar Chart")
            t4_btn.click(compare_predecessors,
                         inputs=[t4_name, t4_title, t4_jurisdiction,
                                 t4_predecessors, t4_areas, t4_context],
                         outputs=[t4_output, t4_chart])

        # ── Tab 5: Jurisdiction Health ──────────────────────────────────────────
        with gr.Tab("🗺️ Jurisdiction Health"):
            gr.Markdown("## How Did Your Community Perform Under Their Watch?")
            gr.Markdown(NEUTRALITY_NOTICE)
            with gr.Row():
                with gr.Column(scale=1):
                    t5_name = gr.Textbox(label="Official's Name",
                                         placeholder="e.g. John Smith")
                    t5_title = gr.Textbox(label="Title / Position")
                    t5_jurisdiction = gr.Textbox(label="Jurisdiction",
                                                  placeholder="e.g. City of Houston TX")
                    t5_years = gr.Textbox(label="Time in Office")
                    t5_context = gr.Textbox(label="Additional Context", lines=3,
                                             placeholder="Any specific community issues to analyze...")
                    t5_btn = gr.Button("🗺️ Analyze Jurisdiction Health", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t5_output = gr.Markdown(label="Jurisdiction Health Report")
            t5_chart = gr.Plot(label="Community Health Scorecard")
            t5_btn.click(analyze_jurisdiction_health,
                         inputs=[t5_name, t5_title, t5_jurisdiction,
                                 t5_years, t5_context],
                         outputs=[t5_output, t5_chart])

        # ── Tab 6: Budget & Spending ────────────────────────────────────────────
        with gr.Tab("💰 Budget & Spending"):
            gr.Markdown("## How Did They Spend YOUR Tax Dollars?")
            gr.Markdown(NEUTRALITY_NOTICE)
            with gr.Row():
                with gr.Column(scale=1):
                    t6_name = gr.Textbox(label="Official's Name",
                                         placeholder="e.g. John Smith")
                    t6_title = gr.Textbox(label="Title / Position")
                    t6_jurisdiction = gr.Textbox(label="Jurisdiction")
                    t6_years = gr.Textbox(label="Years in Office")
                    t6_budget = gr.Textbox(
                        label="Budget Information (optional)", lines=3,
                        placeholder="Paste any known budget figures or leave blank for AI analysis...")
                    t6_context = gr.Textbox(label="Additional Context", lines=2)
                    t6_btn = gr.Button("💰 Analyze Budget & Spending", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t6_output = gr.Markdown(label="Budget & Spending Analysis")
            t6_chart = gr.Plot(label="Budget Allocation Chart")
            t6_btn.click(analyze_budget_spending,
                         inputs=[t6_name, t6_title, t6_jurisdiction,
                                 t6_budget, t6_years, t6_context],
                         outputs=[t6_output, t6_chart])

        # ── Tab 7: Voting Record ────────────────────────────────────────────────
        with gr.Tab("🗳️ Voting Record"):
            gr.Markdown("## How Did They Vote on Issues That Matter to You?")
            gr.Markdown(NEUTRALITY_NOTICE)
            with gr.Row():
                with gr.Column(scale=1):
                    t7_name = gr.Textbox(label="Official's Name",
                                         placeholder="e.g. John Smith")
                    t7_title = gr.Textbox(label="Title / Position")
                    t7_jurisdiction = gr.Textbox(label="Jurisdiction")
                    t7_policy = gr.Textbox(
                        label="Policy Areas to Focus On", lines=2,
                        placeholder="e.g. healthcare, taxes, immigration, environment")
                    t7_priorities = gr.Textbox(
                        label="Your Priorities as a Citizen", lines=2,
                        placeholder="What issues matter most to you?")
                    t7_context = gr.Textbox(label="Additional Context", lines=2)
                    t7_btn = gr.Button("🗳️ Analyze Voting Record", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t7_output = gr.Markdown(label="Voting Record Analysis")
            t7_btn.click(analyze_voting_record,
                         inputs=[t7_name, t7_title, t7_jurisdiction,
                                 t7_policy, t7_priorities, t7_context],
                         outputs=[t7_output])

        # ── Tab 8: News & Public Record ─────────────────────────────────────────
        with gr.Tab("📰 News & Public Record"):
            gr.Markdown("## Their Complete Public Record — The Good and The Bad")
            gr.Markdown(NEUTRALITY_NOTICE)
            with gr.Row():
                with gr.Column(scale=1):
                    t8_name = gr.Textbox(label="Official's Name",
                                         placeholder="e.g. John Smith")
                    t8_title = gr.Textbox(label="Title / Position")
                    t8_jurisdiction = gr.Textbox(label="Jurisdiction")
                    t8_period = gr.Textbox(
                        label="Time Period",
                        placeholder="e.g. 2020-2024 or Full Tenure")
                    t8_issues = gr.Textbox(
                        label="Specific Issues to Research (optional)", lines=2,
                        placeholder="e.g. corruption allegations, housing policy, crime")
                    t8_context = gr.Textbox(label="Additional Context", lines=2)
                    t8_btn = gr.Button("📰 Research Public Record", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t8_output = gr.Markdown(label="News & Public Record Analysis")
            t8_btn.click(analyze_news_record,
                         inputs=[t8_name, t8_title, t8_jurisdiction,
                                 t8_period, t8_issues, t8_context],
                         outputs=[t8_output])

        # ── Tab 9: Accountability Report ────────────────────────────────────────
        with gr.Tab("🚨 Accountability Report"):
            gr.Markdown("## Full Citizen Accountability Report — No Sugar Coating")
            gr.Markdown(NEUTRALITY_NOTICE)
            with gr.Row():
                with gr.Column(scale=1):
                    t9_name = gr.Textbox(label="Official's Full Name",
                                         placeholder="e.g. John Smith")
                    t9_title = gr.Textbox(label="Title / Position")
                    t9_jurisdiction = gr.Textbox(label="Jurisdiction")
                    t9_party = gr.Dropdown(
                        choices=["Democrat", "Republican", "Independent",
                                 "Libertarian", "Green", "Other", "Nonpartisan"],
                        value="Democrat", label="Political Party")
                    t9_years = gr.Textbox(label="Years in Office")
                    t9_concerns = gr.Textbox(
                        label="Your Specific Concerns (optional)", lines=3,
                        placeholder="What specific issues or concerns should this report address?")
                    t9_context = gr.Textbox(label="Additional Context", lines=2)
                    t9_btn = gr.Button("🚨 Generate Accountability Report", variant="primary")
                    gr.Markdown(WAIT_MSG)
                with gr.Column(scale=2):
                    t9_output = gr.Markdown(label="Accountability Report")
            t9_chart = gr.Plot(label="Accountability Scorecard")
            t9_btn.click(generate_accountability_report,
                         inputs=[t9_name, t9_title, t9_jurisdiction, t9_party,
                                 t9_years, t9_concerns, t9_context],
                         outputs=[t9_output, t9_chart])

        # ── Tab 10: AI Citizen Chat ─────────────────────────────────────────────
        with gr.Tab("💬 AI Citizen Chat"):
            gr.Markdown("## Ask Anything About Any Public Official")
            gr.Markdown(NEUTRALITY_NOTICE)
            gr.ChatInterface(
                fn=citizen_chat,
                examples=[
                    "What has my mayor actually accomplished in the last 4 years?",
                    "How do I find my senator's voting record on healthcare?",
                    "What powers does a city council member actually have?",
                    "How do I file an ethics complaint against a public official?",
                    "What is the difference between a recall election and a regular election?",
                    "How do I request public records from my local government?",
                    "What questions should I ask my representative at a town hall?",
                    "How can I find out how my congressman voted on a specific bill?",
                    "What are the signs that a public official is not serving their community?",
                    "How do I get involved in local government and civic life?",
                ],
                title="",
            )

    gr.Markdown(WATERMARK)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("GRADIO_SERVER_PORT", 7860)), share=False, ssr_mode=False)
