# Company Intelligence Dashboard - Complete Implementation Plan

## Project Overview
A comprehensive, beautiful HTML report generator that pulls ALL possible public data about a company from a stock ticker symbol. The report is generated on-demand via a Discord bot command and returns a single, standalone HTML file containing embedded data, charts, graphs, and images.

---

## User Flow
1. User types a command in Discord: `/company-dashboard`
2. Discord bot creates/opens a web dashboard interface
3. User enters a ticker symbol (e.g., "AAPL") in the dashboard
4. Dashboard triggers Python backend script with the ticker
5. Python script scrapes/fetches all public data in real-time
6. Python script generates a single HTML file with all data embedded
7. Dashboard displays download link or automatically downloads the HTML report
8. User opens the HTML file in their browser to view the complete report

---

## Technical Architecture

### Data Collection (Python Backend)
- **All data must be embedded directly in the HTML file** as JavaScript variables/objects
- This creates a single, portable HTML file that works offline
- All images (logos, product photos, executive headshots) should be **base64-encoded** and embedded
- The script should pull **live data** every time it runs (no stale data)
- If ANY critical data source fails, the script should **fail completely** and notify the Discord user with an error message
- Optional: Use a database to cache non-time-sensitive data (company descriptions, historical events) to speed up generation, but always pull financial/price data live

### HTML Structure
- **One massive scrolling page** with all sections
- Fixed sidebar navigation with jump links to each section
- Sticky header with company name, logo, and ticker
- All CSS, JavaScript, and data embedded in the single HTML file
- Mobile-responsive design

### Visual Style: Dark Mode Professional
- Background: Dark navy/charcoal (#1a1d29, #0f1117)
- Accent colors: Electric blue (#3b82f6), cyan (#06b6d4), purple (#8b5cf6)
- Text: White/light gray for readability
- Charts: Dark backgrounds with bright, contrasting colors
- Cards/sections: Subtle borders, slight elevation/shadows
- Clean, modern typography (Inter, Segoe UI, or system fonts)

### Chart Library
- **Chart.js** for all charts and graphs
- Use the dark theme palette
- Enable tooltips and hover interactions
- Consistent styling across all charts

---

## Data Sources & Scraping Strategy

### 1. FREE APIs (No Key Required)
- **Yahoo Finance (via yfinance Python library)**: Stock prices, historical data, basic financials
- **Alpha Vantage FREE tier**: Additional financial data (limit: 5 calls/minute, 500/day)
- **SEC EDGAR API**: Official SEC filings (10-K, 10-Q, 8-K, proxy statements)
- **OpenFIGI API**: Company identifiers and metadata
- **Polygon.io FREE tier**: Market data (limit: 5 calls/minute)

### 2. Public Websites to Scrape (No API)
⚠️ **LEGAL NOTICE**: Respect robots.txt and rate limits. Some sites prohibit scraping in their ToS.

- **Wikipedia**: Company history, founding info, headquarters
- **Crunchbase (public pages)**: Funding rounds, investors (note: aggressive anti-bot measures)
- **Google Finance**: Basic company info
- **Reuters/Bloomberg free pages**: News articles
- **Glassdoor (public reviews)**: Employee sentiment (⚠️ ToS prohibits scraping)
- **LinkedIn (public company pages)**: Employee count estimate (⚠️ ToS strictly prohibits scraping - high risk)
- **USPTO Patent Database**: Patent filings
- **Google Custom Search API (free tier)**: Product images, news (limit: 100 queries/day)
- **Company's official website**: About page, product catalog, press releases
- **Twitter/X API (free tier)**: Social media presence (requires account)
- **Reddit mentions**: Community sentiment (via PRAW library)

### 3. Calculated/Derived Data
- Financial ratios (P/E, debt-to-equity, ROE, etc.)
- Sentiment scores from news headlines
- Growth rates and trends
- Competitor comparisons

---

## Complete Section Breakdown

### HEADER (Sticky)
- Company logo (base64 embedded)
- Company name + ticker symbol
- Current stock price + % change (color-coded: green/red)
- Last updated timestamp
- Quick stats bar: Market Cap | P/E Ratio | 52-Week Range

### SIDEBAR NAVIGATION (Fixed)
Collapsible table of contents with smooth scroll:
1. Executive Summary
2. Company Overview
3. Stock Performance
4. Financial Statements
5. Financial Ratios & Metrics
6. Products & Services
7. Leadership & Management
8. Employees & Culture
9. News & Sentiment
10. Competitors & Market Position
11. Risk Assessment
12. SEC Filings & Legal
13. Patents & Intellectual Property
14. Social Media & Public Presence
15. ESG & Sustainability
16. Historical Timeline
17. Raw Data Dump

---

## Section 1: Executive Summary
**Purpose**: AI-generated 3-5 paragraph overview of the company

**Content**:
- One-sentence company description
- Key strengths and competitive advantages
- Recent notable developments (last 6 months)
- Major risks or red flags identified
- Investment thesis summary (if applicable)

**Visual Elements**:
- Large hero card with gradient background
- Key metrics displayed as stat cards (4-6 metrics)

**Data Sources**:
- Aggregated from all other sections
- Can use GPT/Claude API to generate summary (if available) or template-based generation

---

## Section 2: Company Overview

### 2.1 Basic Information
**Data Points**:
- Official company name
- Ticker symbol + exchange
- Industry / Sector / Sub-sector
- Founded date
- Headquarters location (with map embed if possible)
- Website URL
- Phone number
- Number of employees (with trend chart if historical data available)
- Fiscal year end

**Visual Elements**:
- Two-column layout with info cards
- Small embedded map showing headquarters location
- Company logo prominently displayed

**Data Sources**:
- Yahoo Finance API
- Company website scraping
- SEC filings (10-K)
- Wikipedia

### 2.2 Company Description
**Content**:
- Official business description (from 10-K)
- Mission statement (if available)
- Core business model
- Target markets and customers

**Data Sources**:
- SEC 10-K filing (Business section)
- Company website (About page)

### 2.3 Corporate Structure
**Content**:
- Parent company (if subsidiary)
- Major subsidiaries and brands
- Organizational chart (if data available)

**Visual Elements**:
- Tree diagram or hierarchical list

**Data Sources**:
- SEC filings
- Company website

---

## Section 3: Stock Performance

### 3.1 Current Price Data
**Data Points**:
- Current price
- Day's range (high/low)
- 52-week range (high/low)
- Volume
- Average volume (10-day, 30-day)
- Market cap
- Shares outstanding
- Float

**Visual Elements**:
- Large price card with color-coded change
- Horizontal bar showing current price within 52-week range

**Data Sources**:
- Yahoo Finance (yfinance)
- Alpha Vantage

### 3.2 Price Charts
**Charts to Include**:
1. **Candlestick Chart** (1-year daily): Shows OHLC data
2. **Line Chart** (5-year weekly): Long-term trend
3. **Volume Chart** (1-year): Bar chart of trading volume
4. **Intraday Chart** (if market is open): 1-day, 5-minute intervals

**Visual Elements**:
- Interactive Chart.js charts
- Toggle buttons to switch timeframes
- Moving averages overlaid (50-day, 200-day)

**Data Sources**:
- Yahoo Finance (yfinance)
- Alpha Vantage (for intraday)

### 3.3 Dividend Information
**Data Points** (if applicable):
- Dividend yield
- Annual dividend per share
- Payout ratio
- Ex-dividend date
- Payment date
- Dividend history (5-year table)
- Dividend growth rate

**Visual Elements**:
- Line chart showing dividend per share over time
- Table of dividend payments

**Data Sources**:
- Yahoo Finance
- SEC filings

### 3.4 Stock Splits
**Content**:
- Table of historical stock splits (if any)
- Split ratio, date, adjusted price

**Data Sources**:
- Yahoo Finance

---

## Section 4: Financial Statements

### 4.1 Income Statement
**Time Periods**: Last 5 years (annual) + last 4 quarters

**Line Items**:
- Revenue (Total Revenue / Net Sales)
- Cost of Goods Sold (COGS)
- Gross Profit
- Operating Expenses (breakdown: R&D, SG&A, etc.)
- Operating Income (EBIT)
- Interest Expense
- Pre-Tax Income
- Income Tax Expense
- Net Income
- Earnings Per Share (EPS) - Basic and Diluted

**Visual Elements**:
- Large table with expandable rows
- Revenue & Net Income bar chart (5-year trend)
- Gross Margin trend line chart

**Data Sources**:
- SEC EDGAR (10-K, 10-Q)
- Yahoo Finance
- Alpha Vantage

### 4.2 Balance Sheet
**Time Periods**: Last 5 years (annual) + last 4 quarters

**Line Items**:
- **Assets**:
  - Current Assets (Cash, Marketable Securities, Accounts Receivable, Inventory)
  - Non-Current Assets (PP&E, Intangibles, Goodwill)
  - Total Assets
- **Liabilities**:
  - Current Liabilities (Accounts Payable, Short-term Debt)
  - Non-Current Liabilities (Long-term Debt, Deferred Taxes)
  - Total Liabilities
- **Shareholders' Equity**:
  - Common Stock
  - Retained Earnings
  - Total Equity

**Visual Elements**:
- Stacked bar chart: Assets vs. Liabilities + Equity
- Pie chart: Asset composition
- Table with expandable sections

**Data Sources**:
- SEC EDGAR (10-K, 10-Q)
- Yahoo Finance

### 4.3 Cash Flow Statement
**Time Periods**: Last 5 years (annual) + last 4 quarters

**Line Items**:
- **Operating Activities**:
  - Net Income
  - Depreciation & Amortization
  - Changes in Working Capital
  - Cash from Operations
- **Investing Activities**:
  - CapEx (Capital Expenditures)
  - Acquisitions
  - Cash from Investing
- **Financing Activities**:
  - Dividends Paid
  - Stock Buybacks
  - Debt Issuance/Repayment
  - Cash from Financing
- **Net change in Cash**

**Visual Elements**:
- Waterfall chart showing cash flow sources and uses
- Line chart: Free Cash Flow trend (Operating Cash Flow - CapEx)
- Table with all line items

**Data Sources**:
- SEC EDGAR (10-K, 10-Q)
- Yahoo Finance

---

## Section 5: Financial Ratios & Metrics

### 5.1 Valuation Ratios
**Metrics**:
- P/E Ratio (Price-to-Earnings)
- Forward P/E
- PEG Ratio (P/E to Growth)
- P/B Ratio (Price-to-Book)
- P/S Ratio (Price-to-Sales)
- EV/EBITDA (Enterprise Value to EBITDA)
- Enterprise Value

**Visual Elements**:
- Comparison bar chart vs. industry average (if available)
- Table with current value + 5-year average

**Data Sources**:
- Yahoo Finance
- Calculated from financial statements

### 5.2 Profitability Ratios
**Metrics**:
- Gross Margin (%)
- Operating Margin (%)
- Net Profit Margin (%)
- Return on Assets (ROA)
- Return on Equity (ROE)
- Return on Invested Capital (ROIC)

**Visual Elements**:
- Line chart showing margin trends over 5 years
- Gauge charts for ROA, ROE, ROIC

**Data Sources**:
- Calculated from financial statements

### 5.3 Liquidity Ratios
**Metrics**:
- Current Ratio
- Quick Ratio (Acid Test)
- Cash Ratio
- Operating Cash Flow Ratio

**Visual Elements**:
- Bar chart comparing ratios over time
- Health indicator (green/yellow/red based on thresholds)

**Data Sources**:
- Calculated from balance sheet and cash flow statement

### 5.4 Leverage Ratios
**Metrics**:
- Debt-to-Equity Ratio
- Debt-to-Assets Ratio
- Interest Coverage Ratio
- Long-term Debt to Capitalization

**Visual Elements**:
- Stacked bar chart: Debt vs. Equity over time
- Line chart: Interest coverage trend

**Data Sources**:
- Calculated from financial statements

### 5.5 Efficiency Ratios
**Metrics**:
- Asset Turnover Ratio
- Inventory Turnover Ratio
- Receivables Turnover Ratio
- Days Sales Outstanding (DSO)
- Days Inventory Outstanding (DIO)
- Days Payable Outstanding (DPO)
- Cash Conversion Cycle

**Visual Elements**:
- Bar charts for turnover ratios
- Line chart: Cash conversion cycle trend

**Data Sources**:
- Calculated from financial statements

### 5.6 Growth Metrics
**Metrics**:
- Revenue Growth (YoY, 3-year CAGR, 5-year CAGR)
- Earnings Growth (YoY, 3-year CAGR, 5-year CAGR)
- Book Value Growth
- Free Cash Flow Growth

**Visual Elements**:
- Bar chart: Year-over-year growth rates
- Line chart: Cumulative growth

**Data Sources**:
- Calculated from financial statements

---

## Section 6: Products & Services

### 6.1 Product Catalog
**Content**:
- List of major products/services
- Product categories or business segments
- Revenue breakdown by product line (if available in 10-K)
- Key brands owned by the company

**Visual Elements**:
- Product images embedded (scraped from company website)
- Cards for each major product
- Pie chart: Revenue by segment

**Data Sources**:
- SEC 10-K (Business Segments section)
- Company website (Products page)
- Google Images (via Custom Search API)

### 6.2 Geographic Revenue Breakdown
**Content**:
- Revenue by geographic region (if disclosed)
- Countries where company operates
- International vs. domestic revenue %

**Visual Elements**:
- World map with regions highlighted and sized by revenue
- Pie chart: Revenue by region

**Data Sources**:
- SEC 10-K (Geographic Data section)

---

## Section 7: Leadership & Management

### 7.1 Executive Team
**Data Points** (for each executive):
- Name
- Title/Position
- Photo (if available)
- Age (if available)
- Compensation (from proxy statement)
- Background/bio (brief)

**Executives to Include**:
- CEO
- CFO
- COO
- CTO/CIO
- Division Presidents
- Other C-suite

**Visual Elements**:
- Executive cards with photos (base64 embedded)
- Table of executive compensation
- Bar chart: Compensation comparison

**Data Sources**:
- SEC DEF 14A Proxy Statement
- Company website (Leadership page)
- LinkedIn (⚠️ ToS violation risk)

### 7.2 Board of Directors
**Data Points** (for each director):
- Name
- Role (Independent, Chairman, etc.)
- Photo (if available)
- Other board memberships
- Compensation

**Visual Elements**:
- Board member cards
- Table listing all directors

**Data Sources**:
- SEC DEF 14A Proxy Statement
- Company website

### 7.3 Insider Trading Activity
**Content**:
- Recent insider purchases and sales (last 12 months)
- Form 4 filings (all transactions)
- Individual transactions: Name, Title, Transaction Type, Date, Shares, Price, Value
- Aggregated insider sentiment (net buying vs. selling)
- Largest transactions highlighted
- Percentage of shares owned by insiders

**Visual Elements**:
- Detailed table of insider transactions (sortable)
- Bar chart: Insider buying vs. selling by month
- Pie chart: Insider ownership vs. public float
- Timeline chart: Transaction activity over time

**Data Sources**:
- SEC EDGAR (Form 4 filings)
- Free sites like OpenInsider (scrape carefully)
- Yahoo Finance

### 7.4 Congressional Trading Activity (STOCK Act Filings)
**Content**:
- All Congressional stock transactions for this company (last 24 months)
- Senator/Representative name, party, state
- Transaction date, type (purchase/sale), amount range
- Filing date (track delays in reporting)
- Committee assignments (relevant to company's industry)
- Aggregated data: Which party trades this stock more, timing of trades vs. major events

**Visual Elements**:
- Detailed table of congressional transactions
- Bar chart: Purchases vs. sales by month
- Scatter plot: Transaction timing vs. stock price movements
- Heatmap: Trading activity by politician
- Timeline: Congressional trades plotted against major company announcements

**Data Sources**:
- House Financial Disclosure Reports: https://disclosures-clerk.house.gov/
- Senate Financial Disclosure Reports: https://efdsearch.senate.gov/
- Free APIs/scrapers: Capitol Trades, Quiver Quantitative (check if free tier available)
- SEC EDGAR (some congress members file there)

**⚠️ Important Notes**:
- STOCK Act requires disclosure within 45 days of transaction
- Transactions are reported in ranges ($1,001-$15,000, $15,001-$50,000, etc.)
- Parse PDF reports if necessary

### 7.5 Institutional Ownership
**Content**:
- Top institutional holders
- % of shares held by institutions
- Recent changes in institutional holdings

**Visual Elements**:
- Table of top 10 institutional holders
- Pie chart: Institutional vs. retail ownership

**Data Sources**:
- SEC 13F filings
- Yahoo Finance

---

## Section 8: Employees & Culture

### 8.1 Employee Statistics
**Data Points**:
- Total number of employees
- Employee growth rate
- Turnover rate (if available)
- Average tenure (if available)
- Employee demographics (if disclosed)

**Visual Elements**:
- Line chart: Employee count over time
- Bar chart: Employees by department/division (if available)

**Data Sources**:
- SEC 10-K
- Company website (Careers page)
- Glassdoor (⚠️ ToS risk)

### 8.2 Glassdoor Data (⚠️ HIGH LEGAL RISK)
**Warning**: Glassdoor explicitly prohibits scraping in their ToS. Proceed with extreme caution or skip this section.

**Data Points** (if you choose to scrape):
- Overall rating (out of 5)
- CEO approval rating
- Recommend to a friend %
- Culture & values rating
- Work/life balance rating
- Recent reviews (sample 5-10)

**Visual Elements**:
- Star rating display
- Bar chart: Rating breakdown by category
- Word cloud of common review terms

**Alternative**: Manually collect this data or use a paid API (e.g., Glassdoor API if available to you).

### 8.3 Company Culture
**Content**:
- Mission and values statement
- Diversity initiatives (if disclosed)
- Employee benefits highlights
- Awards and recognitions (e.g., "Best Places to Work")

**Data Sources**:
- Company website (Careers, About pages)
- Press releases
- ESG reports

---

## Section 9: News & Sentiment

### 9.1 Recent News Articles
**Content**:
- Last 30-60 days of news headlines
- Article title, source, date, brief excerpt
- Link to full article

**Visual Elements**:
- Scrollable news feed
- Timeline view with articles plotted by date

**Data Sources**:
- Google News (via Custom Search API or RSS)
- Company press releases page
- Reuters, Bloomberg free articles (scrape headlines)

### 9.2 Sentiment Analysis
**Content**:
- Aggregate sentiment score (positive/negative/neutral %)
- Sentiment trend over time (last 6 months)
- Word cloud of common terms in news

**Visual Elements**:
- Gauge chart: Overall sentiment score
- Line chart: Sentiment trend over time
- Word cloud

**Data Sources**:
- News headlines (analyzed with simple NLP: positive/negative keywords)
- Python libraries: TextBlob, VADER, or transformers (for sentiment analysis)

### 9.3 Earnings Call Transcripts
**Content**:
- Link to most recent earnings call transcript
- Key quotes or highlights
- Management guidance (if mentioned)

**Data Sources**:
- SEC 8-K filings (sometimes include transcripts)
- Company investor relations page
- Free transcript sites (e.g., Seeking Alpha - ⚠️ check ToS)

---

## Section 10: Competitors & Market Position

### 10.1 Identified Competitors
**Content**:
- List of 5-10 direct competitors
- Brief description of each competitor

**Data Sources**:
- SEC 10-K (Competition section)
- Yahoo Finance (Competitors tab)
- Company website

### 10.2 Competitive Metrics Comparison
**Metrics to Compare**:
- Market Cap
- Revenue
- Net Income
- P/E Ratio
- Profit Margin
- Revenue Growth Rate

**Visual Elements**:
- Comparison table (target company vs. top 3-5 competitors)
- Grouped bar chart: Key metrics side-by-side
- Spider/radar chart: Multi-metric comparison

**Data Sources**:
- Yahoo Finance
- SEC filings for each competitor

### 10.3 Market Share Analysis
**Content**:
- Industry market share (if available)
- Target company's position in the industry

**Visual Elements**:
- Pie chart: Market share by company

**Data Sources**:
- Industry reports (may need to scrape research firm summaries)
- Company presentations (investor relations)

---

## Section 11: Risk Assessment

### 11.1 Risk Factors
**Content**:
- Extract "Risk Factors" section from 10-K
- Categorize risks: Financial, Operational, Regulatory, Market, Competitive, etc.
- Highlight any new risks added in recent filings

**Visual Elements**:
- Categorized list with expandable details
- Tag cloud of risk keywords

**Data Sources**:
- SEC 10-K (Item 1A: Risk Factors)

### 11.2 Red Flags Identified
**Content**:
- AI/rule-based detection of potential red flags:
  - Declining revenue or margins
  - Increasing debt-to-equity ratio
  - Negative free cash flow
  - High executive turnover
  - Insider selling spikes
  - Lawsuits or regulatory actions
  - Going concern warnings

**Visual Elements**:
- Alert cards for each identified red flag (color-coded by severity)
- Dashboard-style summary: "X red flags identified"

**Data Sources**:
- Calculated from financial data
- SEC filings (lawsuits, going concern statements)
- News articles

### 11.3 Audit Information
**Content**:
- Current auditor name
- Auditor opinion (unqualified, qualified, adverse)
- Auditor tenure (years with company)
- Any restatements or accounting issues

**Data Sources**:
- SEC 10-K (Auditor's Report section)

### 11.4 Legal Proceedings
**Content**:
- Ongoing lawsuits (from 10-K, 10-Q)
- Regulatory investigations
- Patent disputes
- Environmental violations

**Data Sources**:
- SEC 10-K (Item 3: Legal Proceedings)
- SEC 8-K filings
- PACER (Public Access to Court Electronic Records) - may require account

---

## Section 12: SEC Filings & Legal

### 12.1 Recent SEC Filings
**Content**:
- Last 50 filings (10-K, 10-Q, 8-K, S-1, DEF 14A, etc.)
- Filing type, date, description, link to full document

**Visual Elements**:
- Searchable/filterable table
- Timeline view showing filing frequency

**Data Sources**:
- SEC EDGAR API: https://www.sec.gov/edgar/sec-api-documentation
- Direct link format: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=XXXXX

### 12.2 10-K Highlights
**Content**:
- Extract and display key sections from most recent 10-K:
  - Business Description
  - Risk Factors (top 10)
  - Management's Discussion & Analysis (MD&A)
  - Selected Financial Data

**Data Sources**:
- SEC EDGAR (10-K filing)

### 12.3 Material Events (8-K Filings)
**Content**:
- Last 12 months of 8-K filings
- Type of event (earnings release, acquisition, leadership change, etc.)
- Date and brief description

**Visual Elements**:
- Timeline of material events

**Data Sources**:
- SEC EDGAR (8-K filings)

### 12.4 Proxy Statement Highlights
**Content**:
- Shareholder proposals
- Voting results from last annual meeting
- Executive compensation details
- Related-party transactions

**Data Sources**:
- SEC EDGAR (DEF 14A)

---

## Section 13: Patents & Intellectual Property

### 13.1 Patent Portfolio
**Content**:
- Total number of patents held
- Recent patents filed (last 5 years)
- Patent titles and abstracts
- Patent status (active, pending, expired)
- Key technology areas

**Visual Elements**:
- Bar chart: Patents by year
- Pie chart: Patents by technology category
- Table of recent patents

**Data Sources**:
- USPTO Patent Database: https://www.uspto.gov/
- Google Patents (free to scrape)
- European Patent Office (EPO) for international patents

### 13.2 Trademark Information
**Content**:
- Active trademarks
- Trademark names and registration numbers
- Status (registered, pending)

**Data Sources**:
- USPTO Trademark Database: https://www.uspto.gov/trademarks

### 13.3 IP Legal Disputes
**Content**:
- Patent infringement lawsuits (as plaintiff or defendant)
- Trademark disputes
- Trade secret litigation

**Data Sources**:
- SEC filings
- PACER court records
- News articles

---

## Section 14: Social Media & Public Presence

### 14.1 Social Media Metrics
**Platforms to Track**:
- Twitter/X: Handle, followers, engagement rate, recent tweets
- LinkedIn: Company page followers, employee count
- Facebook: Page likes, followers
- Instagram: Followers, engagement
- YouTube: Subscribers, video views
- TikTok: Followers (if applicable)

**Content for Each Platform**:
- Handle/username
- Follower count
- Recent posts (embed 5-10 latest posts if possible)
- Engagement metrics (likes, shares, comments)
- Growth rate

**Visual Elements**:
- Social media cards with logos
- Follower count comparison bar chart
- Engagement rate line chart over time

**Data Sources**:
- Twitter API (free tier available with account): https://developer.twitter.com/
- LinkedIn public company pages (scrape carefully, ⚠️ ToS risk)
- Facebook Graph API (may require app registration)
- Instagram (difficult to scrape, may need unofficial APIs)
- YouTube Data API: https://developers.google.com/youtube/v3
- Scrape public profiles directly (respect rate limits)

### 14.2 Website Analytics (Public Estimates)
**Content**:
- Estimated monthly traffic
- Traffic sources (direct, search, social, referral)
- Top referring sites
- Geographic traffic distribution

**Visual Elements**:
- Line chart: Traffic trend
- Pie chart: Traffic sources

**Data Sources**:
- SimilarWeb (limited free data available)
- Alexa rank (discontinued, but may find cached data)
- Scrape public rankings from various sources

### 14.3 Media Mentions & Press Coverage
**Content**:
- Count of media mentions over time
- Top publications covering the company
- Sentiment of coverage (positive/negative/neutral)

**Visual Elements**:
- Bar chart: Mentions by month
- Word cloud: Common topics in coverage

**Data Sources**:
- Google News search results
- Company press releases page

### 14.4 Customer Reviews & Ratings
**Content**:
- Product reviews from major platforms (Amazon, Best Buy, etc.)
- Average ratings
- Common complaints and praise

**Visual Elements**:
- Star ratings display
- Word cloud of review terms

**Data Sources**:
- Amazon product pages (scrape carefully)
- Best Buy, Walmart, Target (if applicable)
- App Store / Google Play (for software companies)
- Yelp, Google Reviews (for B2C companies)

---

## Section 15: ESG & Sustainability

### 15.1 ESG Scores & Ratings
**Content**:
- ESG score (if available from free sources)
- Environmental score
- Social score
- Governance score
- Comparison to industry peers

**Visual Elements**:
- Gauge charts for each ESG component
- Bar chart: Company vs. industry average

**Data Sources**:
- Yahoo Finance (sometimes includes ESG data)
- Company sustainability reports
- Free ESG rating sites (MSCI, Sustainalytics - may have limited free data)

### 15.2 Carbon Footprint & Environmental Impact
**Content**:
- Carbon emissions (Scope 1, 2, 3 if disclosed)
- Renewable energy usage %
- Waste reduction initiatives
- Water usage
- Environmental certifications

**Visual Elements**:
- Bar chart: Emissions over time
- Pie chart: Energy sources

**Data Sources**:
- Company sustainability/CSR reports
- CDP (Carbon Disclosure Project) - some data is public
- EPA enforcement database (for violations)

### 15.3 Social Initiatives
**Content**:
- Diversity & inclusion metrics (if disclosed)
- Community programs
- Charitable giving
- Employee welfare programs

**Data Sources**:
- Company ESG reports
- Press releases

### 15.4 Governance Practices
**Content**:
- Board independence (% independent directors)
- Board diversity
- Executive compensation structure
- Shareholder rights
- Anti-corruption policies

**Data Sources**:
- SEC DEF 14A Proxy Statement
- Company governance documents

### 15.5 Controversies & Scandals
**Content**:
- Environmental violations
- Labor disputes
- Data breaches
- Discrimination lawsuits
- Regulatory fines

**Visual Elements**:
- Timeline of controversies

**Data Sources**:
- News articles
- SEC filings
- EPA/OSHA databases
- Court records

---

## Section 16: Historical Timeline

### 16.1 Company Milestones
**Content**:
- Founding date and story
- IPO date and initial price
- Major acquisitions and mergers
- Product launches
- Expansion into new markets
- Leadership changes (CEO transitions)
- Bankruptcy/restructuring (if applicable)
- Stock splits and major corporate actions

**Visual Elements**:
- Interactive vertical timeline
- Icons for different event types
- Images for major milestones (if available)

**Data Sources**:
- Wikipedia (company history section)
- Company website (About/History page)
- SEC filings (8-K for material events)
- News archives

### 16.2 Stock Price Historical Context
**Content**:
- All-time high and low with dates
- Major price movements and their causes
- Correlation with broader market events

**Visual Elements**:
- Annotated line chart showing price history with event markers

**Data Sources**:
- Yahoo Finance
- Historical news

---

## Section 17: Raw Data Dump

### 17.1 Complete Data Export
**Content**:
- Every single data point collected, displayed in tables
- Allows power users to do their own analysis
- Organized by data source

**Visual Elements**:
- Collapsible/expandable sections
- Searchable tables
- Export to CSV buttons (JavaScript-based)

**Data Sources**:
- All collected data

**Format**:
```
FINANCIAL DATA
- Income Statement (5 years, 4 quarters)
- Balance Sheet (5 years, 4 quarters)
- Cash Flow Statement (5 years, 4 quarters)

STOCK DATA
- Historical prices (5 years daily)
- Volume data

INSIDER TRADING
- All Form 4 transactions (12 months)

[etc. for every data category]
```

---

## Implementation Status

### Completed Sections ✅
- [x] Basic HTML structure
- [x] Dark mode styling
- [x] Chart.js integration
- [x] Yahoo Finance data (prices, basic info)
- [x] Congress trading data
- [x] Insider trading data
- [x] Database integration

### In Progress 🔄
- [ ] Comprehensive data fetcher (19 data categories)
- [ ] Financial statements display
- [ ] SEC EDGAR filings integration

### Not Started ⏳
- [ ] Executive team photos
- [ ] Patent database integration
- [ ] Social media metrics
- [ ] ESG data
- [ ] Historical timeline
- [ ] Raw data export

---

## Notes

This HTMLTODO.md serves as the master specification for the Company Intelligence Dashboard. All development should reference this document for requirements, data sources, and visual specifications.

**Last Updated**: 2026-02-10
**Project**: Turd News Network (Stonk Bot)
