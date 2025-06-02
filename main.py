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
    page_title="News Scrapper",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)


class NewsFlowPro:
    def __init__(self):
        # Telegram Bot Configuration
        self.BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
        self.USER_IDS = st.secrets["TELEGRAM_USER_IDS"]

        # RSS feeds for different categories
        self.feeds = {
            'Military': [
                'https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=10',
                'https://www.militarytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml',
                'https://www.navytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml',
                'https://www.armytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml',
                'http://feeds.reuters.com/reuters/worldNews',
                'https://www.stripes.com/rss/news.rss'
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
                'https://www.usgs.gov/rss/home.xml',
                'https://earthobservatory.nasa.gov/rss/earth_news.xml',
                'https://www.noaa.gov/news/rss/news.xml',
                'https://www.nature.com/nature/current_issue/rss'
            ],
            'Finance': [
                'https://feeds.finance.yahoo.com/rss/2.0/headline',
                'http://feeds.reuters.com/reuters/businessNews',
                'https://www.marketwatch.com/rss/topstories'
            ],
            'Technology': [
                'http://feeds.reuters.com/reuters/technologyNews',
                'https://techcrunch.com/feed/',
                'https://www.theverge.com/rss/index.xml',
                'https://feeds.arstechnica.com/arstechnica/index'
            ]
        }

        # Initialize session state for keywords
        if 'saved_searches' not in st.session_state:
            st.session_state.saved_searches = {
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
        total_feeds = sum(len(self.feeds[cat]) for cat in categories)
        current_feed = 0

        for category in categories:
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
        """Send scraped news articles to Telegram users (without summary)"""
        if not articles:
            return False, "No articles to send"

        # Limit articles to prevent message spam
        articles_to_send = articles[:max_articles]

        success_count = 0
        total_messages = len(self.USER_IDS) * len(articles_to_send)

        for user_id in self.USER_IDS:
            # Send individual articles directly (no summary message)
            for i, article in enumerate(articles_to_send):
                message = self.format_article_for_telegram(article)

                if self.send_telegram_message(message, user_id):
                    success_count += 1

                time.sleep(1)  # Rate limiting between messages

        return success_count > 0, f"Sent {success_count}/{total_messages} messages successfully"


def main():
    scraper = NewsFlowPro()

    # Header
    st.title("📰 News Scrapper")
    st.markdown("**Advanced News Scraper with Smart Keyword Filtering**")

    # Sidebar
    with st.sidebar:
        st.header("🔧 Control Panel")

        # Navigation
        page = st.selectbox(
            "Navigate to:",
            ["📰 News Dashboard", "⚙️ Admin Panel", "📊 Analytics", "💾 Export Data"]
        )

        st.divider()

        # Quick scrape button
        if st.button("🔄 Quick Scrape All", type="primary"):
            with st.spinner("Scraping latest news..."):
                progress_bar = st.progress(0)
                articles = scraper.scrape_by_category(['Military', 'Politics', 'Geography', 'Finance', 'Technology'],
                                                      progress_bar)
                st.session_state.scraped_articles = articles
                st.session_state.last_scrape_time = datetime.now()
                st.success(f"Found {len(articles)} articles!")
                progress_bar.empty()

        # Scrape and Send button
        if st.button("📱 Scrape & Send to Telegram", type="secondary"):
            with st.spinner("Scraping news and sending to Telegram..."):
                progress_bar = st.progress(0)

                # Scrape articles
                articles = scraper.scrape_by_category(['Military', 'Politics', 'Geography', 'Finance', 'Technology'],
                                                      progress_bar)
                st.session_state.scraped_articles = articles
                st.session_state.last_scrape_time = datetime.now()

                progress_bar.progress(0.7)

                if articles:
                    # Send to Telegram
                    success, message = scraper.send_news_to_telegram(articles)
                    progress_bar.progress(1.0)

                    if success:
                        st.success(f"✅ Found {len(articles)} articles and sent to Telegram! {message}")
                    else:
                        st.error(f"❌ Failed to send to Telegram: {message}")
                else:
                    st.warning("No articles found to send")

                progress_bar.empty()

        # Telegram test button
        if st.button("🧪 Test Telegram Bot"):
            with st.spinner("Testing Telegram connection..."):
                test_message = f"""🤖 <b>NewsFlow Pro Bot Test</b>

✅ Bot Status: Online
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

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
            st.code(scraper.BOT_TOKEN[:20] + "...", language="text")
            st.markdown("**User IDs:**")
            for user_id in scraper.USER_IDS:
                st.code(str(user_id), language="text")

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
    st.header("📰 Latest News")

    # Controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_categories = st.multiselect(
            "Select Categories:",
            ['Military', 'Politics', 'Geography', 'Finance', 'Technology'],
            default=['Military', 'Politics', 'Geography', 'Finance', 'Technology']
        )

    with col2:
        if st.button("🔍 Scrape Selected"):
            if selected_categories:
                with st.spinner("Scraping news..."):
                    progress_bar = st.progress(0)
                    articles = scraper.scrape_by_category(selected_categories, progress_bar)
                    st.session_state.scraped_articles = articles
                    st.session_state.last_scrape_time = datetime.now()
                    st.success(f"Found {len(articles)} articles!")
                    progress_bar.empty()
            else:
                st.warning("Please select at least one category!")

    with col3:
        # New: Scrape & Send Selected button
        if st.button("📱 Scrape & Send Selected"):
            if selected_categories:
                with st.spinner("Scraping and sending to Telegram..."):
                    progress_bar = st.progress(0)

                    # Scrape selected categories
                    articles = scraper.scrape_by_category(selected_categories, progress_bar)
                    st.session_state.scraped_articles = articles
                    st.session_state.last_scrape_time = datetime.now()

                    progress_bar.progress(0.7)

                    if articles:
                        # Send to Telegram
                        success, message = scraper.send_news_to_telegram(articles)
                        progress_bar.progress(1.0)

                        if success:
                            st.success(f"✅ Found {len(articles)} articles and sent to Telegram! {message}")
                        else:
                            st.error(f"❌ Failed to send to Telegram: {message}")
                    else:
                        st.warning("No articles found to send")

                    progress_bar.empty()
            else:
                st.warning("Please select at least one category!")

    with col4:
        if st.session_state.last_scrape_time:
            st.info(f"Last scraped: {st.session_state.last_scrape_time.strftime('%H:%M:%S')}")

    # Send to Telegram button (for current results)
    if st.session_state.scraped_articles:
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("📱 Send Current Results to Telegram", type="secondary"):
                with st.spinner("Sending to Telegram..."):
                    success, message = scraper.send_news_to_telegram(st.session_state.scraped_articles)
                    if success:
                        st.success(f"✅ Sent to Telegram! {message}")
                    else:
                        st.error(f"❌ Failed to send: {message}")

    # Display articles
    if st.session_state.scraped_articles:
        st.subheader(f"📋 Found {len(st.session_state.scraped_articles)} Articles")

        # Category filter
        categories_in_results = list(set([article['category'] for article in st.session_state.scraped_articles]))
        category_filter = st.selectbox("Filter by category:", ['All'] + categories_in_results)

        # Filter articles
        if category_filter == 'All':
            filtered_articles = st.session_state.scraped_articles
        else:
            filtered_articles = [a for a in st.session_state.scraped_articles if a['category'] == category_filter]

        # Display articles in cards
        for i, article in enumerate(filtered_articles[:20]):  # Limit to 20 for performance
            with st.expander(f"🏷️ {article['category']} | {article['title'][:80]}..."):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Source:** {article['source']}")
                    st.markdown(f"**Published:** {article['published']}")
                    st.markdown(f"**Summary:** {article['summary']}")
                    st.markdown(f"**Matched Keywords:** {', '.join(article['matched_keywords'])}")
                with col2:
                    st.markdown(f"[🔗 Read Full Article]({article['link']})")

                    # Category badge
                    if article['category'] == 'Military':
                        st.markdown("🪖 **Military**")
                    elif article['category'] == 'Politics':
                        st.markdown("🏛️ **Politics**")
                    elif article['category'] == 'Geography':
                        st.markdown("🌍 **Geography**")
                    elif article['category'] == 'Finance':
                        st.markdown("💰 **Finance**")
                    else:
                        st.markdown("💻 **Technology**")
    else:
        st.info("👆 Click 'Quick Scrape All' or 'Scrape Selected' to get started!")


def show_admin_panel(scraper):
    st.header("⚙️ Admin Panel")

    # Tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["🔑 Manage Keywords", "📡 Manage Feeds", "🗂️ Categories"])

    with tab1:
        st.subheader("Keyword Management")

        # Select category to manage
        selected_cat = st.selectbox("Select Category to Manage:",
                                    ['Military', 'Politics', 'Geography', 'Finance', 'Technology'])

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

        feed_cat = st.selectbox("Select Category for Feeds:",
                                ['Military', 'Politics', 'Geography', 'Finance', 'Technology'], key="feed_cat")

        st.markdown("**Current RSS Feeds:**")
        for i, feed in enumerate(scraper.feeds[feed_cat]):
            col_feed, col_test = st.columns([4, 1])
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

        # Add new feed
        st.markdown("**Add New RSS Feed:**")
        new_feed = st.text_input("Enter RSS feed URL:")
        if st.button("🔗 Add Feed") and new_feed:
            # Simple validation
            if new_feed.startswith('http') and ('rss' in new_feed or 'feed' in new_feed):
                scraper.feeds[feed_cat].append(new_feed)
                st.success("Feed added!")
                st.rerun()
            else:
                st.error("Please enter a valid RSS feed URL")

    with tab3:
        st.subheader("Category Overview")

        # Summary stats
        for category in ['Military', 'Politics', 'Geography', 'Finance', 'Technology']:
            with st.expander(f"📁 {category}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Keywords", len(st.session_state.saved_searches[category]))
                    st.metric("RSS Feeds", len(scraper.feeds[category]))
                with col2:
                    # Show recent articles count
                    recent_articles = [a for a in st.session_state.scraped_articles if a.get('category') == category]
                    st.metric("Recent Articles", len(recent_articles))


def show_analytics():
    st.header("📊 Analytics Dashboard")

    if not st.session_state.scraped_articles:
        st.info("No data available. Please scrape some news first!")
        return

    articles = st.session_state.scraped_articles

    # Basic stats
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
            keywords.extend(a['matched_keywords'])
        st.metric("Total Keyword Matches", len(keywords))

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        # Articles by category
        category_counts = Counter([a['category'] for a in articles])
        df_cat = pd.DataFrame(list(category_counts.items()), columns=['Category', 'Count'])
        fig1 = px.pie(df_cat, values='Count', names='Category', title='Articles by Category')
        st.plotly_chart(fig1)

    with col2:
        # Top keywords
        all_keywords = []
        for a in articles:
            all_keywords.extend(a['matched_keywords'])
        keyword_counts = Counter(all_keywords)
        top_keywords = dict(keyword_counts.most_common(10))
        df_kw = pd.DataFrame(list(top_keywords.items()), columns=['Keyword', 'Count'])
        fig2 = px.bar(df_kw, x='Keyword', y='Count', title='Top 10 Keywords')
        st.plotly_chart(fig2)


def show_export_panel():
    st.header("💾 Export Data")

    if not st.session_state.scraped_articles:
        st.info("No data to export. Please scrape some news first!")
        return

    articles = st.session_state.scraped_articles

    # Export options
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Export as JSON")
        if st.button("⬇️ Download JSON"):
            json_data = json.dumps(articles, indent=2, default=str)
            st.download_button(
                label="📥 Download JSON File",
                data=json_data,
                file_name=f"newsflow_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    with col2:
        st.subheader("📊 Export as CSV")
        if st.button("⬇️ Download CSV"):
            # Flatten data for CSV
            csv_data = []
            for article in articles:
                csv_data.append({
                    'Title': article['title'],
                    'Category': article['category'],
                    'Source': article['source'],
                    'Published': article['published'],
                    'Link': article['link'],
                    'Keywords': ', '.join(article['matched_keywords']),
                    'Summary': article['summary'].replace('\n', ' ')
                })

            df = pd.DataFrame(csv_data)
            csv_string = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV File",
                data=csv_string,
                file_name=f"newsflow_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    # Preview data
    st.subheader("👀 Data Preview")
    df_preview = pd.DataFrame([
        {
            'Title': a['title'][:50] + '...',
            'Category': a['category'],
            'Source': a['source'],
            'Keywords': ', '.join(a['matched_keywords'][:3])
        }
        for a in articles[:10]
    ])
    st.dataframe(df_preview, use_container_width=True)


if __name__ == "__main__":
    main()