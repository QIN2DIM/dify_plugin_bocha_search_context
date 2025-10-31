# -*- coding: utf-8 -*-
"""
@Time    : 2025/8/4 15:15
@Author  : QIN2DIM
@GitHub  : https://github.com/QIN2DIM
@Desc    :
"""
from contextlib import suppress
from typing import List, Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field

TOOL_INVOKE_TPL = """
Here are the search results in XML format:

```xml
<search_results>
{context}
</search_results>
```
"""

TOOL_INVOKE_SEGMENT_TPL = """
<search_result index="{i}">
  <title>{title}</title>
  <url>{url}</url>
  <date>{date}</date>
  <source>{source}</source>
  <snippet>
  {snippet}
  </snippet>
</search_result>
"""

EXCLUDE_SITES = [
    "renrendoc.com",
    "csdn.net",
    "mguba.eastmoney.com",
    "gubapost.eastmoney.com",
    "guba.sina.cn",
]


class SearchRef(BaseModel):
    title: str | None = ""
    url: str | None = ""
    content: str | None = ""
    site_name: str | None = ""
    date: str | None = ""

    def model_post_init(self, context: Any, /) -> None:
        with suppress(Exception):
            if not self.site_name and self.url:
                u = urlparse(self.url)
                self.site_name = u.netloc


class InstantSearchResponse(BaseModel):
    refs: List[SearchRef] = Field(default_factory=list)
    webpage_context: str = ""
    total: int = 0

    def model_post_init(self, context: Any, /) -> None:
        self.total = len(self.refs)
        self.webpage_context = self.to_webpage_context()

    def to_webpage_context(self) -> str:
        if not self.refs:
            return ""

        webpage_segments = [
            TOOL_INVOKE_SEGMENT_TPL.format(
                i=i + 1,
                title=ref.title,
                url=ref.url,
                date=ref.date,
                source=ref.site_name,
                snippet=ref.content,
            ).strip()
            for i, ref in enumerate(self.refs)
        ]
        return TOOL_INVOKE_TPL.format(context="\n".join(webpage_segments))

    def to_dify_json_message(self) -> dict:
        if not self.refs:
            return {"search_results": [], "description": "No search results found"}
        return {"search_results": [ref.model_dump(mode="json") for ref in self.refs]}

    def to_dify_text_message(self) -> str:
        return self.webpage_context


def to_ref(response: httpx.Response) -> List[SearchRef]:
    refs = []
    result = response.json()
    contents = result.get("data", {}).get("webPages", {}).get("value", [])

    for c in contents:
        title = c.get("name", "")
        if "股吧" in title:
            continue
        refs.append(
            SearchRef(
                title=title,
                url=c.get("url", "") or c.get("displayUrl", ""),
                content=c.get("summary", "") or c.get("snippet", ""),
                site_name=c.get("siteName", ""),
                date=c.get("datePublished") or c.get("dateLastCrawled", ""),
            )
        )

    return refs
