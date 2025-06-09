from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ActivityTypes,  Attachment

def save_feedback_to_db(user_id, conversation_id, feedback, additional_feedback):
    # Save feedback to database
    pass

async def handle_feedback(context: TurnContext, feedback: str, is_work_mode: bool = True):
    """Send an Adaptive Card with a text input box for feedback."""
    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            {
                "type": "TextBlock",
                "text": "Please provide additional feedback:",
                "wrap": True
            },
            {
                "type": "Input.Text",
                "id": "feedbackText",
                "placeholder": "Type your feedback here..."
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
                    }
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Submit Feedback",
                "data": {"action": "submit_feedback", "feedback": feedback}
            }
        ]
    }

    feedback_activity = Activity(
        type=ActivityTypes.message,
        attachments=[Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=adaptive_card
        )]
    )
    await context.send_activity(feedback_activity)


