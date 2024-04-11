from dataclasses import dataclass
from telegram.ext import ApplicationBuilder, Application, CallbackContext,ExtBot
@dataclass
class WebhookUpdate:
    user_id: int
    payload: str


class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    @classmethod
    def from_update(
        cls,
        update: object,
        application: "Application",
    ) -> "CustomContext":
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)