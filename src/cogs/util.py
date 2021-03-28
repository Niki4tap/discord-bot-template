import discord
import subprocess
import itertools
import datetime

from discord.ext import	commands

# Custom help command implementation
class PrettyHelpCommand(commands.DefaultHelpCommand):

    def __init__(self, embed_color, **options):
        self.embed_color = embed_color
        super().__init__(**options)

    async def send_error_message(self, error):
        # No "no command found" messages
        return

    async def send_pages(self, note="", inline=False):
        # Overwrite the send method to send each page in an embed instead
        destination = self.get_destination()

        for page in self.paginator.pages:
            formatted = discord.Embed(color=self.embed_color)
            
            split = page.split("**")
            if len(split) == 1:
                formatted.description = page
            else:
                split = iter(split)
                header = next(split)
                formatted.description = header

                for segment in split:
                    if segment.strip() == "":
                        continue
                    
                    title = segment
                    content = next(split)

                    formatted.add_field(name=title, value=content, inline=inline)

            formatted.set_footer(text=note)
            
            await destination.send(embed=formatted)

    def add_indented_commands(self, commands, *, heading, max_size=None):
        if not commands:
            return

        self.paginator.add_line()    
        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)

        for command in commands:
            name = command.name
            self.paginator.add_line(self.shorten_text("\u200b  `" + name + "`"))
            self.paginator.add_line(self.shorten_text(command.short_doc))

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_line(bot.description, empty=True)

        def get_category(command, *, no_category='\u200b**{0.no_category}**'.format(self)):
            cog = command.cog
            return "**" + cog.qualified_name + '**' if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            self.add_indented_commands(commands, heading=category, max_size=max_size)

        note = self.get_ending_note()

        await self.send_pages(note=note, inline=True)

    def get_ending_note(self):
        """Returns help command's ending note. This is mainly useful to override for i18n purposes."""
        command_name = self.invoked_with
        return "Type {0}{1} command for more info on a command.".format(self.clean_prefix, command_name)

    def get_command_signature(self, command):
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = '[%s|%s]' % (command.name, aliases)
            if parent:
                fmt = parent + ' ' + fmt
            alias = fmt
        else:
            alias = command.name if not parent else parent + ' ' + command.name

        return '`%s%s %s`' % (self.clean_prefix, alias, command.signature)

class utilCog(commands.Cog, name="Utility commands"):
	def	__init__(self, bot):
		self.bot = bot
		self._original_help_command = bot.help_command
		bot.help_command = PrettyHelpCommand(bot.embed_color, **dict(paginator=commands.Paginator(prefix="", suffix="")))
		bot.help_command.cog = self

	@commands.command(name="ping")
	async def ping(self, ctx):
		'''
		Prints bot's latency
		'''
		return await self.bot.send(ctx, "Latency: " + str(round(self.bot.latency, 3)) + " seconds.")

	@commands.command(aliases=["info", "you"])
	@commands.cooldown(5, 8, commands.BucketType.channel)
	async def about(self, ctx):
		"""
		Displays bot information.
		"""
		about_embed = discord.Embed(
			title="About This Bot", 
			type="rich", 
			colour=self.bot.embed_color, 
			description="\n".join([
				f"{ctx.me.name} - Template discord bot, by Niki4tap.\n"
			])
		)
		ut = datetime.datetime.utcnow() - self.bot.started
		stats = "".join([
			f"\nGuilds: {len(self.bot.guilds)}",
			f"\nChannels: {sum(len(g.channels) for g in self.bot.guilds)}",
			f"\nUptime: {ut.days}d {ut.seconds // 3600}h {ut.seconds % 3600 // 60}m {ut.seconds % 60}s"
		])
		about_embed.add_field(name="Statistics", value=stats)
		about_embed.add_field(name="Valid Prefixes", value="\n".join([
			"`" + p + "`" for p in self.bot.prefixes
		]))
		await ctx.send(embed=about_embed)

	def cog_unload(self):
		self.bot.help_command = self._original_help_command

def setup(bot):
    bot.add_cog(utilCog(bot))