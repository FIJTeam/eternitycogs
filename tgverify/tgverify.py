# Standard Imports
import logging
from typing import Union

# Discord Imports
import discord

# Redbot Imports
from redbot.core import commands, checks, Config

from tgcommon.errors import TGRecoverableError, TGUnrecoverableError
from tgcommon.util import normalise_to_ckey
from typing import cast

__version__ = "1.1.0"
__author__ = "oranges"

log = logging.getLogger("red.oranges_tgverify")

BaseCog = getattr(commands, "Cog", object)


class TGverify(BaseCog):
    """
    Connector that will integrate with any database using the latest tg schema, provides utility functionality
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=672261474290237490, force_registration=True
        )
        self.visible_config = [
            "min_living_minutes",
            "verified_role",
            "instructions_link",
            "welcomegreeting",
            "disabledgreeting",
            "bunkerwarning",
            "bunker",
            "welcomechannel",
        ]

        default_guild = {
            "min_living_minutes": 60,
            "verified_role": None,
            "verified_living_role": None,
            "instructions_link": "",
            "welcomegreeting": "",
            "disabledgreeting": "",
            "bunkerwarning": "",
            "bunker": False,
            "disabled": False,
            "welcomechannel": "",
        }

        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.group()
    @checks.mod_or_permissions(administrator=True)
    async def tgverify(self, ctx):
        """
        SS13 Configure the settings on the verification cog
        """
        pass

    @commands.guild_only()
    @tgverify.group()
    @checks.mod_or_permissions(administrator=True)
    async def config(self, ctx):
        """
        SS13 Configure the settings on the verification cog
        """
        pass

    @config.command()
    async def current(self, ctx):
        """
        Gets the current settings for the verification system
        """
        settings = await self.config.guild(ctx.guild).all()
        embed = discord.Embed(title="__Current settings:__")
        for k, v in settings.items():
            # Hide any non whitelisted config settings (safety moment)
            if k in self.visible_config:
                if v == "":
                    v = None
                embed.add_field(name=f"{k}:", value=v, inline=False)
            else:
                embed.add_field(name=f"{k}:", value="`redacted`", inline=False)
        await ctx.send(embed=embed)

    @config.command()
    async def living_minutes(self, ctx, min_living_minutes: int = None):
        """
        Sets the minimum required living minutes before this bot will apply a verification role to a user
        """
        try:
            if min_living_minutes is None:
                await self.config.guild(ctx.guild).min_living_minutes.set(0)
                await ctx.send(
                    f"Минимальное количество прожитых минут, необходимое для верификации убрано!"
                )
            else:
                await self.config.guild(ctx.guild).min_living_minutes.set(
                    min_living_minutes
                )
                await ctx.send(
                    f"Минимальное количество минут жизни, необходимое для верификации, установлено на: `{min_living_minutes}`"
                )

        except (ValueError, KeyError, AttributeError):
            await ctx.send(
                "Возникла проблема с установкой минимально необходимого количества минут жизни"
            )

    @config.command()
    async def instructions_link(self, ctx, instruction_link: str):
        """
        Sets the link to further instructions on how to generate verification information
        """
        try:
            await self.config.guild(ctx.guild).instructions_link.set(instruction_link)
            await ctx.send(f"Ссылка на инструкцию установлена на: `{instruction_link}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("Возникла проблема с установкой ссылки на инструкции")

    @config.command()
    async def welcome_channel(self, ctx, channel: discord.TextChannel):
        """
        Sets the channel to send the welcome message
        If channel isn"t specified, the guild's default channel will be used
        """
        guild = ctx.message.guild
        guild_settings = await self.config.guild(guild).welcomechannel()
        if channel is None:
            channel = ctx.message.channel
        if not channel.permissions_for(ctx.me).send_messages:
            msg = "У меня нет прав на отправку сообщений в {channel}".format(
                channel=channel.mention
            )
            await ctx.send(msg)
            return
        guild_settings = channel.id
        await self.config.guild(guild).welcomechannel.set(guild_settings)
        msg = "Теперь я буду отправлять приветственные сообщения в {channel}".format(
            channel=channel.mention
        )
        await channel.send(msg)

    @config.command()
    async def welcome_greeting(self, ctx, welcomegreeting: str):
        """
        Sets the welcoming greeting
        """
        try:
            await self.config.guild(ctx.guild).welcomegreeting.set(welcomegreeting)
            await ctx.send(f"Приветствие настроено на: `{welcomegreeting}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("Возникла проблема с установкой приветствия")

    @config.command()
    async def disabled_greeting(self, ctx, disabledgreeting: str):
        """
        Sets the welcoming greeting when the verification system is disabled
        """
        try:
            await self.config.guild(ctx.guild).disabledgreeting.set(disabledgreeting)
            await ctx.send(f"Отключено приветствие, установленное на: `{disabledgreeting}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("Возникла проблема с установкой отключения приветствия")

    @config.command()
    async def bunker_warning(self, ctx, bunkerwarning: str):
        """
        Sets the additional message added to the greeting message when the bunker is on
        """
        try:
            await self.config.guild(ctx.guild).bunkerwarning.set(bunkerwarning)
            await ctx.send(f"Предупреждение бункера установлено на: `{bunkerwarning}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("Проблема с установкой предупреждения бункера")

    @tgverify.command()
    async def bunker(self, ctx):
        """
        Toggle bunker status on or off
        """
        try:
            bunker = await self.config.guild(ctx.guild).bunker()
            bunker = not bunker
            await self.config.guild(ctx.guild).bunker.set(bunker)
            if bunker:
                await ctx.send(f"Предупреждение бункера ВКЛ")
            else:
                await ctx.send(f"Предупреждение бункера ВЫКЛ")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("Проблема с переключением предупреждения бункера")

    @tgverify.command()
    async def broken(self, ctx):
        """
        For when verification breaks
        """
        try:
            disabled = await self.config.guild(ctx.guild).disabled()
            disabled = not disabled
            await self.config.guild(ctx.guild).disabled.set(disabled)
            if disabled:
                await ctx.send(f"Система верификации теперь ВЫКЛ")
            else:
                await ctx.send(f"Система верификации теперь ВКЛ")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("Возникла проблема с переключением флага отключения системы верификации")

    @config.command()
    async def verified_role(self, ctx, verified_role: int = None):
        """
        Set what role is applied when a user verifies
        """
        try:
            role = ctx.guild.get_role(verified_role)
            if not role:
                return await ctx.send(f"Это неподходящая или недопустимая роль для этого дискорда!")
            if verified_role is None:
                await self.config.guild(ctx.guild).verified_role.set(None)
                await ctx.send(f"При верификации пользователя роль не будет установлена!")
            else:
                await self.config.guild(ctx.guild).verified_role.set(verified_role)
                await ctx.send(
                    f"Когда пользователь соответствует минимальной проверке, эта роль будет применена: `{verified_role}`"
                )

        except (ValueError, KeyError, AttributeError):
            await ctx.send("Возникла проблема с установкой верифицированной роли")

    @config.command()
    async def verified_living_role(self, ctx, verified_living_role: int = None):
        """
        Set what role is applied when a user verifies
        """
        try:
            role = ctx.guild.get_role(verified_living_role)
            if not role:
                return await ctx.send(f"Это неподходящая или недопустимая роль для этого дискорда!")
            if verified_living_role is None:
                await self.config.guild(ctx.guild).verified_living_role.set(None)
                await ctx.send(f"При верификации пользователя роль не будет установлена!")
            else:
                await self.config.guild(ctx.guild).verified_living_role.set(
                    verified_living_role
                )
                await ctx.send(
                    f"Когда пользователь соответствует минимальной проверке, эта роль будет применена: `{verified_living_role}`"
                )

        except (ValueError, KeyError, AttributeError):
            await ctx.send("Возникла проблема с установкой верифицированной роли")

    @tgverify.command()
    async def discords(self, ctx, ckey: str):
        """
        List all past discord accounts this ckey has verified with
        """
        tgdb = self.get_tgdb()
        ckey = normalise_to_ckey(ckey)
        message = await ctx.send("Собираем дискорд-аккаунты привязанные к этому ckey....")
        async with ctx.typing():
            embed = discord.Embed(color=await ctx.embed_color())
            embed.set_author(
                name=f"Дискорд-аккаунты привязанные к {str(ckey).title()}"
            )
            links = await tgdb.all_discord_links_for_ckey(ctx, ckey)
            if len(links) <= 0:
                return await message.edit(
                    content="Не найдено привязанных дискорд-аккаунтов к этому ckey"
                )

            names = ""
            for link in links:
                names += f"Пользователь привязан <@{link.discord_id}> на {link.timestamp}, текущий аккаунт: {link.validity}\n"

            embed.add_field(name="__Discord accounts__", value=names, inline=False)
            await message.edit(content=None, embed=embed)

    @tgverify.command()
    async def whois(self, ctx, discord_user: discord.User):
        """
        Return the ckey attached to the given discord user, if they have one
        """
        tgdb = self.get_tgdb()

        message = await ctx.send("Начинаем поиск по ckey пользователя....")
        async with ctx.typing():
            # Attempt to find the discord ids based on the one time token passed in.
            discord_link = await tgdb.discord_link_for_discord_id(ctx, discord_user.id)
            if discord_link:
                message = await message.edit(
                    content=f"Этот пользователь привязан к этому ckey {discord_link.ckey}"
                )
            else:
                message = await message.edit(
                    content=f"У пользователя нету привязанных ckey"
                )

    @tgverify.command()
    async def deverify(self, ctx, discord_user: discord.User):
        """
        Deverifies the ckey linked to this user, all historical verifications will be removed, the user will have to connect to the game
        and generate a new one time token to get their verification role
        """
        tgdb = self.get_tgdb()

        message = await ctx.send("Начинаем поиск по ckey пользователя....")
        async with ctx.typing():
            # Attempt to find the discord link from the user
            discord_link = await tgdb.discord_link_for_discord_id(ctx, discord_user.id)
            if discord_link:
                # now clear all the links for this ckey
                await tgdb.clear_all_valid_discord_links_for_ckey(
                    ctx, discord_link.ckey
                )
                message = await message.edit(content=f"Пользователь деверифицирован")
            else:
                message = await message.edit(
                    content=f"У пользователя нету привязанных ckey"
                )

    # Now the only user facing command, so this has rate limiting across the sky
    @commands.cooldown(2, 60, type=commands.BucketType.user)
    @commands.cooldown(6, 60, type=commands.BucketType.guild)
    @commands.max_concurrency(3, per=commands.BucketType.guild, wait=False)
    @commands.guild_only()
    @commands.command()
    async def verify(self, ctx, *, one_time_token: str = None):
        """
        Attempt to verify the user, based on the passed in one time code
        This command is rated limited to two attempts per user every 60 seconds, and 6 attempts per entire discord every 60 seconds
        """
        # Get the minimum required living minutes
        min_required_living_minutes = await self.config.guild(
            ctx.guild
        ).min_living_minutes()
        instructions_link = await self.config.guild(ctx.guild).instructions_link()
        role = await self.config.guild(ctx.guild).verified_role()
        verified_role = await self.config.guild(ctx.guild).verified_living_role()
        role = ctx.guild.get_role(role)
        verified_role = ctx.guild.get_role(verified_role)
        tgdb = self.get_tgdb()
        ckey = None

        # First lets try to remove their message, since the one time token is technically a secret if something goes wrong
        try:
            await ctx.message.delete()
        except (discord.DiscordException):
            await ctx.send(
                "У меня нет необходимых прав для удаления сообщений, пожалуйста, удалите/отредактируйте одноразовый/временный токен вручную."
            )
        if not role:
            raise TGUnrecoverableError(
                "Роль проверки не настроена, настройте её с помощью конфига"
            )
        if not verified_role:
            raise TGUnrecoverableError(
                "Роль верификации не настроена для минут жизни, настройте её с помощью конфига"
            )

        if role in ctx.author.roles and verified_role in ctx.author.roles:
            return await ctx.send("Вы уже прошли верификацию")

        message = await ctx.send("Пытаюсь верифицировать....")
        async with ctx.typing():

            if one_time_token:
                # Attempt to find the user based on the one time token passed in.
                ckey = await tgdb.lookup_ckey_by_token(ctx, one_time_token)

            prexisting = False
            # they haven't specified a one time token or it didn't match, see if we already have a linked ckey for the user id that is still valid
            if ckey is None:
                discord_link = await tgdb.discord_link_for_discord_id(
                    ctx, ctx.author.id
                )
                if discord_link and discord_link.valid > 0:
                    prexisting = True
                    ckey = discord_link.ckey
                    # Now look for the user based on the ckey
                    # player = await tgdb.get_player_by_ckey(ctx, discord_link.ckey)
                    # if player and player['living_time'] >= min_required_living_minutes:
                    #    await ctx.author.add_roles(verified_role, reason="User has verified against their in game living minutes")
                    # we have a fast path, just reapply the linked role and bail
                    # await ctx.author.add_roles(role, reason="User has verified in game")
                    # return await message.edit(content=f"Congrats {ctx.author} your verification is complete")
                else:
                    raise TGRecoverableError(
                        f"Извините {ctx.author} похоже, что у вас нет ckey, привязанного к этой учетной записи discord, вернитесь в игру и попробуйте сгенерировать токен! Посмотрите {instructions_link} для подробной информации. \n\nЕсли после нескольких попыток проблема всё ещё остаётся, обратитесь за поддержкой к Founder, "
                    )

            log.info(
                f"Запрос на верификацию от {ctx.author.id}, для ckey {ckey}, токен был: {one_time_token}"
            )
            # Now look for the user based on the ckey
            player = await tgdb.get_player_by_ckey(ctx, ckey)

            if player is None:
                raise TGRecoverableError(
                    f"Извините {ctx.author} похоже, мы не смогли найти вашего пользователя, обратитесь за поддержкой к Founder!"
                )

            if not prexisting:
                # clear any/all previous valid links for ckey or the discord id (in case they have decided to make a new ckey)
                await tgdb.clear_all_valid_discord_links_for_ckey(ctx, ckey)
                await tgdb.clear_all_valid_discord_links_for_discord_id(
                    ctx, ctx.author.id
                )
                # Record that the user is linked against a discord id
                await tgdb.update_discord_link(ctx, one_time_token, ctx.author.id)

            successful = False
            if role:
                await ctx.author.add_roles(role, reason="Пользователь прошел верификацию в игре")
            if player["living_time"] >= min_required_living_minutes:
                successful = True
                await ctx.author.add_roles(
                    verified_role,
                    reason="Пользователь прошел верификацию в соответствии со своими минутами жизни в игре",
                )

            fuck = f"Поздравляю {ctx.author} ваша верификация завершена, но у вас не прожито достаточное {min_required_living_minutes} минут в игре за члена экипажа (у вас сейчас {player['living_time']}). Вы всегда можете пройти верификацию повторно, просто написав `$verify`"
            if successful:
                fuck = f"Поздравляю {ctx.author} верификация завершена"
            return await message.edit(content=fuck, color=0xFF0000)

    @verify.error
    async def verify_error(self, ctx, error):
        # Our custom, something recoverable went wrong error type
        if isinstance(error, TGRecoverableError):
            embed = discord.Embed(
                title=f"Ошибка верификации:",
                description=f"{format(error)}",
                color=0xFF0000,
            )
            await ctx.send(content=f"", embed=embed)

        elif isinstance(error, commands.MaxConcurrencyReached):
            embed = discord.Embed(
                title=f"Слишком много верификаций в текущий момент, попробуйте снова через 30 секунд:",
                description=f"{format(error)}",
                color=0xFF0000,
            )
            await ctx.send(content=f"", embed=embed)
            log.exception(
                f"Слишком много пользователей одновременно пытаются пройти верификацию, ожидание БД нарушено?"
            )

        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title=f"Помедленней паренёк:",
                description=f"{format(error)}",
                color=0xFF0000,
            )
            await ctx.send(content=f"", embed=embed)
            log.warning(
                f"Достигнут лимит верификаций, пользователь стал уродцем {ctx.author}, discord id {ctx.author.id}"
            )

        elif isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(
                title=f"Неверный канал приятель, качалка ниже:",
                description=f"{format(error)}",
                color=0xFF0000,
            )
            await ctx.send(content=f"", embed=embed)
        else:
            # Something went badly wrong, log to the console
            log.exception("Внутренняя ошибка во время верификации пользователя")
            # now pretend everything is fine to the user :>
            embed = discord.Embed(
                title=f"Произошла системная ошибка",
                description=f"Попробуйте снова повторить действие",
                color=0xFF0000,
            )
            await ctx.send(content=f"", embed=embed)

    @tgverify.command()
    async def test(self, ctx, discord_user: discord.User):
        """
        Test welcome message sending
        """
        guild = ctx.guild
        member = guild.get_member(discord_user.id)
        await self.handle_member_join(member)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self.handle_member_join(member)

    async def handle_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        if guild is None:
            return
        channel_id = await self.config.guild(guild).welcomechannel()
        channel = cast(discord.TextChannel, guild.get_channel(channel_id))
        if channel is None:
            log.info(
                f"Система верификации не обнаружила требуемый канал в дискорд-сервере, вероятно, он был удален. Пользователь присоединился: {member}"
            )
            return

        if not guild.me.permissions_in(channel).send_messages:
            log.info(f"Ошибка доступа. Пользователь, который присоединился:{member}")
            log.info(
                f"Бот не имеет прав на отправку сообщений в {guild.name}'s #{channel.name} канал"
            )
            return

        final = ""
        if await self.config.guild(guild).disabled():
            msg = await self.config.guild(guild).disabledgreeting()
            final = msg.format(member, guild)
        else:
            msg = await self.config.guild(guild).welcomegreeting()
            final = msg.format(member, guild)
        bunkermsg = await self.config.guild(guild).bunkerwarning()
        bunker = await self.config.guild(guild).bunker()
        if bunkermsg != "" and bunker:
            final = final + " " + bunkermsg

        await channel.send(final)

    def get_tgdb(self):
        tgdb = self.bot.get_cog("TGDB")
        if not tgdb:
            raise TGUnrecoverableError(
                "TGDB должна существовать и быть настроена для работы tgverify cog"
            )

        return tgdb
