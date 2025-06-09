import os
import aiohttp
import requests
import re
from typing import List, Dict
import logging 
from urllib.parse import quote
from botbuilder.schema import Attachment

async def get_user_profile(token: str) -> dict:
    graph_url = "https://graph.microsoft.com/v1.0/me"
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(graph_url, headers=headers) as response:
            if response.status == 200:
                user_data = await response.json()
                display_name = user_data.get("displayName", "Unknown User")
                return display_name
            else:
                return "Unknown User"

async def get_user_group(token: str) -> dict:
    graph_headers = {'Authorization': f'Bearer {token}'}
    graph_url = 'https://graph.microsoft.com/v1.0/me/memberOf'
    # graph_response = requests.get(graph_url, headers=graph_headers)

    async with aiohttp.ClientSession() as session:
        async with session.get(graph_url, headers=graph_headers) as response:
            if response.status == 200:
                group_data = await response.json()
                groups = [group.get('displayName', 'missing-group-read-all-permission') for group in group_data.get('value', [])]
                # display_name = user_data.get("displayName", "Unknown User")
                return groups
            else:
                return "Unknown User"


async def generate_answer(conversation_id:str, user_query: str, client_principal_id, client_principal_name, client_group_names, is_work_mode: bool = True) -> str:
    try:
        url = os.environ.get("ORC_URL")
        function_key = os.environ.get("FUNCTION_KEY")
        payload = {
            "conversation_id": conversation_id,
            "question": user_query,
            "client_principal_id": client_principal_id,
            "client_principal_name": client_principal_name,
            "client_group_names": client_group_names,
            "is_work_mode": is_work_mode
        }
        headers = {
            'Content-Type': 'application/json',
            'x-functions-key': function_key  
        }       
        response = requests.post(url, headers=headers, json=payload)
    
        if response.status_code == 200:
            data = response.json()
            return data.get("answer", "No answer provided.")
        else:
            return f"Error: API call failed with status {response.status_code}"
    except Exception as e:
        response = {
            "answer": f"Error in application backend.{e}",
            "thoughts": "",
            "conversation_id": conversation_id
        }
        return response["answer"]


def get_citations(content: str) -> list[str]:
    matches = re.findall(r'\[(.*?)\]', content)
    if matches:
        unique_matches = list(set(matches))
        return unique_matches
    return []

def convert_html_to_markdown(html: str) -> str:
    # Convert <strong> tags to **bold**
    markdown = re.sub(r'<strong>(.*?)</strong>', r'**\1**', html, flags=re.DOTALL)

    # Convert <em> tags to *italic*
    markdown = re.sub(r'<em>(.*?)</em>', r'*\1*', markdown, flags=re.DOTALL)

    return markdown

def replace_citations(citations: list[str], content: str) -> str:
    for citation in citations:
        escaped_citation = re.escape(citation)
        pattern = re.compile(rf'\[{escaped_citation}\]')
        content = pattern.sub('', content)
    
    # Optionally remove extra spaces that may result from citation removal
    content = re.sub(r'\s{2,}', ' ', content)

    return content.strip()



def convert_citations(citations: List[str]) -> List[Dict[str, str]]:
    app_backend_endpoint = os.getenv("APP_BACKEND_ENDPOINT", "http://localhost:8000/")  # Default fallback
    return [
        {
            "filename": citation,
            "url": f"{app_backend_endpoint}/sites/FMC-BI/BI/bisup/Shared%20Documents/GPT_RAG_2/{quote(citation)}"
        }
        for citation in citations
    ]

def build_citation_card(answer_text: str, citations: List[Dict[str, str]], is_work_mode: bool = True) -> Attachment:
    actions = [
        {
            "type": "Action.OpenUrl",
            "title": citation["filename"],
            "url": citation["url"]
        }
        for citation in citations
    ]

    card = {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": answer_text,
                "wrap": True
            },
            {
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "Mode:",
                        "weight": "Bolder",
                        "size": "Small"
                    },
                    {
                        "type": "Input.Toggle",
                        "id": "workModeToggle",
                        "title": "Work Mode",
                        "value": str(is_work_mode).lower(),
                        "valueOn": "true",
                        "valueOff": "false"
                    },
                    {
                        "type": "TextBlock",
                        "text": "Work Mode: Professional responses | Chat Mode: Casual conversation",
                        "size": "Small",
                        "color": "Accent",
                        "wrap": True
                    }
                ]
            }
        ],
        "actions": actions + [
            {
                "type": "Action.Submit",
                "title": "👍 Helpful",
                "data": {"action": "feedback", "feedback": "helpful", "is_work_mode": is_work_mode}
            },
            {
                "type": "Action.Submit",
                "title": "👎 Not Helpful",
                "data": {"action": "feedback", "feedback": "not_helpful", "is_work_mode": is_work_mode}
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card
    )
 


def format_answer_for_teams(raw_answer: str, citation_file_references: list[dict]) -> str:
    """
    Format a raw answer string and its citation file references into Teams-compatible markdown.
    
    Args:
        raw_answer (str): The raw answer containing Markdown, citation markers like [1], [source], and headings.
        citation_file_references (list of dict): List of dicts with 'filename' and 'url'.
    
    Returns:
        str: A markdown-formatted string suitable for Microsoft Teams.
    """

    # 1. Remove all citation markers like [1], [source], etc.
    cleaned_answer = re.sub(r"\[[^\]]+\]", "", raw_answer)
    if citation_file_references:
        citation_lines = "\n".join(
            f" [{ref['filename']}]({ref['url']})" for ref in citation_file_references
        )
        sources_section = f"\n\n**Sources:**\n\n{citation_lines}"
    else:
        sources_section = ""

    # 5. Combine cleaned answer and sources
    final_markdown = f"{cleaned_answer}{sources_section}"

    return final_markdown

if __name__ == "__main__":
    import asyncio
    loop = asyncio.run(generate_answer("123", "Hi good morning?"))
    print(loop)