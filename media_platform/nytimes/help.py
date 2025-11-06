from typing import Dict, Optional
from bs4 import BeautifulSoup
from tools import utils


def parse_news_info(item_soup) -> Optional[Dict[str, str]]:
    """解析单条新闻信息，适配最新页面结构"""
    try:
        # 标题和链接
        # 扩展标题选择器并添加降级方案
        # 扩展标题选择器以匹配h2标签并增加类名匹配
        # 标题和链接 - 增强选择器适配最新结构
        # 更灵活的标题选择器和详细日志
        # 支持无链接标题和更广泛的选择器
        title_tag = item_soup.select_one('h1, h2, h3, h4, h5, h6, .title, .story-title, .headline, .title-text, h1 a, h2 a, h3 a, h4 a, h5 a, h6 a, .title a, a.title, .headline a, .story-heading a')
        if not title_tag:
            # 记录完整item HTML以便调试
            utils.logger.warning(f"拒绝: 未找到标题元素 - 完整HTML: {item_soup.prettify()}")
            return None
        # 提取标题文本（处理有无链接两种情况）
        title = title_tag.get_text(strip=True)
        if len(title) < 5:
            utils.logger.warning(f"拒绝: 标题过短 ({title}) - HTML片段: {item_soup.prettify()[:200]}")
            return None

        title = title_tag.get_text(strip=True)
        # 从锚点标签提取链接，支持标题内或外部链接
        link_tag = title_tag if title_tag.name == 'a' else item_soup.select_one('a, .story-link, .headline-link')
        if not link_tag or 'href' not in link_tag.attrs:
            utils.logger.warning(f"拒绝: 未找到有效链接 - HTML片段: {item_soup.prettify()[:200]}")
            return None
        link = link_tag['href']
        if not link.startswith('http'):
            link = f"https://cn.nytimes.com{link}"

        # 日期 - 扩展选择器并增加容错
        date_tag = item_soup.select_one('time, [class*="timestamp"], [class*="date"]')
        date = date_tag['datetime'] if (date_tag and 'datetime' in date_tag.attrs) else date_tag.get_text(strip=True) if date_tag else ''
        if not date:
            utils.logger.warning(f"未找到日期: {title[:30]}")

        # 摘要
        summary_tag = item_soup.select_one('p.css-1echdzn, .summary')
        summary = summary_tag.get_text(strip=True) if summary_tag else ''

        # 提取图片链接
        img_tag = item_soup.select_one('img')
        image_url = img_tag['src'] if (img_tag and img_tag.get('src')) else ''

        return {
            'title': title,
              'link': link,
            'summary': summary,
            'image_url': image_url,
            'publish_time': date,
            'source': 'nytimes_china',
            'crawl_time': utils.get_current_time_str()
        }
    except Exception as e:
        utils.logger.error(f"[parse_news_info] 解析新闻信息失败: {str(e)}")
        return None


def extract_pagination_url(soup: BeautifulSoup) -> Optional[str]:
    """提取下一页链接"""
    try:
        # 查找分页按钮
        next_page_tag = soup.find('a', text=lambda t: t and '下一页' in t)
        if next_page_tag and next_page_tag.get('href'):
            return next_page_tag['href']
        return None
    except Exception as e:
        utils.logger.error(f"[extract_pagination_url] 提取分页链接失败: {str(e)}")
        return None