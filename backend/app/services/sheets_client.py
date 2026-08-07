import json
from datetime import datetime, timezone
from typing import Dict, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SheetsWriteError(Exception):
    pass


class GoogleSheetsClient:
    def __init__(self, spreadsheet_id: str, service_account_json: str, tab_name: str = "atendimentos"):
        if not spreadsheet_id:
            raise SheetsWriteError("GOOGLE_SHEETS_SPREADSHEET_ID nao configurado")
        if not service_account_json:
            raise SheetsWriteError("GOOGLE_SERVICE_ACCOUNT_JSON nao configurado")

        self.spreadsheet_id = spreadsheet_id
        self.tab_name = tab_name

        try:
            info = json.loads(service_account_json)
            creds = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            self.service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        except Exception as exc:
            raise SheetsWriteError(f"Falha ao inicializar cliente Google Sheets: {exc}") from exc

    def append_analysis_row(self, row: Dict[str, object]) -> None:
        values: List[object] = [
            row.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            row.get("chat_id", ""),
            row.get("canal", ""),
            row.get("texto_conversa", ""),
            row.get("categoria", "Outro"),
            row.get("categoria_score", 0.0),
            row.get("sentimento_inicial", "Neutro"),
            row.get("sentimento_final", "Neutro"),
            row.get("qualidade_score", 0),
            row.get("resumo", ""),
            row.get("insights", ""),
            row.get("status_erro", ""),
        ]

        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.tab_name}!A:L",
                valueInputOption="USER_ENTERED",
                body={"values": [values]},
            ).execute()
        except HttpError as exc:
            raise SheetsWriteError(
                "Falha ao gravar na planilha. Verifique compartilhamento e nome da aba."
            ) from exc
