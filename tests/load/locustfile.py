import os
from itertools import count
from random import choice

from locust import HttpUser, between, events, task
from locust.exception import StopUser


_token_counter = count()


class BankAiStaffUser(HttpUser):
    wait_time = between(2, 8)

    def on_start(self):
        token = self._assigned_token()
        if token:
            self.headers = {"Authorization": f"Bearer {token}"}
            self.session_id = None
            self._ensure_session()
            return

        email = os.getenv("BANKAI_EMAIL")
        password = os.getenv("BANKAI_PASSWORD")
        if not email or not password:
            raise StopUser("Set BANKAI_TOKEN or BANKAI_EMAIL and BANKAI_PASSWORD before running the load test")

        response = self.client.post(
            "/api/auth/login",
            data={"username": email, "password": password},
            name="/api/auth/login",
        )
        if response.status_code != 200:
            raise StopUser(f"Login failed: HTTP {response.status_code}")

        token = response.json().get("access_token")
        if not token:
            raise StopUser("Login response did not include access_token")

        self.headers = {"Authorization": f"Bearer {token}"}
        self.session_id = None
        self._ensure_session()

    def _assigned_token(self):
        tokens = [
            token.strip()
            for token in os.getenv("BANKAI_TOKENS", "").split(",")
            if token.strip()
        ]
        if tokens:
            return tokens[next(_token_counter) % len(tokens)]
        return os.getenv("BANKAI_TOKEN")

    def _ensure_session(self):
        if self.session_id:
            return

        response = self.client.post(
            "/api/chat/sessions",
            json={"title": "Load test session"},
            headers=self.headers,
            name="/api/chat/sessions",
        )
        if response.status_code in (200, 201):
            self.session_id = response.json().get("id")

    @task(8)
    def health_check(self):
        self.client.get("/health", name="/health")

    @task(6)
    def list_chat_sessions(self):
        self.client.get(
            "/api/chat/sessions?limit=5",
            headers=self.headers,
            name="/api/chat/sessions",
        )

    @task(4)
    def list_task_templates(self):
        self.client.get(
            "/api/tasks/templates",
            headers=self.headers,
            name="/api/tasks/templates",
        )

    @task(3)
    def list_documents(self):
        self.client.get(
            "/api/documents?limit=10",
            headers=self.headers,
            name="/api/documents",
        )

    @task(1)
    def stream_general_chat(self):
        if os.getenv("BANKAI_DISABLE_STREAM", "").lower() in {"1", "true", "yes"}:
            return

        self._ensure_session()
        if not self.session_id:
            return

        prompts = [
            "Write a short customer care response for a failed transaction complaint.",
            "Summarize the steps a bank staff member should take before escalating a complaint.",
            "Draft a concise internal note for a customer follow-up call.",
        ]
        with self.client.post(
            f"/api/chat/sessions/{self.session_id}/stream",
            json={
                "message": choice(prompts),
                "language": "en",
                "mode": "summarize",
                "active_document_ids": [],
            },
            headers=self.headers,
            name="/api/chat/sessions/:id/stream",
            stream=True,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code}")
                return
            for _ in response.iter_lines():
                pass
            response.success()


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        "--scenario-note",
        default="",
        help="Optional note printed in reports to identify 25/50/100 staff runs.",
    )
