from typing import Optional

import discord
from discord.ext import commands, menus


class HelpMenuPages(menus.MenuPages):
    async def update(self, payload):
        if self._can_remove_reactions:
            if payload.event_type == 'REACTION_ADD':
                await self.bot.http.remove_reaction(
                    payload.channel_id, payload.message_id,
                    discord.Message._emoji_reaction(payload.emoji), payload.member.id
                )
            elif payload.event_type == 'REACTION_REMOVE':
                return
        await super().update(payload)


class MyPaginatorHelpBot(menus.GroupByPageSource):
    def __init__(self, entries, key=None, per_page=3):
        super().__init__(entries=entries, key=key, per_page=per_page)
        self.old_entries = []

    @staticmethod
    def get_entry_type(entries):
        for entry in entries.items:
            print('ui')
            if isinstance(entry, commands.Group):
                print("group")
            elif isinstance(entry, commands.Command):
                print('command')
            elif isinstance(entry, commands.Cog):
                print('cog')
        else:
            return "bot"

    async def format_page(self, menu: menus.MenuPages, entries):
        embed = discord.Embed()
        if entries.key == "bot":
            embed.title = f"{menu.ctx.bot.user.name} bot's help"
            embed.description = f"{entries.items[0].description.format(prefix_1=menu.ctx.prefix)}" if entries.items[
                0].description else f"No description for {entries.items[0].qualified_name.replace('_', ' ')}"
            embed.set_footer(
                text=f"Page {menu.current_page + 1}/{self.get_max_pages()} Type {menu.ctx.prefix}help [command] for more info on a command. \nYou can also type {menu.ctx.prefix}help [category] for more info on a category and {menu.ctx.prefix}help [command] [subcommand] for more info in a sub command.")

        cog_ = menu.ctx.bot.get_cog(entries.key)
        print(entries.key, entries.items)
        if cog_ is not None:
            embed.title = f"{cog_.qualified_name.upper() if len(cog_.qualified_name) < 3 else cog_.qualified_name.capitalize()} cog's help"
            if menu.current_page == 0:
                self.old_entries = entries.items
                embed.description = f"{cog_.description.format(prefix_1=menu.ctx.prefix)}" if cog_.description else "No description"
            help_command = MyHelpCommand2()
            help_command.context = menu.ctx
            if menu.current_page != 0:
                entries_ = self.old_entries + entries.items
                for command in entries_:
                    embed.add_field(name=f"`{help_command.get_command_signature(command)}`**:**", value=command.help, inline=False)
            embed.set_footer(
                text=f"Page {menu.current_page + 1}/{self.get_max_pages()} Type {menu.ctx.prefix}help [command] for more info on a command. \nYou can also type {menu.ctx.prefix}help [category] for more info on a category and {menu.ctx.prefix}help [command] [subcommand] for more info in a sub command.")
        group_ = menu.ctx.bot.get_command(entries.key)
        if isinstance(group_, commands.Group):
            print('group')
            embed.title = f"{group_.qualified_name.upper() if len(group_.qualified_name) < 3 else group_.qualified_name.capitalize()} group's help"
            embed.description = f"Help: {group_.help}"
            help_command = MyHelpCommand2()
            help_command.context = menu.ctx
            for command in entries.items:
                embed.add_field(name=f"`{help_command.get_command_signature(command)}`**:**", value=command.help, inline=False)
            embed.set_footer(
                text=f"Page {menu.current_page + 1}/{self.get_max_pages()} Type {menu.ctx.prefix}help [command] for more info on a command. \nYou can also type {menu.ctx.prefix}help [category] for more info on a category and {menu.ctx.prefix}help [command] [subcommand] for more info in a sub command.")

        if isinstance(group_, commands.Command):
            print('command')
            embed.title = f"{group_.qualified_name.upper() if len(group_.qualified_name) < 3 else group_.qualified_name.capitalize()} command's help"
            embed.description = f"""Help: {group_.help}\nAliases: {" | ".join([f"`{alias}`" for alias in group_.aliases]) if group_.aliases else f"`{group_.qualified_name}`"}"""
            help_command = MyHelpCommand2()
            help_command.context = menu.ctx
            embed.set_footer(
                text=f"Page {menu.current_page + 1}/{self.get_max_pages()} \nType {menu.ctx.prefix}help [command] for more info on a command. \nYou can also type {menu.ctx.prefix}help [category] for more info on a category and {menu.ctx.prefix}help [command] [subcommand] for more info in a sub command.")

        return embed


class MyHelpCommand2(commands.HelpCommand):

    async def send_bot_help(self, mapping):
        bot: commands.Bot = self.context.bot
        cogs_ = sorted(bot.cogs.values(), key=lambda cog: cog.qualified_name)
        paginator_ = MyPaginatorHelpBot(cogs_, key=lambda c: "bot", per_page=1)
        pages_ = HelpMenuPages(source=paginator_, clear_reactions_after=True)
        await pages_.start(self.context)

    async def send_cog_help(self, cog):
        commands_ = sorted(await self.filter_commands(cog.get_commands(), sort=True), key=lambda command: command.qualified_name)
        paginator_ = MyPaginatorHelpBot(commands_, key=lambda command: command.cog_name or 'No Category', per_page=5)
        pages_ = HelpMenuPages(source=paginator_, clear_reactions_after=True)
        await pages_.start(self.context)

    async def send_group_help(self, group: commands.Group):
        commands_ = sorted(await self.filter_commands(group.commands, sort=True), key=lambda command: command.qualified_name)
        paginator_ = MyPaginatorHelpBot(commands_, key=lambda group_: group_.full_parent_name, per_page=5)
        pages_ = HelpMenuPages(source=paginator_, clear_reactions_after=True)
        await pages_.start(self.context)

    async def send_command_help(self, command):
        paginator_ = MyPaginatorHelpBot([command], key=lambda command_: command_.qualified_name, per_page=1)
        pages_ = HelpMenuPages(source=paginator_, clear_reactions_after=True)
        await pages_.start(self.context)


class Source(menus.GroupByPageSource):
    async def format_page(self, menu, entry):
        joined = '\n'.join(f'{i}. {v.value=}' for i, v in enumerate(entry.items, start=1))
        embed = discord.Embed()
        embed.title = f"Test paginator {entry.key}"
        embed.description = joined
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed


class Test:
    def __init__(self, key, value):
        self.key = key
        self.value = value


data = [
    Test(key=key, value=value)
    for key in ['test', 'other', 'okay']
    for value in range(20)
]


class Test_Cog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.help_2_command_ = MyHelpCommand2()

    @commands.command(help="Just a test. Nothing special. Will be removed soon.")
    async def test_command(self, ctx: commands.Context):
        pages = menus.MenuPages(source=Source(data, key=lambda t: t.key, per_page=5), clear_reactions_after=True)
        await pages.start(ctx)

    @commands.command(help="Just a test. Nothing special. Will be removed soon.")
    async def embed_command(self, ctx: commands.Context):
        embed = discord.Embed()
        leveling_cog = self.bot.get_cog('Leveling')
        embed.title = f"{leveling_cog.qualified_name} module's help"
        embed.description = leveling_cog.__doc__
        for command in leveling_cog.get_commands():
            embed.add_field(name=f'`!{command.qualified_name}`', value=command.help, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='help-2', help="The new help command which is going to replace the old help command.")
    async def help_2_command(self, ctx, *, command: Optional[str]):
        self.help_2_command_.context = ctx
        await self.help_2_command_.command_callback(ctx, command=command)


def setup(bot):
    bot.add_cog(Test_Cog(bot))
