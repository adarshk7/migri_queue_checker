import os
from dataclasses import asdict, dataclass
from typing import Optional

import requests


MIGRI_CHATBOT_URL = "https://networkmigri.boost.ai/api/chat/v2"
QUEUE_REQUEST_MESSAGE = "My place in queue"


@dataclass
class ChatbotRequest:
    value: str
    conversation_id: Optional[str] = None

    def request_migri_chatbot(self) -> requests.Response:
        payload = asdict(self)
        payload.update(
            {
                "command": "POST",
                "type": "text",
                "client_timezone": "Europe/Helsinki",
            }
        )
        if self.conversation_id is None:
            del payload["conversation_id"]
        return requests.post(
            MIGRI_CHATBOT_URL,
            json=payload,
            headers={"User-Agent": "Python 3.10 (requests)"}
        )


@dataclass
class QueueResult:
    position: int
    slider_index: float

    @classmethod
    def from_response(cls, response: requests.Response) -> "QueueResult":
        if response.status_code != 200:
            raise ValueError(f"Non successful queue response: {response.text}")
        data = response.json()["response"]["elements"][1]["payload"]["json"]["data"]
        return cls(position=data["counterValue"], slider_index=data["linePosition"])


def get_conversation_id() -> str:
    response = ChatbotRequest(value=QUEUE_REQUEST_MESSAGE).request_migri_chatbot()
    if response.status_code != 200:
        raise ValueError(f"Non successful response: {response.text}")
    return response.json()["conversation"]["id"]


def prepare_chatbot_conversation_for_queue_number(conversation_id: str) -> None:
    """This is required so that chatbot with given conversation id is ready to take the diary number."""
    response = ChatbotRequest(
        value=QUEUE_REQUEST_MESSAGE, conversation_id=conversation_id
    ).request_migri_chatbot()
    if response.status_code != 200:
        raise ValueError(f"Non successful preparation response: {response.text}")


def main():
    diary_number = os.environ.get("MIGRI_DIARY_NUMBER")
    if diary_number is None:
        raise ValueError("Empty diary number")
    conversation_id = get_conversation_id()
    prepare_chatbot_conversation_for_queue_number(conversation_id)
    result = QueueResult.from_response(
        ChatbotRequest(
            value=diary_number, conversation_id=conversation_id
        ).request_migri_chatbot()
    )
    print(f"Queue position: {result.position} and slider index: {result.slider_index}")


if __name__ == "__main__":
    main()
