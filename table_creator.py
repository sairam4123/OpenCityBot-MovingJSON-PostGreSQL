import os

import asyncpg

DATABASE_URL = os.getenv('DATABASE_URL')


async def create_tables():
    pg_conn = await asyncpg.connect(DATABASE_URL)
    await pg_conn.execute("""
    CREATE TABLE public.application_data
(
    guild_id bigint,
    application_name text COLLATE pg_catalog."default",
    questions text[] COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE public.application_data
    OWNER to postgres;
    """)
    await pg_conn.execute("""
    CREATE TABLE public.bank_data
(
    guild_id bigint,
    bank_name text COLLATE pg_catalog."default",
    currency_symbol text COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE public.bank_data
    OWNER to postgres;
    """)
    await pg_conn.execute("""
    CREATE TABLE public.cogs_data
(
    guild_id bigint NOT NULL,
    enabled text[] COLLATE pg_catalog."default",
    disabled text[] COLLATE pg_catalog."default",
    CONSTRAINT cogs_data_pk PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE public.cogs_data
    OWNER to postgres;
-- Index: cogs_data_guild_id_uindex

-- DROP INDEX public.cogs_data_guild_id_uindex;

CREATE UNIQUE INDEX cogs_data_guild_id_uindex
    ON public.cogs_data USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
    """)
    await pg_conn.execute("""
    CREATE TABLE public.count_data
(
    guild_id bigint NOT NULL,
    suggestion_number integer DEFAULT 0,
    report_number integer DEFAULT 0,
    ticket_number integer DEFAULT 0,
    tunnel_number integer DEFAULT 0,
    CONSTRAINT count_data_pk PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE public.count_data
    OWNER to postgres;

CREATE UNIQUE INDEX count_data_guild_id_uindex
    ON public.count_data USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
    """)

    await pg_conn.execute("""
    CREATE TABLE public.economy_data
(
    guild_id bigint,
    user_id bigint,
    amount bigint DEFAULT 2000
)

TABLESPACE pg_default;

ALTER TABLE public.economy_data
    OWNER to postgres;
    """)

    await pg_conn.execute("""
    CREATE TABLE public.id_data
(
    suggestion_id bigint,
    report_id bigint,
    ticket_id bigint,
    tunnel_id bigint,
    row_id integer DEFAULT 0
)

TABLESPACE pg_default;

ALTER TABLE public.id_data
    OWNER to postgres;

CREATE UNIQUE INDEX id_data_report_id_uindex
    ON public.id_data USING btree
    (report_id ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX id_data_suggestion_id_uindex
    ON public.id_data USING btree
    (suggestion_id ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX id_data_ticket_id_uindex
    ON public.id_data USING btree
    (ticket_id ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX id_data_tunnel_id_uindex
    ON public.id_data USING btree
    (tunnel_id ASC NULLS LAST)
    TABLESPACE pg_default;
    """)

    await pg_conn.execute("""
    CREATE TABLE public.join_to_create_data
(
    channel_id bigint,
    user_id bigint
)

TABLESPACE pg_default;

ALTER TABLE public.join_to_create_data
    OWNER to postgres;    
    """)

    await pg_conn.execute("""
    CREATE TABLE public.leveling_data
(
    guild_id bigint,
    user_id bigint,
    xps integer,
    level integer,
    last_message_time bigint
)

TABLESPACE pg_default;

ALTER TABLE public.leveling_data
    OWNER to postgres;
    """)

    await pg_conn.execute("""
    CREATE TABLE public.prefix_data
(
    guild_id bigint NOT NULL,
    prefixes character varying[] COLLATE pg_catalog."default",
    CONSTRAINT prefix_data_pkey PRIMARY KEY (guild_id)
)

TABLESPACE pg_default;

ALTER TABLE public.prefix_data
    OWNER to postgres;
    """)

    await pg_conn.execute("""
    CREATE TABLE public.reaction_roles_data
(
    guild_id bigint,
    message_id bigint,
    reaction text COLLATE pg_catalog."default",
    role_id bigint,
    message_type text COLLATE pg_catalog."default"
)

TABLESPACE pg_default;

ALTER TABLE public.reaction_roles_data
    OWNER to postgres;
    """)
    await pg_conn.execute("""
    CREATE TABLE public.report_data
(
    "reportID" bigint NOT NULL,
    "reportMessageID" bigint,
    "reportTitle" text COLLATE pg_catalog."default",
    "reportReason" text COLLATE pg_catalog."default",
    "reportAuthor" text COLLATE pg_catalog."default",
    "reportTime" text COLLATE pg_catalog."default",
    "reportChannelID" bigint,
    "reportGuildID" bigint,
    "reportStatus" text COLLATE pg_catalog."default",
    "reportUser" text COLLATE pg_catalog."default",
    "reportModerator" text COLLATE pg_catalog."default",
    CONSTRAINT report_data_pk PRIMARY KEY ("reportID")
)

TABLESPACE pg_default;

ALTER TABLE public.report_data
    OWNER to postgres;

CREATE UNIQUE INDEX report_data_reportid_uindex
    ON public.report_data USING btree
    ("reportID" ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX report_data_reportmessageid_uindex
    ON public.report_data USING btree
    ("reportMessageID" ASC NULLS LAST)
    TABLESPACE pg_default;  
    """)

    await pg_conn.execute("""
    CREATE TABLE public.suggestion_data
(
    "suggestionID" bigint NOT NULL,
    "suggestionMessageID" bigint,
    "suggestionTitle" text COLLATE pg_catalog."default",
    "suggestionContent" text COLLATE pg_catalog."default",
    "suggestionAuthor" text COLLATE pg_catalog."default",
    "suggestionTime" text COLLATE pg_catalog."default",
    "suggestionChannelID" bigint,
    "suggestionGuildID" bigint,
    "suggestionType" text COLLATE pg_catalog."default",
    "suggestionStatus" text COLLATE pg_catalog."default",
    "suggestionModerator" text COLLATE pg_catalog."default",
    CONSTRAINT suggestion_data_pk PRIMARY KEY ("suggestionID")
)

TABLESPACE pg_default;

ALTER TABLE public.suggestion_data
    OWNER to postgres;

CREATE UNIQUE INDEX suggestion_data_suggestionid_uindex
    ON public.suggestion_data USING btree
    ("suggestionID" ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE UNIQUE INDEX suggestion_data_suggestionmessageid_uindex
    ON public.suggestion_data USING btree
    ("suggestionMessageID" ASC NULLS LAST)
    TABLESPACE pg_default;
    """)
    await pg_conn.execute("""
    CREATE TABLE public.tunnel_data
(
    "tunnelID" bigint NOT NULL,
    "tunnelReason" text COLLATE pg_catalog."default",
    "tunnelAuthor" text COLLATE pg_catalog."default",
    "tunnelOpenedTime" text COLLATE pg_catalog."default",
    "tunnelClosedTime" text COLLATE pg_catalog."default",
    "tunnelGuildID" text COLLATE pg_catalog."default",
    "tunnelStatus" text COLLATE pg_catalog."default",
    "tunnelUser" text COLLATE pg_catalog."default",
    CONSTRAINT tunnel_data_pk PRIMARY KEY ("tunnelID")
)

TABLESPACE pg_default;

ALTER TABLE public.tunnel_data
    OWNER to postgres;

CREATE UNIQUE INDEX tunnel_data_tunnelid_uindex
    ON public.tunnel_data USING btree
    ("tunnelID" ASC NULLS LAST)
    TABLESPACE pg_default;
    """)
    await pg_conn.execute("""
    CREATE TABLE public.ticket_data
(
    "ticketID" bigint NOT NULL,
    "ticketReason" text COLLATE pg_catalog."default",
    "ticketAuthor" text COLLATE pg_catalog."default",
    "ticketOpenedTime" text COLLATE pg_catalog."default",
    "ticketClosedTime" text COLLATE pg_catalog."default",
    "ticketGuildID" text COLLATE pg_catalog."default",
    "ticketStatus" text COLLATE pg_catalog."default",
    "ticketUser" text COLLATE pg_catalog."default",
    CONSTRAINT ticket_data_pk PRIMARY KEY ("ticketID")
)

TABLESPACE pg_default;

ALTER TABLE public.ticket_data
    OWNER to postgres;

CREATE UNIQUE INDEX ticket_data_ticketid_uindex
    ON public.ticket_data USING btree
    ("ticketID" ASC NULLS LAST)
    TABLESPACE pg_default;
    """)

    await pg_conn.execute("""
    CREATE TABLE public.tunnel_data
(
    "tunnelID" bigint NOT NULL,
    "tunnelReason" text COLLATE pg_catalog."default",
    "tunnelAuthor" text COLLATE pg_catalog."default",
    "tunnelOpenedTime" text COLLATE pg_catalog."default",
    "tunnelClosedTime" text COLLATE pg_catalog."default",
    "tunnelGuildID" text COLLATE pg_catalog."default",
    "tunnelStatus" text COLLATE pg_catalog."default",
    "tunnelUser" text COLLATE pg_catalog."default",
    CONSTRAINT tunnel_data_pk PRIMARY KEY ("tunnelID")
)

TABLESPACE pg_default;

ALTER TABLE public.tunnel_data
    OWNER to postgres;

CREATE UNIQUE INDEX tunnel_data_tunnelid_uindex
    ON public.tunnel_data USING btree
    ("tunnelID" ASC NULLS LAST)
    TABLESPACE pg_default;
    """)

    await pg_conn.execute("""
    CREATE TABLE public.voice_text_data
(
    guild_id bigint,
    voice_channel_id bigint,
    text_channel_id bigint
)

TABLESPACE pg_default;

ALTER TABLE public.voice_text_data
    OWNER to postgres;
    """)

create_tables()