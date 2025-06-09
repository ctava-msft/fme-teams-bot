"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.

Description: initialize the app and listen for `message` activitys
"""

import sys
import traceback

from botbuilder.core import MemoryStorage, TurnContext
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.auth import AuthOptions, OAuthOptions, SignInResponse
from teams.state import ConversationState, TempState, TurnState, UserState
from botbuilder.schema import Activity, ActivityTypes, CardAction, ActionTypes
import logging

from utils import get_user_profile,generate_answer, get_user_group, get_citations, replace_citations, convert_html_to_markdown, convert_citations, format_answer_for_teams, build_citation_card
from feedback import handle_feedback,save_feedback_to_db
from config import Config
config = Config()

app = Application[TurnState[ConversationState, UserState, TempState]](
    ApplicationOptions(
        bot_app_id=config.APP_ID,
        storage=MemoryStorage(),
        adapter=TeamsAdapter(config),
        auth=AuthOptions(
            default="graph",
            auto=True,
            settings={
                "graph": OAuthOptions(
                    connection_name=config.OAUTH_CONNECTION_NAME,
                    title="Sign In",
                    text="please sign in",
                    end_on_invalid_message=True,
                    enable_sso=True,
                ),
            },
        ),
    )
)

auth = app.auth.get("graph")


@app.message("/signout")
async def on_sign_out(
    context: TurnContext, state: TurnState[ConversationState, UserState, TempState]
):
    await auth.sign_out(context, state)
    await context.send_activity("you are now signed out...👋")
    return False

@app.message("/login")
async def on_login(context: TurnContext, state: TurnState[ConversationState, UserState, TempState]):
    await auth.sign_in(context, state)
    await context.send_activity("Starting sign in flow.")

    name = await get_user_profile(state.temp.auth_tokens["graph"])
    await context.send_activity(f"successfully logged in! {name}")
    return False

@auth.on_sign_in_success
async def on_sign_in_success(
    context: TurnContext, state: TurnState[ConversationState, UserState, TempState]
):
    await context.send_activity("No existing login session found, Initiating login")
    await context.send_activity("successfully logged in! Please ask the question again")

    # await context.send_activity(f"token: {state.temp.auth_tokens['graph']}")


@auth.on_sign_in_failure
async def on_sign_in_failure(
    context: TurnContext,
    _state: TurnState[ConversationState, UserState, TempState],
    _res: SignInResponse,
):
    await context.send_activity("failed to login...")

@app.conversation_update("membersAdded")
async def conversation_update(context: TurnContext, state: TurnState[ConversationState, UserState, TempState]):
    # name = context.activity.from_property.name
    # await context.send_activity(
    #     f"Welcome! {name} I'm a conversational bot"
    # )
    # await context.send_activity(f"token: {state.temp.auth_tokens['graph']}")
    await context.send_activity("No existing login session found, Initiating login")
    await context.send_activity("successfully logged in! Please ask the question again")

    return True


@app.activity("message")
async def on_message(
    context: TurnContext, _state: TurnState[ConversationState, UserState, TempState]
):
    if isinstance(context.activity.value, dict) and "action" in context.activity.value and context.activity.value["action"] == "submit_feedback":
        user_id = context.activity.from_property.id
        conversation_id = context.activity.conversation.id
        feedback = context.activity.value.get("feedback", "")
        additional_feedback = context.activity.value.get("feedbackText", "")
        save_feedback_to_db(user_id, conversation_id, feedback, additional_feedback)
        await context.send_activity("Thank you for your feedback!")
        return True
    groups = await get_user_group(_state.temp.auth_tokens["graph"])
    # logging.error(f"groups are {groups}")
    answer = await generate_answer(context.activity.conversation.id, context.activity.text, context.activity.from_property.aad_object_id, context.activity.from_property.name ,groups)
    citation_file_references = get_citations(answer)
    citations = convert_citations(citation_file_references)
# reply_text = format_answer_for_teams(answer, citations)
    card_attachment = build_citation_card(answer, citations)

    # logging.info(f"reply text {reply_text}")
    reply = Activity(
        type=ActivityTypes.message,
        # text = reply_text,
        attachments=[card_attachment]
        # text =  f"payload details {context.activity.conversation.id}, {context.activity.text}, {context.activity.from_property.aad_object_id}, {context.activity.from_property.name} ,{groups},  ",
    )
    await context.send_activity(reply)
    return False


@app.error
async def on_error(context: TurnContext, error: Exception):
    logging.error(f"\n [on_turn_error] unhandled error: {error}")
    await context.send_activity("The bot encountered an error or bug.")