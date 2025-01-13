from typing import cast

import tweepy
from tweepy.client import Response

from backend.blocks.twitter._auth import (
    TEST_CREDENTIALS,
    TEST_CREDENTIALS_INPUT,
    TwitterCredentials,
    TwitterCredentialsField,
    TwitterCredentialsInput,
)
from backend.blocks.twitter._builders import UserExpansionsBuilder
from backend.blocks.twitter._serializer import IncludesSerializer
from backend.blocks.twitter._types import (
    TweetFieldsFilter,
    TweetUserFieldsFilter,
    UserExpansionInputs,
    UserExpansionsFilter,
)
from backend.blocks.twitter.tweepy_exceptions import handle_tweepy_exception
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class TwitterUnblockUserBlock(Block):
    """
    Unblock a specific user on Twitter. The request succeeds with no action when the user sends a request to a user they're not blocking or have already unblocked.
    """

    class Input(BlockSchema):
        credentials: TwitterCredentialsInput = TwitterCredentialsField(
            ["block.write", "users.read", "offline.access"]
        )

        target_user_id: str = SchemaField(
            description="The user ID of the user that you would like to unblock",
            placeholder="Enter target user ID",
        )

    class Output(BlockSchema):
        success: bool = SchemaField(description="Whether the unblock was successful")
        error: str = SchemaField(description="Error message if the request failed")

    def __init__(self):
        super().__init__(
            id="0f1b6570-a631-11ef-a3ea-230cbe9650dd",
            description="This block unblocks a specific user on Twitter.",
            categories={BlockCategory.SOCIAL},
            input_schema=TwitterUnblockUserBlock.Input,
            output_schema=TwitterUnblockUserBlock.Output,
            test_input={
                "target_user_id": "12345",
                "credentials": TEST_CREDENTIALS_INPUT,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[
                ("success", True),
            ],
            test_mock={"unblock_user": lambda *args, **kwargs: True},
        )

    @staticmethod
    def unblock_user(credentials: TwitterCredentials, target_user_id: str):
        try:
            client = tweepy.Client(
                bearer_token=credentials.access_token.get_secret_value()
            )

            client.unblock(target_user_id=target_user_id, user_auth=False)

            return True

        except tweepy.TweepyException:
            raise

    def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            success = self.unblock_user(credentials, input_data.target_user_id)
            yield "success", success
        except Exception as e:
            yield "error", handle_tweepy_exception(e)


class TwitterGetBlockedUsersBlock(Block):
    """
    Get a list of users who are blocked by the authenticating user
    """

    class Input(UserExpansionInputs):
        credentials: TwitterCredentialsInput = TwitterCredentialsField(
            ["users.read", "offline.access", "block.read"]
        )

        max_results: int | None = SchemaField(
            description="Maximum number of results to return (1-1000, default 100)",
            placeholder="Enter max results",
            default=10,
            advanced=True,
        )

        pagination_token: str | None = SchemaField(
            description="Token for retrieving next/previous page of results",
            placeholder="Enter pagination token",
            default="",
            advanced=True,
        )

    class Output(BlockSchema):
        user_ids: list[str] = SchemaField(description="List of blocked user IDs")
        usernames_: list[str] = SchemaField(description="List of blocked usernames")
        included: dict = SchemaField(
            description="Additional data requested via expansions"
        )
        meta: dict = SchemaField(description="Metadata including pagination info")
        next_token: str = SchemaField(description="Next token for pagination")
        error: str = SchemaField(description="Error message if the request failed")

    def __init__(self):
        super().__init__(
            id="05f409e8-a631-11ef-ae89-93de863ee30d",
            description="This block retrieves a list of users blocked by the authenticating user.",
            categories={BlockCategory.SOCIAL},
            input_schema=TwitterGetBlockedUsersBlock.Input,
            output_schema=TwitterGetBlockedUsersBlock.Output,
            test_input={
                "max_results": 10,
                "pagination_token": "",
                "credentials": TEST_CREDENTIALS_INPUT,
                "expansions": None,
                "tweet_fields": None,
                "user_fields": None,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[
                ("user_ids", ["12345", "67890"]),
                ("usernames_", ["testuser1", "testuser2"]),
            ],
            test_mock={
                "get_blocked_users": lambda *args, **kwargs: (
                    {},  # included
                    {},  # meta
                    ["12345", "67890"],  # user_ids
                    ["testuser1", "testuser2"],  # usernames
                    None,  # next_token
                )
            },
        )

    @staticmethod
    def get_blocked_users(
        credentials: TwitterCredentials,
        max_results: int | None,
        pagination_token: str | None,
        expansions: UserExpansionsFilter | None,
        tweet_fields: TweetFieldsFilter | None,
        user_fields: TweetUserFieldsFilter | None,
    ):
        try:
            client = tweepy.Client(
                bearer_token=credentials.access_token.get_secret_value()
            )

            params = {
                "max_results": max_results,
                "pagination_token": (
                    None if pagination_token == "" else pagination_token
                ),
                "user_auth": False,
            }

            params = (
                UserExpansionsBuilder(params)
                .add_expansions(expansions)
                .add_tweet_fields(tweet_fields)
                .add_user_fields(user_fields)
                .build()
            )

            response = cast(Response, client.get_blocked(**params))

            meta = {}
            user_ids = []
            usernames = []
            next_token = None

            included = IncludesSerializer.serialize(response.includes)

            if response.data:
                for user in response.data:
                    user_ids.append(str(user.id))
                    usernames.append(user.username)

            if response.meta:
                meta = response.meta
                if "next_token" in meta:
                    next_token = meta["next_token"]

            if user_ids and usernames:
                return included, meta, user_ids, usernames, next_token
            else:
                raise tweepy.TweepyException("No blocked users found")

        except tweepy.TweepyException:
            raise

    def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            included, meta, user_ids, usernames, next_token = self.get_blocked_users(
                credentials,
                input_data.max_results,
                input_data.pagination_token,
                input_data.expansions,
                input_data.tweet_fields,
                input_data.user_fields,
            )
            if user_ids:
                yield "user_ids", user_ids
            if usernames:
                yield "usernames_", usernames
            if included:
                yield "included", included
            if meta:
                yield "meta", meta
            if next_token:
                yield "next_token", next_token
        except Exception as e:
            yield "error", handle_tweepy_exception(e)


class TwitterBlockUserBlock(Block):
    """
    Block a specific user on Twitter
    """

    class Input(BlockSchema):
        credentials: TwitterCredentialsInput = TwitterCredentialsField(
            ["block.write", "users.read", "offline.access"]
        )

        target_user_id: str = SchemaField(
            description="The user ID of the user that you would like to block",
            placeholder="Enter target user ID",
        )

    class Output(BlockSchema):
        success: bool = SchemaField(description="Whether the block was successful")
        error: str = SchemaField(description="Error message if the request failed")

    def __init__(self):
        super().__init__(
            id="fc258b94-a630-11ef-abc3-df050b75b816",
            description="This block blocks a specific user on Twitter.",
            categories={BlockCategory.SOCIAL},
            input_schema=TwitterBlockUserBlock.Input,
            output_schema=TwitterBlockUserBlock.Output,
            test_input={
                "target_user_id": "12345",
                "credentials": TEST_CREDENTIALS_INPUT,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[
                ("success", True),
            ],
            test_mock={"block_user": lambda *args, **kwargs: True},
        )

    @staticmethod
    def block_user(credentials: TwitterCredentials, target_user_id: str):
        try:
            client = tweepy.Client(
                bearer_token=credentials.access_token.get_secret_value()
            )

            client.block(target_user_id=target_user_id, user_auth=False)

            return True

        except tweepy.TweepyException:
            raise

    def run(
        self,
        input_data: Input,
        *,
        credentials: TwitterCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            success = self.block_user(credentials, input_data.target_user_id)
            yield "success", success
        except Exception as e:
            yield "error", handle_tweepy_exception(e)