"""Краулер."""

import aiofiles
import asyncio

import aiohttp
import bs4
import os
from urllib.parse import urljoin


class CrawlerData:
    """Краулер data."""

    url = 'https://news.ycombinator.com/'
    path = 'result'


async def get_page(url, session):
    """Получение страницы."""
    try:
        async with session.get(url, timeout=20) as response:
            return await response.text()
    except Exception:
        return None


async def get_articles(session):
    """Получение статей."""
    page = await get_page(CrawlerData.url, session)
    soup = bs4.BeautifulSoup(page, "html.parser")
    # только 30 статей
    links = soup.select("span.titleline a")[:30]

    for link in links:
        href = urljoin(CrawlerData.url, link["href"])
        article = await get_article(href, session)
        if article is None:
            continue


async def get_article(url, session):
    """Получение статьи."""
    page = await get_page(url, session)
    soup = bs4.BeautifulSoup(page, "html.parser")
    if soup.title is None:
        return
    title = soup.title.string.replace(" ", "").split("/")[0]

    path = os.path.join(CrawlerData.path, title)
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        # если статья записана - пропускает ее
        return
    await save_article(url, session, path, soup, title)


async def save_article(url, session, path, soup, title):
    """Запись статьи."""
    article = title + '.html'
    path_file = os.path.join(path, article)
    async with aiofiles.open(path_file, 'w') as f:
        await f.write(str(soup))
    await find_comments(url, session, path, soup)


async def find_comments(url, session, path, soup):
    """Поиск комментариев."""
    comments = soup.find_all("a")
    for number, comment in enumerate(comments, 1):
        try:
            comment_url = urljoin(url, comment["href"])
        except KeyError:
            continue
        comment = await get_comment_page(comment_url, session, path, number)
        if comment is None:
            continue


async def get_comment_page(comment_url, session, path, number):
    """Получение страницы комментария."""
    page = await get_page(comment_url, session)
    if page is None:
        return
    else:
        try:
            async with session.get(comment_url, timeout=10):
                soup = bs4.BeautifulSoup(page, "html.parser")
        except Exception:
            return
    await save_comment(soup, path, number)


async def save_comment(soup, path, number):
    """Запись комментария."""
    title = 'comments'
    path = os.path.join(path, title)
    if not os.path.exists(path):
        os.makedirs(path)

    article = f'comment_{number}.html'
    path_file = os.path.join(path, article)
    async with aiofiles.open(path_file, 'w') as f:
        await f.write(str(soup))


async def main():
    """Основная функция."""
    async with aiohttp.ClientSession() as session:
        while True:
            await get_articles(session)
            await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())
