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
import asyncio
import threading
from queue import Queue

st.set_page_config(
    page_title="News Scraper ",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)


class NewsFlowPro:
    def __init__(self):
        # Telegram Bot Configuration
        self.BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
        self.USER_IDS = st.secrets["TELEGRAM_USER_IDS"]

        # Initialize notification queue and status tracking
        if 'notification_queue' not in st.session_state:
            st.session_state.notification_queue = Queue()

        if 'notification_status' not in st.session_state:
            st.session_state.notification_status = {
                'total_sent': 0,
                'failed_sends': 0,
                'last_send_time': None,
                'send_history': []
            }

        # RSS feeds with defense and regional categories
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
            # Traditional categories
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

        # Enhanced keywords for all categories
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

    def scrape_by_category_with_notifications(self, categories, progress_bar=None, send_immediately=False):
        """Enhanced scraping with real-time notifications"""
        all_articles = []
        total_feeds = sum(len(self.feeds[cat]) for cat in categories if cat in self.feeds)
        current_feed = 0

        # Create notification container
        notification_container = st.empty()
        articles_found_container = st.empty()

        for category in categories:
            if category not in self.feeds:
                continue

            feeds_to_check = self.feeds[category]
            keywords_to_check = st.session_state.saved_searches[category]
            category_articles = []

            for feed_url in feeds_to_check:
                if progress_bar:
                    progress_bar.progress((current_feed + 1) / total_feeds)

                # Update current activity
                notification_container.info(f"🔍 Checking {category} - {feed_url.split('/')[2]}")

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
                        category_articles.append(article)
                        all_articles.append(article)

                        # Show real-time article discovery
                        articles_found_container.success(
                            f"📰 Found: {article['title'][:60]}... in {category}")

                        # Send immediately if requested
                        if send_immediately and category_articles:
                            self.send_article_immediately(article)

                current_feed += 1
                time.sleep(0.3)  # Be nice to servers

            # Show category completion with count
            if category_articles:
                notification_container.success(
                    f"✅ {category}: Found {len(category_articles)} relevant articles!")

                # Optional: Send category summary
                if send_immediately:
                    self.send_category_summary(category, len(category_articles))

        # Final notification
        notification_container.success(f"🎉 Scraping complete! Found {len(all_articles)} total articles")

        return all_articles

    def send_article_immediately(self, article):
        """Send individual article immediately when found"""
        message = self.format_article_for_telegram(article)

        for user_id in self.USER_IDS:
            success = self.send_telegram_message_with_retry(message, user_id)
            if success:
                st.session_state.notification_status['total_sent'] += 1
            else:
                st.session_state.notification_status['failed_sends'] += 1

            time.sleep(1.5)  # Increased rate limiting for individual sends

    def send_category_summary(self, category, count):
        """Send a summary when a category is completed"""
        summary_message = f"""🏷️ <b>{category.upper()} UPDATE</b>

📊 <b>Scraping Complete</b>
Found {count} new articles matching your keywords

⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
🔍 <b>Status:</b> Monitoring continues...

---"""

        for user_id in self.USER_IDS:
            self.send_telegram_message_with_retry(summary_message, user_id)
            time.sleep(1)

    def send_telegram_message_with_retry(self, message, user_id, max_retries=3):
        """Enhanced message sending with retry logic and better error handling"""
        for attempt in range(max_retries):
            try:
                url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
                data = {
                    'chat_id': user_id,
                    'text': message,
                    'disable_web_page_preview': True,
                    'parse_mode': 'HTML',
                    'disable_notification': False  # Enable notifications
                }

                response = requests.post(url, data=data, timeout=15)

                if response.status_code == 200:
                    result = response.json()
                    if result['ok']:
                        # Log successful send
                        st.session_state.notification_status['send_history'].append({
                            'user_id': user_id,
                            'time': datetime.now(),
                            'status': 'success',
                            'attempt': attempt + 1
                        })
                        return True
                    else:
                        st.warning(f"Telegram API error: {result.get('description', 'Unknown error')}")

                elif response.status_code == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', 1))
                    st.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                else:
                    print(f"HTTP {response.status_code}: {response.text}")

            except requests.exceptions.Timeout:
                st.warning(f"Timeout on attempt {attempt + 1} for user {user_id}")
            except Exception as e:
                st.warning(f"Error on attempt {attempt + 1} for user {user_id}: {e}")

            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff

        # Log failed send
        st.session_state.notification_status['send_history'].append({
            'user_id': user_id,
            'time': datetime.now(),
            'status': 'failed',
            'attempts': max_retries
        })
        return False

    def send_telegram_message(self, message, user_id):
        """Legacy method - now uses retry logic"""
        return self.send_telegram_message_with_retry(message, user_id)

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

        message = f"""{emoji} <b>{article['category'].upper()}</b>

📰 <b>{article['title']}</b>

📝 {article['summary'][:400]}{'...' if len(article['summary']) > 400 else ''}

🏷️ <b>Keywords:</b> {', '.join(article['matched_keywords'])}

📅 {article['published']}
📰 <b>Source:</b> {article['source']}

🔗 <a href="{article['link']}">Read Full Article</a>

---"""

        return message

    def scrape_by_category(self, categories, progress_bar=None):
        """Original method - kept for backward compatibility"""
        return self.scrape_by_category_with_notifications(categories, progress_bar, send_immediately=False)

    def send_news_to_telegram_enhanced(self, articles, max_articles=10, batch_size=5):
        """Enhanced news sending with better feedback and batching"""
        if not articles:
            return False, "No articles to send"

        articles_to_send = articles[:max_articles]
        total_articles = len(articles_to_send)
        total_users = len(self.USER_IDS)

        # Create progress tracking
        progress_container = st.empty()
        status_container = st.empty()

        sent_count = 0
        failed_count = 0

        # Send in batches to avoid overwhelming
        for i in range(0, total_articles, batch_size):
            batch = articles_to_send[i:i + batch_size]

            progress_container.info(f"📤 Sending batch {i // batch_size + 1}/{(total_articles - 1) // batch_size + 1}")

            for article in batch:
                message = self.format_article_for_telegram(article)

                for user_id in self.USER_IDS:
                    if self.send_telegram_message_with_retry(message, user_id):
                        sent_count += 1
                    else:
                        failed_count += 1

                    # Update status in real-time
                    status_container.success(
                        f"✅ Sent: {sent_count} | ❌ Failed: {failed_count} | 📊 Progress: {((sent_count + failed_count) / (total_articles * total_users) * 100):.1f}%"
                    )

                    time.sleep(1.2)  # Rate limiting

            # Batch delay
            if i + batch_size < total_articles:
                time.sleep(3)

        # Update session state
        st.session_state.notification_status['total_sent'] += sent_count
        st.session_state.notification_status['failed_sends'] += failed_count
        st.session_state.notification_status['last_send_time'] = datetime.now()

        success_rate = (sent_count / (sent_count + failed_count)) * 100 if (sent_count + failed_count) > 0 else 0

        final_message = f"📊 Sending Complete!\n✅ Sent: {sent_count}\n❌ Failed: {failed_count}\n📈 Success Rate: {success_rate:.1f}%"

        if success_rate > 80:
            progress_container.success(final_message)
        elif success_rate > 50:
            progress_container.warning(final_message)
        else:
            progress_container.error(final_message)

        return sent_count > 0, final_message

    def send_news_to_telegram(self, articles, max_articles=10):
        """Legacy method - now uses  version"""
        return self.send_news_to_telegram_enhanced(articles, max_articles)

    def get_bot_status(self):
        """Check bot status and recent activity"""
        try:
            url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/getMe"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                bot_info = response.json()
                if bot_info['ok']:
                    return True, bot_info['result']

            return False, "Bot not responding"
        except Exception as e:
            return False, str(e)

    def show_notification_status(self):
        """Display notification status in sidebar"""
        st.sidebar.markdown("### 📊 Notification Status")

        # Bot status check
        bot_online, bot_info = self.get_bot_status()

        if bot_online:
            st.sidebar.success(f"🤖 Bot Online: @{bot_info['username']}")
        else:
            st.sidebar.error(f"🤖 Bot Offline: {bot_info}")

        # Send statistics
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("✅ Sent", st.session_state.notification_status['total_sent'])
        with col2:
            st.metric("❌ Failed", st.session_state.notification_status['failed_sends'])

        # Last activity
        if st.session_state.notification_status['last_send_time']:
            last_send = st.session_state.notification_status['last_send_time']
            time_diff = datetime.now() - last_send
            st.sidebar.info(f"🕐 Last sent: {time_diff.seconds // 60}m ago")

        # Recent activity log
        if st.sidebar.button("📜 Show Send History"):
            history = st.session_state.notification_status['send_history'][-10:]  # Last 10
            if history:
                st.sidebar.markdown("**Recent Activity:**")
                for entry in reversed(history):
                    status_icon = "✅" if entry['status'] == 'success' else "❌"
                    time_str = entry['time'].strftime('%H:%M:%S')
                    st.sidebar.text(f"{status_icon} {time_str} User {entry['user_id']}")
            else:
                st.sidebar.info("No recent activity")


def main():
    scraper = NewsFlowPro()

    # Header
    st.title("📰 News Scraper ")
    st.markdown("** Defense & Intelligence News Scraper with Real-time Notifications**")

    # Sidebar with  notification status
    with st.sidebar:
        st.header("🔧 Control Panel")

        # Show notification status
        scraper.show_notification_status()

        st.divider()

        # Navigation
        page = st.selectbox(
            "Navigate to:",
            ["📰 News Dashboard", "⚙️ Admin Panel", "📊 Analytics", "💾 Export Data"]
        )

        st.divider()

        #  Quick Actions
        st.subheader("⚡ Quick Actions")

        # Real-time scraping toggle
        send_immediately = st.checkbox("📱 Send notifications immediately", value=False,
                                       help="Send each article as it's found (slower but real-time)")

        if st.button("🛡️ All Defense Categories", type="primary"):
            defense_cats = ['Air', 'Sea', 'Land', 'C4ISR', 'Weapons', 'Security', 'Industry']
            with st.spinner("Scraping defense news..."):
                progress_bar = st.progress(0)
                articles = scraper.scrape_by_category_with_notifications(
                    defense_cats, progress_bar, send_immediately)
                st.session_state.scraped_articles = articles
                st.session_state.last_scrape_time = datetime.now()

                if not send_immediately and articles:
                    st.success(f"Found {len(articles)} defense articles!")
                    if st.button("📤 Send All Now"):
                        scraper.send_news_to_telegram_enhanced(articles)
                elif send_immediately:
                    st.success(f"✅ Found and sent {len(articles)} articles in real-time!")
                progress_bar.empty()

        if st.button("🌍 All Middle East Regions"):
            me_cats = [cat for cat in scraper.feeds.keys() if cat.startswith('Middle East')]
            with st.spinner("Scraping Middle East news..."):
                progress_bar = st.progress(0)
                articles = scraper.scrape_by_category_with_notifications(
                    me_cats, progress_bar, send_immediately)
                st.session_state.scraped_articles = articles
                st.session_state.last_scrape_time = datetime.now()

                if not send_immediately and articles:
                    st.success(f"Found {len(articles)} Middle East articles!")
                elif send_immediately:
                    st.success(f"✅ Found and sent {len(articles)} articles in real-time!")
                progress_bar.empty()

        if st.button("🔄 Quick Scrape All"):
            all_cats = ['Military', 'Politics', 'Geography', 'Finance', 'Technology']
            with st.spinner("Scraping all news..."):
                progress_bar = st.progress(0)
                articles = scraper.scrape_by_category_with_notifications(
                    all_cats, progress_bar, send_immediately)
                st.session_state.scraped_articles = articles
                st.session_state.last_scrape_time = datetime.now()

                if not send_immediately and articles:
                    st.success(f"Found {len(articles)} articles!")
                elif send_immediately:
                    st.success(f"✅ Found and sent {len(articles)} articles in real-time!")
                progress_bar.empty()

        st.divider()

        #  Telegram controls
        st.subheader("📱 Telegram Controls")

        if st.button("📤 Send Latest ()"):
            if st.session_state.scraped_articles:
                with st.spinner("Sending with  delivery..."):
                    success, message = scraper.send_news_to_telegram_enhanced(
                        st.session_state.scraped_articles)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.warning("No articles to send. Please scrape first!")

        # Batch sending options
        col1, col2 = st.columns(2)
        with col1:
            max_articles = st.selectbox("Max articles:", [5, 10, 15, 20], index=1)
        with col2:
            batch_size = st.selectbox("Batch size:", [3, 5, 7, 10], index=1)

        if st.button("📦 Send in Batches"):
            if st.session_state.scraped_articles:
                success, message = scraper.send_news_to_telegram_enhanced(
                    st.session_state.scraped_articles, max_articles, batch_size)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")

        if st.button("🧪  Bot Test"):
            with st.spinner("Testing  bot features..."):
                bot_online, bot_info = scraper.get_bot_status()

                if bot_online:
                    test_message = f"""🤖 <b> News Scraper Test</b>

✅ <b>Bot Status:</b> Online (@{bot_info['username']})
📅 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 <b>Features:</b>  with real-time notifications and retry logic

📊 <b>Session Stats:</b>
• Messages sent: {st.session_state.notification_status['total_sent']}
• Failed sends: {st.session_state.notification_status['failed_sends']}

If you receive this message, all  features are working! 🎉"""

                    success_count = 0
                    for user_id in scraper.USER_IDS:
                        if scraper.send_telegram_message_with_retry(test_message, user_id):
                            success_count += 1

                    if success_count > 0:
                        st.success(f"✅  test successful! Sent to {success_count}/{len(scraper.USER_IDS)} users")
                    else:
                        st.error("❌  test failed. Check connection.")
                else:
                    st.error(f"❌ Bot offline: {bot_info}")

        st.divider()

        # Show  Telegram info
        with st.expander("📱  Telegram Settings"):
            st.markdown("**Bot Status:**")
            bot_online, bot_info = scraper.get_bot_status()
            if bot_online:
                st.success(f"✅ Online: @{bot_info['username']}")
                st.json(bot_info)
            else:
                st.error(f"❌ Offline: {bot_info}")

            st.markdown("** Features:**")
            st.info("""
            • Real-time article sending
            • Retry logic with exponential backoff
            • Rate limit handling
            • Batch processing
            • Send status tracking
            • Activity logging
            """)

    # Main content based on page selection
    if page == "📰 News Dashboard":
        show_enhanced_news_dashboard(scraper)
    elif page == "⚙️ Admin Panel":
        show_admin_panel(scraper)
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "💾 Export Data":
        show_export_panel()


def show_enhanced_news_dashboard(scraper):
    st.header("📰  News Dashboard")

    #  notification options
    col1, col2, col3 = st.columns(3)
    with col1:
        send_mode = st.radio("Notification Mode:",
                             ["Store Only", "Send After Scraping", "Real-time Sending"])
    with col2:
        priority_categories = st.multiselect("Priority Categories (sent first):",
                                             ['Air', 'Sea', 'Weapons', 'Security'],
                                             default=['Weapons', 'Security'])
    with col3:
        notification_delay = st.slider("Delay between notifications (seconds):", 0.5, 5.0, 1.2)

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

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍  Scrape Defense", type="primary"):
                if selected_defense:
                    with st.spinner(" scraping in progress..."):
                        progress_bar = st.progress(0)
                        send_immediately = (send_mode == "Real-time Sending")

                        articles = scraper.scrape_by_category_with_notifications(
                            selected_defense, progress_bar, send_immediately)
                        st.session_state.scraped_articles = articles
                        st.session_state.last_scrape_time = datetime.now()

                        if send_mode == "Send After Scraping" and articles:
                            st.info("📤 Now sending all articles...")
                            success, message = scraper.send_news_to_telegram_enhanced(articles)
                            if success:
                                st.success(f"✅ Scraped and sent {len(articles)} articles!")
                            else:
                                st.warning(f"⚠️ Scraped {len(articles)} but sending issues: {message}")
                        elif not send_immediately:
                            st.success(f"✅ Found {len(articles)} defense articles!")
                        progress_bar.empty()

        with col2:
            if st.button("⚡ Priority Defense"):
                priority_defense = [cat for cat in selected_defense if cat in priority_categories]
                if priority_defense:
                    with st.spinner("Scraping priority categories..."):
                        progress_bar = st.progress(0)
                        articles = scraper.scrape_by_category_with_notifications(
                            priority_defense, progress_bar, True)  # Always send immediately for priority
                        st.session_state.scraped_articles = articles
                        st.session_state.last_scrape_time = datetime.now()
                        st.success(f"🚨 Priority alert sent for {len(articles)} articles!")
                        progress_bar.empty()

        with col3:
            if st.button("📱 Send Defense Batch"):
                if st.session_state.scraped_articles:
                    defense_articles = [a for a in st.session_state.scraped_articles
                                        if a['category'] in defense_categories]
                    if defense_articles:
                        success, message = scraper.send_news_to_telegram_enhanced(defense_articles)
                        if success:
                            st.success(f"✅ Sent {len(defense_articles)} defense articles!")

    with tab2:
        st.subheader("Middle East Regional Coverage")

        me_categories = [cat for cat in scraper.feeds.keys() if cat.startswith('Middle East')]
        me_display_names = [cat.replace('Middle East - ', '') for cat in me_categories]

        selected_regions = st.multiselect(
            "Select Middle East Regions:",
            me_display_names,
            default=['Palestine', 'Iran']
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍  Regional Scrape", type="primary"):
                if selected_regions:
                    full_categories = [f"Middle East - {region}" for region in selected_regions]
                    with st.spinner(" regional scraping..."):
                        progress_bar = st.progress(0)
                        send_immediately = (send_mode == "Real-time Sending")

                        articles = scraper.scrape_by_category_with_notifications(
                            full_categories, progress_bar, send_immediately)
                        st.session_state.scraped_articles = articles
                        st.session_state.last_scrape_time = datetime.now()

                        if send_mode == "Send After Scraping" and articles:
                            success, message = scraper.send_news_to_telegram_enhanced(articles)
                        progress_bar.empty()

        with col2:
            if st.button("🔥 Breaking Regional"):
                if selected_regions:
                    full_categories = [f"Middle East - {region}" for region in selected_regions]
                    # For breaking news, always send immediately with high priority
                    with st.spinner("Checking for breaking regional news..."):
                        articles = scraper.scrape_by_category_with_notifications(
                            full_categories, None, True)
                        if articles:
                            # Send breaking news alert
                            breaking_alert = f"""🚨 <b>BREAKING REGIONAL NEWS ALERT</b>

📍 <b>Regions:</b> {', '.join(selected_regions)}
📊 <b>Articles Found:</b> {len(articles)}
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

Individual articles following...
---"""
                            for user_id in scraper.USER_IDS:
                                scraper.send_telegram_message_with_retry(breaking_alert, user_id)

                            st.success(f"🚨 Breaking news alert sent for {len(articles)} articles!")

        with col3:
            if st.button("📊 Regional Summary"):
                regional_articles = [a for a in st.session_state.scraped_articles
                                     if a['category'].startswith('Middle East')]
                if regional_articles:
                    # Create and send summary
                    summary = create_regional_summary(regional_articles)
                    for user_id in scraper.USER_IDS:
                        scraper.send_telegram_message_with_retry(summary, user_id)
                    st.success(f"📊 Regional summary sent covering {len(regional_articles)} articles!")

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
            if st.button("🔍  Traditional Scrape", type="primary"):
                if selected_traditional:
                    with st.spinner(" traditional news scraping..."):
                        progress_bar = st.progress(0)
                        send_immediately = (send_mode == "Real-time Sending")

                        articles = scraper.scrape_by_category_with_notifications(
                            selected_traditional, progress_bar, send_immediately)
                        st.session_state.scraped_articles = articles
                        st.session_state.last_scrape_time = datetime.now()

                        if send_mode == "Send After Scraping" and articles:
                            success, message = scraper.send_news_to_telegram_enhanced(articles)
                        progress_bar.empty()

        with col2:
            if st.button("📈 Send Traditional Digest"):
                traditional_articles = [a for a in st.session_state.scraped_articles
                                        if a['category'] in traditional_categories]
                if traditional_articles:
                    # Create digest format
                    digest = create_news_digest(traditional_articles)
                    for user_id in scraper.USER_IDS:
                        scraper.send_telegram_message_with_retry(digest, user_id)
                    st.success(f"📈 News digest sent with {len(traditional_articles)} articles!")

    #  article display
    if st.session_state.scraped_articles:
        st.divider()
        show_enhanced_articles_list(st.session_state.scraped_articles, scraper)


def create_regional_summary(articles):
    """Create a summary of regional articles"""
    summary = f"""🌍 <b>MIDDLE EAST REGIONAL SUMMARY</b>

📊 <b>Total Articles:</b> {len(articles)}
⏰ <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

    # Group by region
    by_region = {}
    for article in articles:
        region = article['category'].replace('Middle East - ', '')
        if region not in by_region:
            by_region[region] = []
        by_region[region].append(article)

    for region, region_articles in by_region.items():
        summary += f"""
🏛️ <b>{region.upper()}</b>
📰 {len(region_articles)} articles
🔑 Top keywords: {', '.join(set([kw for a in region_articles for kw in a.get('matched_keywords', [])])[:3])}
"""

    summary += "\n---\nDetailed articles sent separately."
    return summary


def create_news_digest(articles):
    """Create a digest format for traditional news"""
    digest = f"""📰 <b>NEWS DIGEST</b>

📊 <b>Articles:</b> {len(articles)}
⏰ <b>Generated:</b> {datetime.now().strftime('%H:%M:%S')}

"""

    # Group by category
    by_category = {}
    for article in articles:
        cat = article['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(article)

    for category, cat_articles in by_category.items():
        digest += f"""
📂 <b>{category.upper()}</b>
• {len(cat_articles)} articles
• Latest: {cat_articles[0]['title'][:50]}...

"""

    digest += "Individual articles follow..."
    return digest


def show_enhanced_articles_list(articles, scraper):
    """ article display with better controls"""
    if not articles:
        return

    st.subheader(f"📋 Found {len(articles)} Articles")

    #  filtering
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        categories_in_results = list(set([article['category'] for article in articles]))
        category_filter = st.selectbox("Filter by category:", ['All'] + categories_in_results)

    with col2:
        sources_in_results = list(set([article['source'] for article in articles]))
        source_filter = st.selectbox("Filter by source:", ['All'] + sources_in_results[:10])  # Limit for performance

    with col3:
        sort_by = st.selectbox("Sort by:", ['Recent First', 'Category', 'Source', 'Relevance'])

    with col4:
        display_limit = st.selectbox("Show articles:", [10, 20, 50, 100], index=1)

    # Apply filters
    filtered_articles = articles
    if category_filter != 'All':
        filtered_articles = [a for a in filtered_articles if a['category'] == category_filter]
    if source_filter != 'All':
        filtered_articles = [a for a in filtered_articles if a['source'] == source_filter]

    # Apply sorting
    if sort_by == 'Recent First':
        filtered_articles = sorted(filtered_articles, key=lambda x: x.get('scrape_time', datetime.min), reverse=True)
    elif sort_by == 'Category':
        filtered_articles = sorted(filtered_articles, key=lambda x: x['category'])
    elif sort_by == 'Source':
        filtered_articles = sorted(filtered_articles, key=lambda x: x['source'])
    elif sort_by == 'Relevance':
        filtered_articles = sorted(filtered_articles, key=lambda x: len(x.get('matched_keywords', [])), reverse=True)

    st.markdown(f"**Showing {min(len(filtered_articles), display_limit)} of {len(filtered_articles)} articles**")

    # Bulk actions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📤 Send Filtered Articles"):
            if filtered_articles:
                success, message = scraper.send_news_to_telegram_enhanced(filtered_articles[:display_limit])
                if success:
                    st.success(f"✅ Sent {min(len(filtered_articles), display_limit)} filtered articles!")

    with col2:
        if st.button("🎯 Send Top 5 Priority"):
            priority_articles = filtered_articles[:5]
            if priority_articles:
                for article in priority_articles:
                    message = scraper.format_article_for_telegram(article)
                    for user_id in scraper.USER_IDS:
                        scraper.send_telegram_message_with_retry(message, user_id)
                    time.sleep(0.5)  # Quick send for priority
                st.success("🎯 Priority articles sent!")

    with col3:
        if st.button("📊 Send Category Summary"):
            if category_filter != 'All':
                summary_msg = f"""📊 <b>{category_filter.upper()} SUMMARY</b>

📰 <b>Articles Found:</b> {len(filtered_articles)}
⏰ <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

🔑 <b>Key Topics:</b>
{', '.join(set([kw for a in filtered_articles for kw in a.get('matched_keywords', [])])[:5])}

Individual articles follow...
---"""
                for user_id in scraper.USER_IDS:
                    scraper.send_telegram_message_with_retry(summary_msg, user_id)
                st.success(f"📊 {category_filter} summary sent!")

    # Display articles with enhanced cards
    for i, article in enumerate(filtered_articles[:display_limit]):
        category_emojis = {
            'Air': '✈️', 'Sea': '⚓', 'Industry': '🏭', 'Land': '🎖️', 'C4ISR': '📡',
            'Weapons': '🚀', 'Security': '🔒', 'Latest Analysis': '📊', 'Company Updates': '💼',
            'Terrorism and Insurgency': '⚠️', 'Middle East - Palestine': '🇮🇱',
            'Middle East - Iran': '🇮🇷', 'Middle East - Gulf States': '🏛️',
            'Middle East - Syria/Iraq': '🏺', 'Middle East - Turkey': '🇹🇷',
            'Military': '🪖', 'Politics': '🏛️', 'Geography': '🌍', 'Finance': '💰', 'Technology': '💻'
        }

        emoji = category_emojis.get(article['category'], '📰')

        #  card with more info
        with st.expander(f"{emoji} {article['category']} | {article['title'][:80]}...", expanded=(i < 3)):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**📰 Source:** {article['source']}")
                st.markdown(f"**📅 Published:** {article['published']}")
                st.markdown(f"**📝 Summary:** {article['summary']}")

                if article.get('matched_keywords'):
                    keywords_display = ', '.join(article['matched_keywords'])
                    st.markdown(f"**🏷️ Matched Keywords:** {keywords_display}")

                # Show scrape time if available
                if article.get('scrape_time'):
                    time_ago = datetime.now() - article['scrape_time']
                    minutes_ago = time_ago.seconds // 60
                    st.markdown(f"**🕐 Found:** {minutes_ago} minutes ago")

            with col2:
                st.markdown(f"[🔗 Read Full Article]({article['link']})")

                #  send options
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("📱 Send", key=f"send_{i}"):
                        with st.spinner("Sending..."):
                            message = scraper.format_article_for_telegram(article)
                            success_count = 0
                            for user_id in scraper.USER_IDS:
                                if scraper.send_telegram_message_with_retry(message, user_id):
                                    success_count += 1

                            if success_count > 0:
                                st.success(f"✅ Sent to {success_count} users!")
                            else:
                                st.error("❌ Failed to send")

                with col_b:
                    if st.button("🚨 Priority", key=f"priority_{i}"):
                        # Send as priority with special formatting
                        priority_msg = f"""🚨 <b>PRIORITY ALERT</b>

{scraper.format_article_for_telegram(article)}

⚡ <b>Marked as Priority</b> ⚡"""

                        success_count = 0
                        for user_id in scraper.USER_IDS:
                            if scraper.send_telegram_message_with_retry(priority_msg, user_id):
                                success_count += 1

                        if success_count > 0:
                            st.success(f"🚨 Priority alert sent to {success_count} users!")


def show_admin_panel(scraper):
    st.header("⚙️  Admin Panel")

    # Tabs for different admin functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔑 Keywords", "📡 Feeds", "🗂️ Categories", "📱 Telegram", "📊 System Status"])

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
        st.subheader(" Telegram Bot Configuration")

        st.markdown("**Current Configuration:**")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Bot Status:**")
            bot_online, bot_info = scraper.get_bot_status()
            if bot_online:
                st.success(f"✅ Online: @{bot_info['username']}")
                st.metric("Bot ID", bot_info['id'])
                st.metric("Can Join Groups", bot_info.get('can_join_groups', 'N/A'))
                st.metric("Can Read All Messages", bot_info.get('can_read_all_group_messages', 'N/A'))
            else:
                st.error(f"❌ Offline: {bot_info}")

        with col2:
            st.markdown("**Notification Statistics:**")
            st.metric("Total Sent", st.session_state.notification_status['total_sent'])
            st.metric("Failed Sends", st.session_state.notification_status['failed_sends'])

            if st.session_state.notification_status['total_sent'] > 0:
                success_rate = (st.session_state.notification_status['total_sent'] /
                                (st.session_state.notification_status['total_sent'] +
                                 st.session_state.notification_status['failed_sends'])) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")

        st.markdown("**User Configuration:**")
        if scraper.USER_IDS:
            for i, user_id in enumerate(scraper.USER_IDS):
                col_user, col_test = st.columns([3, 1])
                with col_user:
                    st.code(f"User {i + 1}: {user_id}", language="text")
                with col_test:
                    if st.button("🧪 Test", key=f"test_user_{i}"):
                        test_msg = f"🧪 Test message for User {i + 1} at {datetime.now().strftime('%H:%M:%S')}"
                        if scraper.send_telegram_message_with_retry(test_msg, user_id):
                            st.success("✅ Message sent!")
                        else:
                            st.error("❌ Failed to send")
        else:
            st.error("❌ No user IDs configured")

        st.markdown("** Features:**")
        with st.expander("📖 New Features Guide"):
            st.markdown("""
            **🚀  Features:**

            **Real-time Notifications:**
            - Articles sent immediately as they're found
            - Live progress updates during scraping
            - Category completion notifications

            **Retry Logic:**
            - Automatic retry on failed sends (up to 3 attempts)
            - Exponential backoff for rate limiting
            - Detailed send status tracking

            **Batch Processing:**
            - Configurable batch sizes for bulk sending
            - Rate limiting between batches
            - Progress tracking for large sends

            **Priority Alerts:**
            - Mark articles as priority for immediate sending
            - Special formatting for urgent news
            - Breaking news alert system

            **Advanced Filtering:**
            - Send only specific categories
            - Filter by keywords or sources
            - Create custom news digests
            """)

    with tab5:
        st.subheader("System Status & Performance")

        # System metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Session Statistics:**")
            st.metric("Articles Scraped", len(st.session_state.scraped_articles))
            st.metric("Categories Active",
                      len(set([a.get('category', 'Unknown') for a in st.session_state.scraped_articles])))

            if st.session_state.last_scrape_time:
                time_since = datetime.now() - st.session_state.last_scrape_time
                st.metric("Last Scrape", f"{time_since.seconds // 60}m ago")

        with col2:
            st.markdown("**Notification Performance:**")
            total_attempts = (st.session_state.notification_status['total_sent'] +
                              st.session_state.notification_status['failed_sends'])

            if total_attempts > 0:
                success_rate = (st.session_state.notification_status['total_sent'] / total_attempts) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
                st.metric("Average per Hour", f"{(total_attempts / max(1, (datetime.now().hour + 1))):.1f}")
            else:
                st.metric("Success Rate", "No data")
                st.metric("Average per Hour", "No data")

        with col3:
            st.markdown("**Feed Health:**")
            total_feeds = sum(len(feeds) for feeds in scraper.feeds.values())
            st.metric("Total RSS Feeds", total_feeds)
            st.metric("Active Categories", len(scraper.feeds))

            # Check for problematic feeds
            if st.button("🏥 Health Check"):
                with st.spinner("Checking feed health..."):
                    problematic_feeds = []
                    working_feeds = 0

                    for category, feeds in scraper.feeds.items():
                        for feed in feeds[:3]:  # Check first 3 feeds per category for performance
                            try:
                                articles = scraper.scrape_feed(feed)
                                if articles:
                                    working_feeds += 1
                                else:
                                    problematic_feeds.append((category, feed))
                            except:
                                problematic_feeds.append((category, feed))

                    if problematic_feeds:
                        st.warning(f"⚠️ Found {len(problematic_feeds)} problematic feeds")
                        with st.expander("View Problematic Feeds"):
                            for category, feed in problematic_feeds:
                                st.text(f"❌ {category}: {feed}")
                    else:
                        st.success(f"✅ All checked feeds ({working_feeds}) are working!")

        # Recent activity log
        st.markdown("**Recent Activity:**")
        if st.session_state.notification_status['send_history']:
            recent_activity = st.session_state.notification_status['send_history'][-20:]  # Last 20

            activity_df = pd.DataFrame([
                {
                    'Time': entry['time'].strftime('%H:%M:%S'),
                    'User ID': str(entry['user_id']),
                    'Status': '✅' if entry['status'] == 'success' else '❌',
                    'Attempts': entry.get('attempt', entry.get('attempts', 1))
                }
                for entry in reversed(recent_activity)
            ])

            st.dataframe(activity_df, use_container_width=True)
        else:
            st.info("No recent activity to display")

        # System controls
        st.markdown("**System Controls:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Reset Session Stats"):
                st.session_state.scraped_articles = []
                st.session_state.notification_status = {
                    'total_sent': 0,
                    'failed_sends': 0,
                    'last_send_time': None,
                    'send_history': []
                }
                st.success("📊 Session statistics reset!")
                st.rerun()

        with col2:
            if st.button("💾 Export Logs"):
                if st.session_state.notification_status['send_history']:
                    log_data = pd.DataFrame(st.session_state.notification_status['send_history'])
                    csv_data = log_data.to_csv(index=False)
                    st.download_button(
                        "📥 Download Activity Log",
                        csv_data,
                        f"news_scraper_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
                else:
                    st.info("No logs to export")

        with col3:
            if st.button("🧹 Clear Old Logs"):
                # Keep only last 50 entries
                if len(st.session_state.notification_status['send_history']) > 50:
                    st.session_state.notification_status['send_history'] = \
                        st.session_state.notification_status['send_history'][-50:]
                    st.success("🧹 Old logs cleared!")
                else:
                    st.info("No old logs to clear")


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
        # Articles by category with enhanced styling
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
                      title='Articles by Category and Type',
                      color_discrete_map={'Defense': '#FF6B6B', 'Regional': '#4ECDC4', 'Traditional': '#45B7D1'})
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
                      title='Top 15 Keywords',
                      color='Count', color_continuous_scale='viridis')
        st.plotly_chart(fig2, use_container_width=True)

    #  content analysis
    st.subheader("📈  Content Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Defense vs Regional vs Traditional pie chart
        defense_count = len([a for a in articles if categorize_type(a['category']) == 'Defense'])
        regional_count = len([a for a in articles if categorize_type(a['category']) == 'Regional'])
        traditional_count = len([a for a in articles if categorize_type(a['category']) == 'Traditional'])

        fig_pie = px.pie(
            values=[defense_count, regional_count, traditional_count],
            names=['Defense & Security', 'Regional Middle East', 'Traditional News'],
            title='Content Distribution by Type',
            color_discrete_map={'Defense & Security': '#FF6B6B',
                                'Regional Middle East': '#4ECDC4',
                                'Traditional News': '#45B7D1'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Source diversity
        source_counts = Counter([a['source'] for a in articles])
        top_sources = dict(source_counts.most_common(10))
        df_sources = pd.DataFrame(list(top_sources.items()), columns=['Source', 'Articles'])

        fig_sources = px.bar(df_sources, x='Articles', y='Source', orientation='h',
                             title='Top 10 News Sources',
                             color='Articles', color_continuous_scale='plasma')
        st.plotly_chart(fig_sources, use_container_width=True)

    # Notification analytics
    st.subheader("📱 Notification Analytics")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_sent = st.session_state.notification_status['total_sent']
        total_failed = st.session_state.notification_status['failed_sends']
        total_attempts = total_sent + total_failed

        if total_attempts > 0:
            success_rate = (total_sent / total_attempts) * 100
            st.metric("Notification Success Rate", f"{success_rate:.1f}%")
        else:
            st.metric("Notification Success Rate", "No data")

    with col2:
        st.metric("Total Notifications Sent", total_sent)
        st.metric("Failed Notifications", total_failed)

    with col3:
        if st.session_state.notification_status['last_send_time']:
            last_send = st.session_state.notification_status['last_send_time']
            time_since = datetime.now() - last_send
            st.metric("Time Since Last Send", f"{time_since.seconds // 60}m ago")
        else:
            st.metric("Time Since Last Send", "Never")

    # Timeline analysis if scrape times are available
    if articles and any(a.get('scrape_time') for a in articles):
        st.subheader("⏰ Scraping Timeline")

        # Create timeline data
        timeline_data = []
        for article in articles:
            if article.get('scrape_time'):
                timeline_data.append({
                    'Time': article['scrape_time'],
                    'Category': article['category'],
                    'Title': article['title'][:50] + '...'
                })

        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            timeline_df['Hour'] = timeline_df['Time'].dt.hour

            # Articles per hour
            hourly_counts = timeline_df.groupby('Hour').size().reset_index(name='Articles')
            fig_timeline = px.line(hourly_counts, x='Hour', y='Articles',
                                   title='Articles Scraped by Hour',
                                   markers=True)
            st.plotly_chart(fig_timeline, use_container_width=True)


def show_export_panel():
    st.header("💾  Export Data")

    if not st.session_state.scraped_articles:
        st.info("No data to export. Please scrape some news first!")
        return

    articles = st.session_state.scraped_articles

    #  export options with advanced filtering
    st.subheader("🔧 Advanced Export Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Category filter for export
        all_categories = list(set([a['category'] for a in articles]))
        selected_export_cats = st.multiselect(
            "Select categories to export:",
            all_categories,
            default=all_categories
        )

    with col2:
        # Date range filter
        if articles and any(a.get('scrape_time') for a in articles):
            min_date = min([a['scrape_time'] for a in articles if a.get('scrape_time')]).date()
            max_date = max([a['scrape_time'] for a in articles if a.get('scrape_time')]).date()

            date_range = st.date_input(
                "Date range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        else:
            date_range = None

    with col3:
        # Export format
        export_format = st.selectbox(
            "Export format:",
            ["JSON (Full Data)", "CSV (Simplified)", "TXT (Summary Report)", "HTML (Formatted Report)"]
        )

    # Advanced filters
    with st.expander("🔍 Advanced Filters"):
        col1, col2 = st.columns(2)

        with col1:
            # Keyword filter
            all_keywords = set()
            for a in articles:
                all_keywords.update(a.get('matched_keywords', []))

            keyword_filter = st.multiselect(
                "Filter by keywords:",
                sorted(list(all_keywords)),
                help="Select specific keywords to include"
            )

        with col2:
            # Source filter
            all_sources = list(set([a['source'] for a in articles]))
            source_filter = st.multiselect(
                "Filter by sources:",
                all_sources,
                help="Select specific sources to include"
            )

    # Apply filters
    filtered_articles = articles

    # Category filter
    if selected_export_cats:
        filtered_articles = [a for a in filtered_articles if a['category'] in selected_export_cats]

    # Date filter
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_articles = [a for a in filtered_articles
                             if a.get('scrape_time') and start_date <= a['scrape_time'].date() <= end_date]

    # Keyword filter
    if keyword_filter:
        filtered_articles = [a for a in filtered_articles
                             if any(kw in a.get('matched_keywords', []) for kw in keyword_filter)]

    # Source filter
    if source_filter:
        filtered_articles = [a for a in filtered_articles if a['source'] in source_filter]

    st.info(f"Ready to export {len(filtered_articles)} articles from {len(selected_export_cats)} categories")

    #  export buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📥 Download JSON") and export_format.startswith("JSON"):
            #  JSON with metadata
            export_data = {
                'metadata': {
                    'export_time': datetime.now().isoformat(),
                    'total_articles': len(filtered_articles),
                    'categories': selected_export_cats,
                    'filters_applied': {
                        'date_range': [str(d) for d in date_range] if date_range else None,
                        'keywords': keyword_filter,
                        'sources': source_filter
                    }
                },
                'articles': filtered_articles
            }

            json_data = json.dumps(export_data, indent=2, default=str)
            st.download_button(
                label="💾 Download  JSON",
                data=json_data,
                file_name=f"enhanced_news_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    with col2:
        if st.button("📊 Download CSV") and export_format.startswith("CSV"):
            #  CSV with additional fields
            csv_data = []
            for article in filtered_articles:
                csv_data.append({
                    'Title': article['title'],
                    'Category': article['category'],
                    'Source': article['source'],
                    'Published': article['published'],
                    'Link': article['link'],
                    'Keywords': ', '.join(article.get('matched_keywords', [])),
                    'Keyword_Count': len(article.get('matched_keywords', [])),
                    'Summary': article['summary'].replace('\n', ' '),
                    'Summary_Length': len(article['summary']),
                    'Scrape_Time': article.get('scrape_time', '').isoformat() if article.get('scrape_time') else '',
                    'Category_Type': categorize_type(article['category'])
                })

            df = pd.DataFrame(csv_data)
            csv_string = df.to_csv(index=False)
            st.download_button(
                label="💾 Download  CSV",
                data=csv_string,
                file_name=f"enhanced_news_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    with col3:
        if st.button("📄 Generate Report"):
            #  summary report
            report = f"""#  News Intelligence Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
- **Total Articles Analyzed:** {len(filtered_articles)}
- **Categories Covered:** {len(selected_export_cats)}
- **Unique Sources:** {len(set([a['source'] for a in filtered_articles]))}
- **Time Period:** {date_range[0] if date_range else 'All time'} to {date_range[1] if date_range and len(date_range) > 1 else 'present'}

## Category Breakdown
"""
            category_counts = Counter([a['category'] for a in filtered_articles])
            for cat, count in category_counts.most_common():
                percentage = (count / len(filtered_articles)) * 100
                report += f"- **{cat}:** {count} articles ({percentage:.1f}%)\n"

            report += "\n## Top Keywords Analysis\n"
            all_keywords = []
            for a in filtered_articles:
                all_keywords.extend(a.get('matched_keywords', []))
            keyword_counts = Counter(all_keywords)
            for kw, count in keyword_counts.most_common(15):
                report += f"- **{kw}:** {count} mentions\n"

            report += "\n## Source Analysis\n"
            source_counts = Counter([a['source'] for a in filtered_articles])
            for source, count in source_counts.most_common(10):
                report += f"- **{source}:** {count} articles\n"

            # Category type analysis
            report += "\n## Content Type Distribution\n"
            type_counts = Counter([categorize_type(a['category']) for a in filtered_articles])
            for content_type, count in type_counts.items():
                percentage = (count / len(filtered_articles)) * 100
                report += f"- **{content_type}:** {count} articles ({percentage:.1f}%)\n"

            st.download_button(
                label="📋 Download  Report",
                data=report,
                file_name=f"enhanced_news_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )

    with col4:
        if st.button("🌐 Generate HTML"):
            # Create HTML report
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>News Intelligence Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .article {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }}
        .category {{ background-color: #3498db; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }}
        .keywords {{ color: #7f8c8d; font-style: italic; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ background-color: #ecf0f1; padding: 15px; border-radius: 8px; text-align: center; flex: 1; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 News Intelligence Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="stats">
            <div class="stat-box">
                <h3>{len(filtered_articles)}</h3>
                <p>Total Articles</p>
            </div>
            <div class="stat-box">
                <h3>{len(set([a['category'] for a in filtered_articles]))}</h3>
                <p>Categories</p>
            </div>
            <div class="stat-box">
                <h3>{len(set([a['source'] for a in filtered_articles]))}</h3>
                <p>Sources</p>
            </div>
        </div>

        <h2>📊 Recent Articles</h2>
"""

            for article in filtered_articles[:20]:  # Show first 20 articles
                html_content += f"""
        <div class="article">
            <h3>{article['title']}</h3>
            <p><span class="category">{article['category']}</span> | <strong>{article['source']}</strong> | {article['published']}</p>
            <p>{article['summary']}</p>
            <p class="keywords">Keywords: {', '.join(article.get('matched_keywords', []))}</p>
            <a href="{article['link']}" target="_blank">Read Full Article →</a>
        </div>
"""

            html_content += """
    </div>
</body>
</html>
"""

            st.download_button(
                label="🌐 Download HTML Report",
                data=html_content,
                file_name=f"news_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html"
            )

    #  preview
    st.subheader("👀 Export Preview")

    # Show sample data with enhanced formatting
    if filtered_articles:
        preview_df = pd.DataFrame([
            {
                'Title': a['title'][:60] + '...' if len(a['title']) > 60 else a['title'],
                'Category': a['category'],
                'Type': categorize_type(a['category']),
                'Source': a['source'],
                'Keywords': ', '.join(a.get('matched_keywords', [])[:3]),
                'Keyword Count': len(a.get('matched_keywords', [])),
                'Summary Length': len(a['summary'])
            }
            for a in filtered_articles[:20]
        ])
        st.dataframe(preview_df, use_container_width=True)

        if len(filtered_articles) > 20:
            st.info(f"Showing first 20 articles. Total filtered: {len(filtered_articles)}")

        # Export statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_keywords = sum(len(a.get('matched_keywords', [])) for a in filtered_articles) / len(filtered_articles)
            st.metric("Avg Keywords per Article", f"{avg_keywords:.1f}")
        with col2:
            avg_summary_length = sum(len(a['summary']) for a in filtered_articles) / len(filtered_articles)
            st.metric("Avg Summary Length", f"{avg_summary_length:.0f} chars")
        with col3:
            unique_domains = len(set([a['link'].split('/')[2] for a in filtered_articles if 'http' in a['link']]))
            st.metric("Unique Domains", unique_domains)


def categorize_type(cat):
    """Helper function to categorize article types"""
    if cat.startswith('Middle East'):
        return 'Regional'
    elif cat in ['Air', 'Sea', 'Land', 'C4ISR', 'Weapons', 'Security', 'Industry',
                 'Latest Analysis', 'Company Updates', 'Terrorism and Insurgency']:
        return 'Defense'
    else:
        return 'Traditional'


if __name__ == "__main__":
    main()
