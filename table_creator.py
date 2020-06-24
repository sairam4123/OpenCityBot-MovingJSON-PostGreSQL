import asyncio
import os

import asyncpg

DATABASE_URL = os.getenv('DATABASE_URL')


async def create_tables():
    pg_conn = await asyncpg.connect(DATABASE_URL)
    await pg_conn.execute("""

            create table if not exists prefix_data
            (
                guild_id bigint not null
                    constraint prefix_data_pkey
                        primary key,
                prefixes character varying[]
            );

            create table if not exists cogs_data
            (
                guild_id bigint not null
                    constraint cogs_data_pk
                        primary key,
                enabled  text[],
                disabled text[]
            );

            create unique index if not exists cogs_data_guild_id_uindex
                on cogs_data (guild_id);

            create table if not exists voice_text_data
            (
                guild_id         bigint,
                voice_channel_id bigint,
                text_channel_id  bigint
            );

            create table if not exists suggestion_data
            (
                "suggestionID"        bigint not null
                    constraint suggestion_data_pk
                        primary key,
                "suggestionMessageID" bigint,
                "suggestionTitle"     text,
                "suggestionContent"   text,
                "suggestionAuthor"    text,
                "suggestionTime"      text,
                "suggestionChannelID" bigint,
                "suggestionGuildID"   bigint,
                "suggestionType"      text,
                "suggestionStatus"    text,
                "suggestionModerator" text
            );

            create unique index if not exists suggestion_data_suggestionid_uindex
                on suggestion_data ("suggestionID");

            create unique index if not exists suggestion_data_suggestionmessageid_uindex
                on suggestion_data ("suggestionMessageID");

            create table if not exists report_data
            (
                "reportID"        bigint not null
                    constraint report_data_pk
                        primary key,
                "reportMessageID" bigint,
                "reportTitle"     text,
                "reportReason"    text,
                "reportAuthor"    text,
                "reportTime"      text,
                "reportChannelID" bigint,
                "reportGuildID"   bigint,
                "reportStatus"    text,
                "reportUser"      text,
                "reportModerator" text
            );

            create unique index if not exists report_data_reportid_uindex
                on report_data ("reportID");

            create unique index if not exists report_data_reportmessageid_uindex
                on report_data ("reportMessageID");

            create table if not exists ticket_data
            (
                "ticketID"         bigint not null
                    constraint ticket_data_pk
                        primary key,
                "ticketReason"     text,
                "ticketAuthor"     text,
                "ticketOpenedTime" text,
                "ticketClosedTime" text,
                "ticketGuildID"    text,
                "ticketStatus"     text,
                "ticketUser"       text
            );

            create unique index if not exists ticket_data_ticketid_uindex
                on ticket_data ("ticketID");

            create table if not exists tunnel_data
            (
                "tunnelID"         bigint not null
                    constraint tunnel_data_pk
                        primary key,
                "tunnelReason"     text,
                "tunnelAuthor"     text,
                "tunnelOpenedTime" text,
                "tunnelClosedTime" text,
                "tunnelGuildID"    text,
                "tunnelStatus"     text,
                "tunnelUser"       text
            );

            create unique index if not exists tunnel_data_tunnelid_uindex
                on tunnel_data ("tunnelID");

            create table if not exists id_data
            (
                suggestion_id bigint,
                report_id     bigint,
                ticket_id     bigint,
                tunnel_id     bigint,
                row_id        integer default 0
            );

            create unique index if not exists id_data_report_id_uindex
                on id_data (report_id);

            create unique index if not exists id_data_suggestion_id_uindex
                on id_data (suggestion_id);

            create unique index if not exists id_data_ticket_id_uindex
                on id_data (ticket_id);

            create unique index if not exists id_data_tunnel_id_uindex
                on id_data (tunnel_id);

            create table if not exists count_data
            (
                guild_id          bigint not null
                    constraint count_data_pk
                        primary key,
                suggestion_number integer default 0,
                report_number     integer default 0,
                ticket_number     integer default 0,
                tunnel_number     integer default 0
            );

            create unique index if not exists count_data_guild_id_uindex
                on count_data (guild_id);

            create table if not exists leveling_data
            (
                guild_id          bigint,
                user_id           bigint,
                xps               integer,
                level             integer,
                last_message_time bigint
            );

            create table if not exists application_data
            (
                guild_id         bigint,
                application_name text,
                questions        text[]
            );

            create table if not exists join_to_create_data
            (
                channel_id bigint,
                user_id    bigint
            );

            create table if not exists reaction_roles_data
            (
                guild_id     bigint,
                message_id   bigint,
                reaction     text,
                role_id      bigint,
                message_type text
            );

            create table if not exists bank_data
            (
                guild_id        bigint,
                bank_name       text,
                currency_symbol text
            );

            create table if not exists economy_data
            (
                guild_id bigint,
                user_id  bigint,
                amount   bigint default 2000
            );

            create table if not exists leveling_message_destination_data
            (
                guild_id       bigint,
                channel_id     bigint,
                "enabled?"     boolean,
                message_string text[]
            );

            create table if not exists gate_keeper_data
            (
                guild_id                   bigint,
                welcome_message            text[],
                leave_message              text[],
                ban_message                text[],
                welcome_message_channel_id bigint,
                leave_message_channel_id   bigint,
                ban_message_channel_id     bigint
            );

            create unique index if not exists gate_keeper_data_guild_id_uindex
                on gate_keeper_data (guild_id);

            create table if not exists black_listed_users_data
            (
                black_listed_users bigint[],
                row_id             integer default 1
            );
            
            create table if not exists jokes_data
            (
                questions text,
                answers text
            );
            
            create table if not exists "reaction_roles_message_data" 
            (
                "message_id" bigint,
                "message_type" text,
                "limit" integer default '-1'::integer
            );


    """)
    print("created everything")


asyncio.run(create_tables())

# drop
# table if exists
# prefix_data
# cascade;
#
# drop
# table if exists
# cogs_data
# cascade;
#
# drop
# table if exists
# voice_text_data
# cascade;
#
# drop
# table if exists
# suggestion_data
# cascade;
#
# drop
# table if exists
# report_data
# cascade;
#
# drop
# table if exists
# ticket_data
# cascade;
#
# drop
# table if exists
# tunnel_data
# cascade;
#
# drop
# table if exists
# id_data
# cascade;
#
# drop
# table if exists
# count_data
# cascade;
#
# drop
# table if exists
# leveling_data
# cascade;
#
# drop
# table if exists
# application_data
# cascade;
#
# drop
# table if exists
# join_to_create_data
# cascade;
#
# drop
# table if exists
# reaction_roles_data
# cascade;
#
# drop
# table if exists
# bank_data
# cascade;
#
# drop
# table if exists
# economy_data
# cascade;
#
# drop
# table if exists
# leveling_message_destination_data
# cascade;
#
# drop
# table if exists
# gate_keeper_data
# cascade;
#
# drop
# table if exists
# black_listed_users_data
# cascade;
#
# drop
# table if exists
# jokes_data
# cascade;
