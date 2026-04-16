from bs4 import BeautifulSoup


def extract_page_summary(url: str, html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    text = " ".join(node.strip() for node in soup.stripped_strings)
    return {"url": url, "title": title, "content": text}
