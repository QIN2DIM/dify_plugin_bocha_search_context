from collections.abc import Generator
from typing import Any

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._search_client import EXCLUDE_SITES, to_ref, InstantSearchResponse


class BochaSearchContextTool(Tool):
    BOCHA_API_URL = "https://api.bochaai.com/v1"

    @staticmethod
    def _set_params_freshness(payload: dict, tool_parameters: dict[str, Any]):
        available_freshness = ["noLimit", "oneYear", "oneMonth", "oneWeek", "oneDay"]

        payload["freshness"] = "noLimit"
        if tool_parameters.get("freshness") in available_freshness:
            payload["freshness"] = tool_parameters["freshness"]

    @staticmethod
    def _set_params_count(payload: dict, tool_parameters: dict[str, Any]):
        count = tool_parameters.get("count")
        payload["count"] = count if isinstance(count, int) and 1 <= count <= 50 else 10

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        as_agent_tool = tool_parameters.get("as_agent_tool", False)

        payload = {
            "query": tool_parameters["query"],
            "exclude": "|".join(EXCLUDE_SITES),
            "summary": True,
        }

        self._set_params_count(payload, tool_parameters)
        self._set_params_freshness(payload, tool_parameters)

        _client = httpx.Client(
            base_url=self.BOCHA_API_URL,
            timeout=60,
            headers={
                "Authorization": f"Bearer {self.runtime.credentials["BOCHA_API_KEY"]}",
                "Content-Type": "application/json",
            },
        )

        try:
            response = _client.post("/web-search", json=payload)
            isr = InstantSearchResponse(refs=to_ref(response))

            if not as_agent_tool:
                yield self.create_json_message(json=isr.to_dify_json_message())
            else:
                yield self.create_text_message(text=isr.to_dify_text_message())
        except Exception as e:
            yield self.create_text_message(f"An error occurred while invoking the tool: {str(e)}. ")
