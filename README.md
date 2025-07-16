# NewsHub Real-Time News Aggregator Web App
 
NewsHub is a fully featured Django web application that aggregates news from the web using NewsAPI, classifies it using NLP, and allows users to interact with content via semantic search, category filters, bookmarks, alerts, and real-time notifications.

## Features

| Feature                         | Description                                                              |
| ------------------------------- | ------------------------------------------------------------------------ |
| 📰 News Aggregation             | Pulls and stores 200+ daily articles via NewsAPI                         |
| 🧠 NLP Summarization            | Generates summary snippets using HuggingFace Transformers                |
| 📂 Category Classification      | Automatically assigns categories: Tech, Sports, Business, Politics, etc. |
| 🔍 Semantic Search + Filter     | Allows users to search articles and filter by category                   |
| 🧑‍💼 User Authentication          | Built-in sign up, login, logout via Django auth                          |
| 🔖 Bookmarks                    | Users can save/remove articles                                           |
| 🛎️ Keyword Alerts               | Users receive alerts for keywords (e.g. “AI”, “Bitcoin”)                 |
| 🧭 Personalized Recommendations | Based on user bookmarks and behavior                                     |
| ⚙️ Preferences                  | Users can choose email frequency (daily/weekly/none) and preferred hour  |
| ✉️ Email Digests                | Sends smart, personalized digests with category and keyword matches      |
| 🔔 Web Push Notifications       | Sends real-time push alerts for breaking news                            |
| 📊 User Analytics Dashboard     | Users can view activity stats and keyword engagement                     |
| 🛠️ Admin Panel                  | Manage users, articles, alerts, notifications, and analytics             |
| 🌐 Render Deployment Ready      | Configured with `render.yaml`, `Procfile`, `.env` for secure deployment  |
