import streamlit as st
import feedparser
import requests
from datetime import datetime, timedelta
import json
import time
import pandas as pd
import plotly.express as px
from collections import Counter
import re

st.set_page_config(
    page_title="News Scraper Pro",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)


class NewsFlowPro:
    def __init__(self):
        # Telegram Bot Configuration
        self.BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
        self.USER_IDS = st.secrets["TELEGRAM_USER_IDS"]

        #  RSS feeds with defense and regional categories
        self.feeds = {
            'Air': [
                'https://www.ainonline.com/rss.xml',
                'https://www.flightglobal.com/rss/defence/rss.xml',
                'https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10',
                'https://www.airandspaceforces.com/feed/',
                'https://www.defensenews.com/air/feed/',
                'https://theaviationist.com/feed/'
            ],
            'Sea': [
                'https://www.navalnews.com/feed/',
                'https://news.usni.org/category/news/fleet-tracker/feed',
                'https://www.navytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml',
                'https://www.defensenews.com/naval/feed/',
                'https://www.maritimeexecutive.com/rss/all-news',
                'https://thediplomat.com/category/flashpoints/maritime-security/feed/'
            ],
            'Industry': [
                'https://www.defensenews.com/industry/feed/',
                'https://www.shephard.co.uk/rss',
                'https://breakingdefense.com/feed/',
                'https://www.flightglobal.com/rss/aerospace/rss.xml',
                'https://www.defensedaily.com/rss',
                'https://www.aviationweek.com/rss.xml'
            ],
            'Land': [
                'https://www.armytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml',
                'https://www.army.mil/rss/news/',
                'https://www.defensenews.com/land/feed/',
                'https://armyrecognition.com/rss_feed/army_recognition_news_online.xml',
                'https://www.militarytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml',
                'https://www.shephardmedia.com/rss/'
            ],
            'C4ISR': [
                'https://www.c4isrnet.com/rss/',
                'https://www.defensenews.com/c2-comms/feed/',
                'https://breakingdefense.com/category/c4isr/feed/',
                'https://www.militaryaerospace.com/rss.xml',
                'https://www.intelligent-aerospace.com/rss.xml',
                'https://www.cybersecuritydive.com/feeds/news/'
            ],
            'Weapons': [
                'https://www.defensenews.com/weapons/feed/',
                'https://missilethreat.csis.org/feed/',
                'https://www.thedefensepost.com/feed/',
                'https://theaviationist.com/feed/',
                'https://armyrecognition.com/rss_feed/army_recognition_news_online.xml',
                'https://breakingdefense.com/category/weapons/feed/'
            ],
            'Security': [
                'https://www.hstoday.us/feed/',
                'https://www.securitymagazine.com/rss/all',
                'https://www.securityweek.com/feed/',
                'https://www.cybersecuritydive.com/feeds/news/',
                'https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10',
                'https://www.cfr.org/rss-feeds/cyber-brief?format=xml'
            ],
            'Latest Analysis': [
                'https://warontherocks.com/feed/',
                'https://www.csis.org/rss/all-csis-content',
                'https://www.rand.org/blog.xml',
                'https://www.brookings.edu/rss/',
                'https://www.cfr.org/rss-feeds/expert-briefs?format=xml',
                'https://carnegieendowment.org/feeds/all.xml'
            ],
            'Company Updates': [
                'https://www.lockheedmartin.com/en-us/news.rss.xml',
                'https://boeing.mediaroom.com/rss',
                'https://www.northropgrumman.com/news/rss/',
                'https://www.rtx.com/news/rss',
                'https://www.generaldynamics.com/news/rss',
                'https://www.defensenews.com/industry/feed/'
            ],
            'Terrorism and Insurgency': [
                'https://ctc.usma.edu/feed/',
                'https://www.start.umd.edu/news/rss.xml',
                'https://icsr.info/feed/',
                'https://www.longwarjournal.org/feeds/rss-2-full',
                'https://www.trackingterrorism.org/rss',
                'https://www.counterextremism.com/rss.xml'
            ],
            'Middle East - Palestine': [
                'https://www.jpost.com/rss/rssfeedsfrontpage',
                'https://www.haaretz.com/cmlink/1.628752',
                'https://english.wafa.ps/rss',
                'https://www.middleeasteye.net/rss',
                'https://www.al-monitor.com/rss.xml'
            ],
            'Middle East - Iran': [
                'https://www.presstv.ir/rss',
                'https://en.mehrnews.com/rss',
                'https://www.tasnimnews.com/en/rss/feed',
                'https://www.iranintl.com/en/rss.xml',
                'https://www.al-monitor.com/pulse/rss/iran.xml',
                'https://thediplomat.com/regions/middle-east/feed/'
            ],
            'Middle East - Gulf States': [
                'https://www.arabnews.com/rss.xml',
                'https://gulfnews.com/rss',
                'https://www.thenationalnews.com/rss',
                'https://www.gulf-times.com/rss/qatar-news',
                'https://www.khaleejtimes.com/rss',
                'https://www.al-monitor.com/pulse/rss/gulf.xml'
            ],
            'Middle East - Syria/Iraq': [
                'https://sana.sy/en/?feed=rss2',
                'https://www.kurdistan24.net/rss',
                'https://www.rudaw.net/rss',
                'https://www.alsumaria.tv/rss',
                'https://www.iraqinews.com/feed/',
                'https://thediplomat.com/regions/middle-east/feed/'
            ],
            'Middle East - Turkey': [
                'https://www.hurriyetdailynews.com/rss',
                'https://www.dailysabah.com/rss',
                'https://www.aa.com.tr/en/rss/default?cat=turkey',
                'https://www.duvarenglish.com/rss',
                'https://www.trtworld.com/rss',
                'https://thediplomat.com/regions/middle-east/feed/'
            ],
            # Keep original categories for backward compatibility
            'Military': [
                'https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10',
                'https://www.militarytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml',
                'https://www.navytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml',
                'https://www.armytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml',
                'https://www.stripes.com/rss/news.rss',
                'https://www.defensenews.com/rss/'
            ],
            'Politics': [
                'http://feeds.reuters.com/Reuters/PoliticsNews',
                'https://www.politico.com/rss/politicopicks.xml',
                'https://feeds.washingtonpost.com/rss/politics',
                'https://www.npr.org/rss/rss.php?id=1014',
                'https://abcnews.go.com/abcnews/politicsheadlines',
                'https://feeds.bbci.co.uk/news/politics/rss.xml'
            ],
            'Geography': [
                'https://www.nationalgeographic.com/news/rss/',
                'https://www.sciencedaily.com/rss/earth_climate.xml',
                'https://earthobservatory.nasa.gov/rss/earth_news.xml',
                'https://www.noaa.gov/news/rss/news.xml',
                'https://www.nature.com/nature/current_issue/rss',
                'https://www.usgs.gov/rss/home.xml'
            ],
            'Finance': [
                'https://feeds.finance.yahoo.com/rss/2.0/headline',
                'http://feeds.reuters.com/reuters/businessNews',
                'https://www.marketwatch.com/rss/topstories',
                'https://www.bloomberg.com/politics/feeds/site.xml',
                'https://www.cnbc.com/id/100003114/device/rss/rss.html'
            ],
            'Technology': [
                'http://feeds.reuters.com/reuters/technologyNews',
                'https://techcrunch.com/feed/',
                'https://www.theverge.com/rss/index.xml',
                'https://feeds.arstechnica.com/arstechnica/index',
                'https://www.wired.com/feed/rss'
            ]
        }

        #  keywords for all categories
        if 'saved_searches' not in st.session_state:
            st.session_state.saved_searches = {
                'Air': ['aircraft', 'fighter jet', 'drone', 'UAV', 'air force', 'aviation', 'helicopter', 'bomber',
                        'aerial', 'airspace', 'pilot', 'squadron', 'stealth', 'F-35', 'F-16', 'missile defense'],
                'Sea': ['naval', 'ship', 'submarine', 'fleet', 'maritime', 'destroyer', 'frigate', 'carrier',
                        'coast guard', 'port', 'naval base', 'amphibious', 'torpedo', 'sonar', 'radar'],
                'Industry': ['defense contractor', 'military industrial', 'procurement', 'contract', 'manufacturing',
                             'Lockheed Martin', 'Boeing', 'Northrop Grumman', 'Raytheon', 'General Dynamics',
                             'BAE Systems', 'merger', 'acquisition', 'supply chain', 'production'],
                'Land': ['army', 'tank', 'armored vehicle', 'infantry', 'ground forces', 'artillery', 'combat',
                         'battalion', 'regiment', 'base', 'training', 'deployment', 'soldier', 'equipment'],
                'C4ISR': ['intelligence', 'surveillance', 'reconnaissance', 'communication', 'command', 'control',
                          'cyber', 'electronic warfare', 'signals intelligence', 'radar', 'satellite', 'ISR'],
                'Weapons': ['missile', 'weapons system', 'ammunition', 'firepower', 'ballistic', 'cruise missile',
                            'rocket', 'guided munition', 'precision strike', 'warhead', 'launcher', 'ordnance'],
                'Security': ['homeland security', 'border security', 'counterterrorism', 'cybersecurity', 'threat',
                             'intelligence', 'surveillance', 'protection', 'emergency response',
                             'critical infrastructure'],
                'Latest Analysis': ['strategic analysis', 'defense policy', 'military strategy', 'geopolitical',
                                    'threat assessment', 'security studies', 'defense research', 'policy analysis'],
                'Company Updates': ['earnings', 'quarterly results', 'new contract', 'partnership', 'merger',
                                    'acquisition', 'product launch', 'technology development', 'expansion'],
                'Terrorism and Insurgency': ['terrorism', 'terrorist', 'insurgency', 'extremism', 'radical',
                                             'jihadist', 'ISIS', 'al-Qaeda', 'counterterrorism', 'militant'],
                'Middle East - Palestine': ['Israel', 'Palestine', 'Gaza', 'West Bank', 'Jerusalem', 'IDF',
                                                   'Hamas', 'Fatah', 'settlement', 'conflict', 'peace process'],
                'Middle East - Iran': ['Iran', 'Tehran', 'nuclear', 'sanctions', 'IRGC', 'Hezbollah', 'proxy',
                                       'Persian Gulf', 'uranium enrichment', 'Supreme Leader'],
                'Middle East - Gulf States': ['Saudi Arabia', 'UAE', 'Qatar', 'Kuwait', 'Bahrain', 'Oman',
                                              'GCC', 'oil', 'energy', 'Gulf cooperation'],
                'Middle East - Syria/Iraq': ['Syria', 'Iraq', 'Assad', 'Kurdistan', 'ISIS', 'civil war',
                                             'refugee', 'reconstruction', 'sectarian'],
                'Middle East - Turkey': ['Turkey', 'Erdogan', 'Kurdish', 'PKK', 'Syria border', 'NATO',
                                         'Bosphorus', 'Cyprus', 'Greece tensions'],
                # Original categories
                'Military': ['military', 'defense', 'army', 'navy', 'air force', 'marines', 'pentagon', 'NATO', 'war',
                             'conflict', 'security', 'deployment', 'veteran', 'combat', 'homeland security'],
                'Politics': ['politics', 'election', 'congress', 'senate', 'president', 'vote', 'policy', 'government',
                             'democrat', 'republican', 'campaign', 'legislation', 'political', 'governor', 'mayor'],
                'Geography': ['geography', 'climate', 'environment', 'earthquake', 'hurricane', 'natural disaster',
                              'mapping', 'exploration', 'geological', 'weather', 'ocean', 'mountain', 'forest',
                              'ecosystem', 'conservation'],
                'Finance': ['stocks', 'earnings', 'market', 'Fed', 'inflation', 'crypto', 'Bitcoin', 'Tesla'],
                'Technology': ['AI', 'tech', 'startup', 'Google', 'Apple', 'Microsoft', 'OpenAI', 'software']
            }

        if 'scraped_articles' not in st.session_state:
            st.session_state.scraped_articles = []

        if 'last_scrape_time' not in st.session_state:
            st.session_state.last_scrape_time = None

    def keyword_match(self, text, keywords):
        """Check if any keywords appear in the text"""
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False

    def scrape_feed(self, feed_url):
        """Scrape a single RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            articles = []

            for entry in feed.entries:
                article = {
                    'title': entry.title,
                    'link': entry.link,
                    'published': getattr(entry, 'published', 'No date'),
                    'summary': getattr(entry, 'summary', '')[:300] + '...',
                    'source': feed.feed.title if hasattr(feed.feed, 'title') else 'Unknown'
                }
                articles.append(article)

            return articles
        except Exception as e:
            st.error(f"Error scraping {feed_url}: {e}")
            return []

    def scrape_by_category(self, categories, progress_bar=None):
        """Scrape news for selected categories"""
        all_articles = []
        total_feeds = sum(len(self.feeds[cat]) for cat in categories if cat in self.feeds)
        current_feed = 0

        for category in categories:
            if category not in self.feeds:
                continue

            feeds_to_check = self.feeds[category]
            keywords_to_check = st.session_state.saved_searches[category]

            for feed_url in feeds_to_check:
                if progress_bar:
                    progress_bar.progress((current_feed + 1) / total_feeds)

                articles = self.scrape_feed(feed_url)

                # Filter articles by keywords
                for article in articles:
                    title_match = self.keyword_match(article['title'], keywords_to_check)
                    summary_match = self.keyword_match(article['summary'], keywords_to_check)

                    if title_match or summary_match:
                        article['matched_keywords'] = [kw for kw in keywords_to_check
                                                       if kw.lower() in article['title'].lower()
                                                       or kw.lower() in article['summary'].lower()]
                        article['category'] = category
                        article['scrape_time'] = datetime.now()
                        all_articles.append(article)

                current_feed += 1
                time.sleep(0.3)  # Be nice to servers

        return all_articles

    def send_telegram_message(self, message, user_id):
        """Send a message to a specific Telegram user"""
        try:
            url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': user_id,
                'text': message,
                'disable_web_page_preview': True,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, data=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                return result['ok']
            return False
        except Exception as e:
            st.error(f"Error sending message to {user_id}: {e}")
            return False

    def format_article_for_telegram(self, article):
        """Format a single article for Telegram"""
        category_emojis = {
            'Air': '✈️',
            'Sea': '⚓',
            'Industry': '🏭',
            'Land': '🎖️',
            'C4ISR': '📡',
            'Weapons': '🚀',
            'Security': '🔒',
            'Latest Analysis': '📊',
            'Company Updates': '💼',
            'Terrorism and Insurgency': '⚠️',
            'Middle East - Palestine': '🇮🇱',
            'Middle East - Iran': '🇮🇷',
            'Middle East - Gulf States': '🏛️',
            'Middle East - Syria/Iraq': '🏺',
            'Middle East - Turkey': '🇹🇷',
            'Military': '🪖',
            'Politics': '🏛️',
            'Geography': '🌍',
            'Finance': '💰',
            'Technology': '💻'
        }

        emoji = category_emojis.get(article['category'], '📰')

        message = f"""{emoji} <b>{article['category'].upper()} NEWS</b>

📰 <b>{article['title']}</b>

📝 <b>Summary:</b>
{article['summary'][:400]}{'...' if len(article['summary']) > 400 else ''}

🏷️ <b>Keywords:</b> {', '.join(article['matched_keywords'])}

📅 <b>Published:</b> {article['published']}
📰 <b>Source:</b> {article['source']}

🔗 <a href="{article['link']}">Read Full Article</a>

---"""

        return message

    def send_news_to_telegram(self, articles, max_articles=10):
        """Send scraped news articles to Telegram users"""
        if not articles:
            return False, "No articles to send"

        articles_to_send = articles[:max_articles]
        success_count = 0
        total_messages = len(self.USER_IDS) * len(articles_to_send)

        for user_id in self.USER_IDS:
            for i, article in enumerate(articles_to_send):
                message = self.format_article_for_telegram(article)

                if self.send_telegram_message(message, user_id):
                    success_count += 1

                time.sleep(1)  # Rate limiting between messages

        return success_count > 0, f"Sent {success_count}/{total_messages} messages successfully"


def main():
    scraper = NewsFlowPro()

    # Header
    st.title("📰 News Scraper Pro")
    st.markdown("** Defense & Intelligence News Scraper with  Categories**")

    # Sidebar
    with st.sidebar:
        st.header("🔧 Control Panel")

        # Navigation
        page = st.selectbox(
            "Navigate to:",
            ["📰 News Dashboard", "⚙️ Admin Panel", "📊 Analytics", "💾 Export Data"]
        )

        st.divider()

        # Quick category buttons
        st.subheader("⚡ Quick Actions")

        if st.button("🛡️ All Defense Categories", type="primary"):
            defense_cats = ['Air', 'Sea', 'Land', 'C4ISR', 'Weapons', 'Security', 'Industry']
            with st.spinner("Scraping defense news..."):
                progress_bar = st.progress(0)
                articles = scraper.scrape_by_category(defense_cats, progress_bar)
                st.session_state.scraped_articles = articles
                st.session_state.last_scrape_time = datetime.now()
                st.success(f"Found {len(articles)} defense articles!")
                progress_bar.empty()

        if st.button("🌍 All Middle East Regions"):
            me_cats = [cat for cat in scraper.feeds.keys() if cat.startswith('Middle East')]
            with st.spinner("Scraping Middle East news..."):
                progress_bar = st.progress(0)
                articles = scraper.scrape_by_category(me_cats, progress_bar)
                st.session_state.scraped_articles = articles
                st.session_state.last_scrape_time = datetime.now()
                st.success(f"Found {len(articles)} Middle East articles!")
                progress_bar.empty()

        if st.button("🔄 Quick Scrape All"):
            all_cats = ['Military', 'Politics', 'Geography', 'Finance', 'Technology']
            with st.spinner("Scraping all news..."):
                progress_bar = st.progress(0)
                articles = scraper.scrape_by_category(all_cats, progress_bar)
                st.session_state.scraped_articles = articles
                st.session_state.last_scrape_time = datetime.now()
                st.success(f"Found {len(articles)} articles!")
                progress_bar.empty()

        st.divider()

        # Telegram controls
        if st.button("📱 Send Latest to Telegram"):
            if st.session_state.scraped_articles:
                with st.spinner("Sending to Telegram..."):
                    success, message = scraper.send_news_to_telegram(st.session_state.scraped_articles)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.warning("No articles to send. Please scrape first!")

        if st.button("🧪 Test Telegram Bot"):
            with st.spinner("Testing Telegram connection..."):
                test_message = f"""🤖 <b> News Scraper Test</b>

✅ Bot Status: Online
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧  with defense categories and Middle East focus

If you receive this message, the bot is working correctly!"""

                success_count = 0
                for user_id in scraper.USER_IDS:
                    if scraper.send_telegram_message(test_message, user_id):
                        success_count += 1

                if success_count > 0:
                    st.success(f"✅ Test successful! Sent to {success_count}/{len(scraper.USER_IDS)} users")
                else:
                    st.error("❌ Test failed. Check bot token and user IDs")

        st.divider()

        # Show Telegram info
        with st.expander("📱 Telegram Settings"):
            st.markdown("**Bot Token:**")
            if scraper.BOT_TOKEN:
                st.code(scraper.BOT_TOKEN[:20] + "...", language="text")
            else:
                st.warning("Bot token not found in secrets")

            st.markdown("**User IDs:**")
            if scraper.USER_IDS:
                for user_id in scraper.USER_IDS:
                    st.code(str(user_id), language="text")
            else:
                st.warning("User IDs not found in secrets")

    # Main content based on page selection
    if page == "📰 News Dashboard":
        show_news_dashboard(scraper)
    elif page == "⚙️ Admin Panel":
        show_admin_panel(scraper)
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "💾 Export Data":
        show_export_panel()


def show_news_dashboard(scraper):
    st.header("📰  News Dashboard")

    # Tabbed interface for better organization
    tab1, tab2, tab3 = st.tabs(["🛡️ Defense Categories", "🌍 Regional News", "📊 Traditional Categories"])

    with tab1:
        st.subheader("Defense & Security Categories")

        defense_categories = ['Air', 'Sea', 'Land', 'C4ISR', 'Weapons', 'Security', 'Industry',
                              'Latest Analysis', 'Company Updates', 'Terrorism and Insurgency']

        selected_defense = st.multiselect(
            "Select Defense Categories:",
            defense_categories,
            default=['Air', 'Sea', 'Weapons', 'Security']
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Scrape Defense News", type="primary"):
                if selected_defense:
                    with st.spinner("Scraping defense news..."):
                        progress_bar = st.progress(0)
                        articles = scraper.scrape_by_category(selected_defense, progress_bar)
                        st.session_state.scraped_articles = articles
                        st.session_state.last_scrape_time = datetime.now()
                        st.success(f"Found {len(articles)} defense articles!")
                        progress_bar.empty()

        with col2:
            if st.button("📱 Scrape & Send Defense"):
                if selected_defense:
                    with st.spinner("Scraping and sending..."):
                        progress_bar = st.progress(0)
                        articles = scraper.scrape_by_category(selected_defense, progress_bar)
                        st.session_state.scraped_articles = articles
                        st.session_state.last_scrape_time = datetime.now()

                        if articles:
                            success, message = scraper.send_news_to_telegram(articles)
                            if success:
                                st.success(f"✅ Found {len(articles)} articles and sent to Telegram!")
                            else:
                                st.error(f"❌ Failed to send: {message}")

    with tab2:
        st.subheader("Middle East Regional Coverage")

        me_categories = [cat for cat in scraper.feeds.keys() if cat.startswith('Middle East')]
        me_display_names = [cat.replace('Middle East - ', '') for cat in me_categories]

        selected_regions = st.multiselect(
            "Select Middle East Regions:",
            me_display_names,
            default=['Palestine', 'Iran']
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Scrape Regional News", type="primary"):
                if selected_regions:
                    full_categories = [f"Middle East - {region}" for region in selected_regions]
                    with st.spinner("Scraping regional news..."):
                        progress_bar = st.progress(0)
                        articles = scraper.scrape_by_category(full_categories, progress_bar)
                        st.session_state.scraped_articles = articles
                        st.session_state.last_scrape_time = datetime.now()
                        st.success(f"Found {len(articles)} regional articles!")
                        progress_bar.empty()

        with col2:
            if st.button("📱 Scrape & Send Regional"):
                if selected_regions:
                    full_categories = [f"Middle East - {region}" for region in selected_regions]
                    with st.spinner("Scraping and sending..."):
                        progress_bar = st.progress(0)
                        articles = scraper.scrape_by_category(full_categories, progress_bar)
                        st.session_state.scraped_articles = articles
                        st.session_state.last_scrape_time = datetime.now()

                        if articles:
                            success, message = scraper.send_news_to_telegram(articles)
                            if success:
                                st.success(f"✅ Found {len(articles)} articles and sent to Telegram!")
                            else:
                                st.error(f"❌ Failed to send: {message}")

    with tab3:
        st.subheader("Traditional News Categories")

        traditional_categories = ['Military', 'Politics', 'Geography', 'Finance', 'Technology']

        selected_traditional = st.multiselect(
            "Select Traditional Categories:",
            traditional_categories,
            default=['Military', 'Politics']
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Scrape Traditional News", type="primary"):
                if selected_traditional:
                    with st.spinner("Scraping traditional news..."):
                        progress_bar = st.progress(0)
                        articles = scraper.scrape_by_category(selected_traditional, progress_bar)
                        st.session_state.scraped_articles = articles
                        st.session_state.last_scrape_time = datetime.now()
                        st.success(f"Found {len(articles)} traditional articles!")
                        progress_bar.empty()

        with col2:
            if st.button("📱 Scrape & Send Traditional"):
                if selected_traditional:
                    with st.spinner("Scraping and sending..."):
                        progress_bar = st.progress(0)
                        articles = scraper.scrape_by_category(selected_traditional, progress_bar)
                        st.session_state.scraped_articles = articles
                        st.session_state.last_scrape_time = datetime.now()

                        if articles:
                            success, message = scraper.send_news_to_telegram(articles)
                            if success:
                                st.success(f"✅ Found {len(articles)} articles and sent to Telegram!")
                            else:
                                st.error(f"❌ Failed to send: {message}")

    # Display scraped articles
    if st.session_state.scraped_articles:
        st.divider()
        show_articles_list(st.session_state.scraped_articles)


def show_articles_list(articles):
    """Display articles in an organized list"""
    if not articles:
        return

    st.subheader(f"📋 Found {len(articles)} Articles")

    # Category filter
    categories_in_results = list(set([article['category'] for article in articles]))
    category_filter = st.selectbox("Filter by category:", ['All'] + categories_in_results, key="article_filter")

    # Filter articles
    if category_filter == 'All':
        filtered_articles = articles
    else:
        filtered_articles = [a for a in articles if a['category'] == category_filter]

    st.markdown(f"**Showing {len(filtered_articles)} articles**")

    # Display articles in expandable cards
    for i, article in enumerate(filtered_articles[:20]):  # Limit to 20 for performance
        # Category emoji mapping
        category_emojis = {
            'Air': '✈️',
            'Sea': '⚓',
            'Industry': '🏭',
            'Land': '🎖️',
            'C4ISR': '📡',
            'Weapons': '🚀',
            'Security': '🔒',
            'Latest Analysis': '📊',
            'Company Updates': '💼',
            'Terrorism and Insurgency': '⚠️',
            'Middle East - Palestine': '🇮🇱',
            'Middle East - Iran': '🇮🇷',
            'Middle East - Gulf States': '🏛️',
            'Middle East - Syria/Iraq': '🏺',
            'Middle East - Turkey': '🇹🇷',
            'Military': '🪖',
            'Politics': '🏛️',
            'Geography': '🌍',
            'Finance': '💰',
            'Technology': '💻'
        }

        emoji = category_emojis.get(article['category'], '📰')

        with st.expander(f"{emoji} {article['category']} | {article['title'][:80]}..."):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Source:** {article['source']}")
                st.markdown(f"**Published:** {article['published']}")
                st.markdown(f"**Summary:** {article['summary']}")
                if article.get('matched_keywords'):
                    st.markdown(f"**Matched Keywords:** {', '.join(article['matched_keywords'])}")
            with col2:
                st.markdown(f"[🔗 Read Full Article]({article['link']})")

                # Send individual article to Telegram
                if st.button("📱 Send to Telegram", key=f"send_{i}"):
                    with st.spinner("Sending..."):
                        success_count = 0
                        for user_id in scraper.USER_IDS:
                            message = scraper.format_article_for_telegram(article)
                            if scraper.send_telegram_message(message, user_id):
                                success_count += 1

                        if success_count > 0:
                            st.success(f"✅ Sent to {success_count} users!")
                        else:
                            st.error("❌ Failed to send")


def show_admin_panel(scraper):
    st.header("⚙️ Admin Panel")

    # Tabs for different admin functions
    tab1, tab2, tab3, tab4 = st.tabs(["🔑 Manage Keywords", "📡 Manage Feeds", "🗂️ Categories", "📱 Telegram Settings"])

    with tab1:
        st.subheader("Keyword Management")

        # Category groups for easier management
        col1, col2 = st.columns(2)
        with col1:
            category_group = st.radio(
                "Category Group:",
                ["Defense Categories", "Middle East Regions", "Traditional Categories"]
            )

        with col2:
            if category_group == "Defense Categories":
                available_cats = ['Air', 'Sea', 'Land', 'C4ISR', 'Weapons', 'Security', 'Industry',
                                  'Latest Analysis', 'Company Updates', 'Terrorism and Insurgency']
            elif category_group == "Middle East Regions":
                available_cats = [cat for cat in scraper.feeds.keys() if cat.startswith('Middle East')]
            else:
                available_cats = ['Military', 'Politics', 'Geography', 'Finance', 'Technology']

        selected_cat = st.selectbox("Select Category to Manage:", available_cats)

        if selected_cat in st.session_state.saved_searches:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Current Keywords:**")
                keywords = st.session_state.saved_searches[selected_cat]

                # Display current keywords with delete buttons
                for keyword in keywords:
                    col_kw, col_del = st.columns([3, 1])
                    with col_kw:
                        st.text(f"• {keyword}")
                    with col_del:
                        if st.button("❌", key=f"del_{selected_cat}_{keyword}"):
                            st.session_state.saved_searches[selected_cat].remove(keyword)
                            st.rerun()

            with col2:
                st.markdown("**Add New Keywords:**")
                new_keyword = st.text_input("Enter new keyword:")
                if st.button("➕ Add Keyword") and new_keyword:
                    if new_keyword not in st.session_state.saved_searches[selected_cat]:
                        st.session_state.saved_searches[selected_cat].append(new_keyword)
                        st.success(f"Added '{new_keyword}' to {selected_cat}")
                        st.rerun()
                    else:
                        st.warning("Keyword already exists!")

                # Bulk add
                st.markdown("**Bulk Add (comma-separated):**")
                bulk_keywords = st.text_area("Enter keywords separated by commas:")
                if st.button("📝 Add All") and bulk_keywords:
                    new_keywords = [kw.strip() for kw in bulk_keywords.split(',')]
                    added = 0
                    for kw in new_keywords:
                        if kw and kw not in st.session_state.saved_searches[selected_cat]:
                            st.session_state.saved_searches[selected_cat].append(kw)
                            added += 1
                    st.success(f"Added {added} new keywords!")
                    st.rerun()

    with tab2:
        st.subheader("RSS Feed Management")

        # Feed category selection
        feed_cat = st.selectbox("Select Category for Feeds:", list(scraper.feeds.keys()), key="feed_cat")

        st.markdown("**Current RSS Feeds:**")
        for i, feed in enumerate(scraper.feeds[feed_cat]):
            col_feed, col_test, col_del = st.columns([3, 1, 1])
            with col_feed:
                st.text(f"{i + 1}. {feed}")
            with col_test:
                if st.button("🧪", key=f"test_{feed_cat}_{i}", help="Test feed"):
                    with st.spinner("Testing feed..."):
                        articles = scraper.scrape_feed(feed)
                        if articles:
                            st.success(f"✅ Working! Found {len(articles)} articles")
                        else:
                            st.error("❌ Feed not working")
            with col_del:
                if st.button("🗑️", key=f"delete_{feed_cat}_{i}", help="Delete feed"):
                    scraper.feeds[feed_cat].remove(feed)
                    st.success("Feed deleted!")
                    st.rerun()

        # Add new feed
        st.markdown("**Add New RSS Feed:**")
        col1, col2 = st.columns([3, 1])
        with col1:
            new_feed = st.text_input("Enter RSS feed URL:")
        with col2:
            if st.button("🔗 Add Feed") and new_feed:
                # Simple validation
                if new_feed.startswith('http'):
                    scraper.feeds[feed_cat].append(new_feed)
                    st.success("Feed added!")
                    st.rerun()
                else:
                    st.error("Please enter a valid URL")

    with tab3:
        st.subheader("Category Overview")

        #  category overview with metrics
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Defense Categories:**")
            defense_cats = ['Air', 'Sea', 'Land', 'C4ISR', 'Weapons', 'Security', 'Industry',
                            'Latest Analysis', 'Company Updates', 'Terrorism and Insurgency']
            for category in defense_cats:
                with st.expander(f"🛡️ {category}"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Keywords", len(st.session_state.saved_searches.get(category, [])))
                    with col_b:
                        st.metric("RSS Feeds", len(scraper.feeds.get(category, [])))
                    with col_c:
                        recent_articles = [a for a in st.session_state.scraped_articles if
                                           a.get('category') == category]
                        st.metric("Recent Articles", len(recent_articles))

        with col2:
            st.markdown("**Regional Categories:**")
            regional_cats = [cat for cat in scraper.feeds.keys() if cat.startswith('Middle East')]
            for category in regional_cats:
                with st.expander(f"🌍 {category}"):
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Keywords", len(st.session_state.saved_searches.get(category, [])))
                    with col_b:
                        st.metric("RSS Feeds", len(scraper.feeds.get(category, [])))
                    with col_c:
                        recent_articles = [a for a in st.session_state.scraped_articles if
                                           a.get('category') == category]
                        st.metric("Recent Articles", len(recent_articles))

    with tab4:
        st.subheader("Telegram Bot Configuration")

        st.markdown("**Current Configuration:**")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Bot Token Status:**")
            if scraper.BOT_TOKEN:
                st.success("✅ Bot token configured")
                st.code(scraper.BOT_TOKEN[:20] + "...", language="text")
            else:
                st.error("❌ Bot token not found")
                st.markdown("Please add `TELEGRAM_BOT_TOKEN` to your Streamlit secrets")

        with col2:
            st.markdown("**User IDs Status:**")
            if scraper.USER_IDS:
                st.success(f"✅ {len(scraper.USER_IDS)} user(s) configured")
                for i, user_id in enumerate(scraper.USER_IDS):
                    st.code(f"User {i + 1}: {user_id}", language="text")
            else:
                st.error("❌ No user IDs found")
                st.markdown("Please add `TELEGRAM_USER_IDS` to your Streamlit secrets")

        st.markdown("**Configuration Help:**")
        with st.expander("📖 How to Configure Telegram Bot"):
            st.markdown("""
            **Step 1: Create a Telegram Bot**
            1. Message @BotFather on Telegram
            2. Send `/newbot` command
            3. Follow instructions to create your bot
            4. Copy the bot token

            **Step 2: Get Your Chat ID**
            1. Message your bot or add it to a group
            2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
            3. Look for "chat":{"id": YOUR_CHAT_ID}

            **Step 3: Add to Streamlit Secrets**
            ```toml
            TELEGRAM_BOT_TOKEN = "your_bot_token_here"
            TELEGRAM_USER_IDS = [123456789, 987654321]
            ```
            """)


def show_analytics():
    st.header("📊  Analytics Dashboard")

    if not st.session_state.scraped_articles:
        st.info("No data available. Please scrape some news first!")
        return

    articles = st.session_state.scraped_articles

    #  metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Articles", len(articles))
    with col2:
        categories = [a['category'] for a in articles]
        st.metric("Categories", len(set(categories)))
    with col3:
        sources = [a['source'] for a in articles]
        st.metric("Sources", len(set(sources)))
    with col4:
        keywords = []
        for a in articles:
            keywords.extend(a.get('matched_keywords', []))
        st.metric("Total Keyword Matches", len(keywords))

    #  visualizations
    col1, col2 = st.columns(2)

    with col1:
        # Articles by category with  styling
        category_counts = Counter([a['category'] for a in articles])
        df_cat = pd.DataFrame(list(category_counts.items()), columns=['Category', 'Count'])

        # Separate defense vs regional vs traditional
        def categorize_type(cat):
            if cat.startswith('Middle East'):
                return 'Regional'
            elif cat in ['Air', 'Sea', 'Land', 'C4ISR', 'Weapons', 'Security', 'Industry',
                         'Latest Analysis', 'Company Updates', 'Terrorism and Insurgency']:
                return 'Defense'
            else:
                return 'Traditional'

        df_cat['Type'] = df_cat['Category'].apply(categorize_type)

        fig1 = px.bar(df_cat, x='Category', y='Count', color='Type',
                      title='Articles by Category and Type')
        fig1.update_xaxis(tickangle=45)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Top keywords
        all_keywords = []
        for a in articles:
            all_keywords.extend(a.get('matched_keywords', []))
        keyword_counts = Counter(all_keywords)
        top_keywords = dict(keyword_counts.most_common(15))
        df_kw = pd.DataFrame(list(top_keywords.items()), columns=['Keyword', 'Count'])
        fig2 = px.bar(df_kw, x='Count', y='Keyword', orientation='h',
                      title='Top 15 Keywords')
        st.plotly_chart(fig2, use_container_width=True)

    # Content type breakdown
    st.subheader("📈 Content Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Defense vs Regional vs Traditional pie chart
        defense_count = len([a for a in articles if categorize_type(a['category']) == 'Defense'])
        regional_count = len([a for a in articles if categorize_type(a['category']) == 'Regional'])
        traditional_count = len([a for a in articles if categorize_type(a['category']) == 'Traditional'])

        fig_pie = px.pie(
            values=[defense_count, regional_count, traditional_count],
            names=['Defense & Security', 'Regional Middle East', 'Traditional News'],
            title='Content Distribution by Type'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Source diversity
        source_counts = Counter([a['source'] for a in articles])
        top_sources = dict(source_counts.most_common(10))
        df_sources = pd.DataFrame(list(top_sources.items()), columns=['Source', 'Articles'])

        fig_sources = px.bar(df_sources, x='Articles', y='Source', orientation='h',
                             title='Top 10 News Sources')
        st.plotly_chart(fig_sources, use_container_width=True)


def show_export_panel():
    st.header("💾 Export Data")

    if not st.session_state.scraped_articles:
        st.info("No data to export. Please scrape some news first!")
        return

    articles = st.session_state.scraped_articles

    # Export options with  filtering
    st.subheader("🔧 Export Configuration")

    col1, col2 = st.columns(2)

    with col1:
        # Category filter for export
        all_categories = list(set([a['category'] for a in articles]))
        selected_export_cats = st.multiselect(
            "Select categories to export:",
            all_categories,
            default=all_categories
        )

    with col2:
        # Export format
        export_format = st.selectbox(
            "Export format:",
            ["JSON (Full Data)", "CSV (Simplified)", "TXT (Summary Report)"]
        )

    # Filter articles for export
    filtered_articles = [a for a in articles if a['category'] in selected_export_cats]

    st.info(f"Ready to export {len(filtered_articles)} articles from {len(selected_export_cats)} categories")

    # Export buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Download JSON") and export_format.startswith("JSON"):
            json_data = json.dumps(filtered_articles, indent=2, default=str)
            st.download_button(
                label="💾 Download JSON File",
                data=json_data,
                file_name=f"_news_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    with col2:
        if st.button("📊 Download CSV") and export_format.startswith("CSV"):
            # Flatten data for CSV
            csv_data = []
            for article in filtered_articles:
                csv_data.append({
                    'Title': article['title'],
                    'Category': article['category'],
                    'Source': article['source'],
                    'Published': article['published'],
                    'Link': article['link'],
                    'Keywords': ', '.join(article.get('matched_keywords', [])),
                    'Summary': article['summary'].replace('\n', ' ')
                })

            df = pd.DataFrame(csv_data)
            csv_string = df.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV File",
                data=csv_string,
                file_name=f"_news_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    with col3:
        if st.button("📄 Generate Report"):
            # Generate summary report
            report = f"""#  News Intelligence Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics
- Total Articles: {len(filtered_articles)}
- Categories Covered: {len(selected_export_cats)}
- Unique Sources: {len(set([a['source'] for a in filtered_articles]))}

## Category Breakdown
"""
            category_counts = Counter([a['category'] for a in filtered_articles])
            for cat, count in category_counts.most_common():
                report += f"- {cat}: {count} articles\n"

            report += "\n## Top Keywords\n"
            all_keywords = []
            for a in filtered_articles:
                all_keywords.extend(a.get('matched_keywords', []))
            keyword_counts = Counter(all_keywords)
            for kw, count in keyword_counts.most_common(10):
                report += f"- {kw}: {count} mentions\n"

            st.download_button(
                label="📋 Download Report",
                data=report,
                file_name=f"_news_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )

    #  preview
    st.subheader("👀 Export Preview")

    # Show sample data
    if filtered_articles:
        preview_df = pd.DataFrame([
            {
                'Title': a['title'][:60] + '...' if len(a['title']) > 60 else a['title'],
                'Category': a['category'],
                'Source': a['source'],
                'Keywords': ', '.join(a.get('matched_keywords', [])[:3])
            }
            for a in filtered_articles[:15]
        ])
        st.dataframe(preview_df, use_container_width=True)

        if len(filtered_articles) > 15:
            st.info(f"Showing first 15 articles. Total: {len(filtered_articles)}")


if __name__ == "__main__":
    main()
