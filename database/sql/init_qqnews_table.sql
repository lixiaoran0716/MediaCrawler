-- 创建腾讯新闻表 (SQLite版本)
CREATE TABLE IF NOT EXISTS qq_news (
    id VARCHAR(32) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    url VARCHAR(512) NOT NULL UNIQUE,
    content TEXT NOT NULL,
    author VARCHAR(100),
    author_url VARCHAR(512),
    publish_time DATETIME NOT NULL,
    publish_location VARCHAR(100),
    media_account VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_qq_news_publish_time ON qq_news (publish_time);
CREATE INDEX IF NOT EXISTS idx_qq_news_author ON qq_news (author);