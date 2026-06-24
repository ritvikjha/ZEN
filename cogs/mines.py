"""
Mines Cog — Interactive 5×5 minefield with Discord buttons.

The player reveals tiles one at a time. Each safe tile increases their
multiplier. They can "Cash Out" at any time to lock in winnings.
Hitting a mine = lose the entire bet.
"""

import random
import discord
from discord.ext import commands
from discord.ui import View, Button

from utils.data import get_balance, add_balance

# ── Configuration ─────────────────────────────────────────────────────────
GRID_SIZE = 5
NUM_MINES = 5

# Multiplier table: maps number_of_safe_reveals → cumulative multiplier
# Roughly follows a risk-curve (gets more rewarding as you go deeper).
_TOTAL_TILES = GRID_SIZE * GRID_SIZE
_SAFE_TILES = _TOTAL_TILES - NUM_MINES

# Pre-compute multipliers using a geometric progression
MULTIPLIERS: dict[int, float] = {}
for i in range(1, _SAFE_TILES + 1):
    # Each reveal multiplies by roughly (total_remaining / safe_remaining)
    # This gives fair-ish odds with a slight house edge
    mult = 1.0
    for j in range(i):
        remaining = _TOTAL_TILES - j
        safe_remaining = _SAFE_TILES - j
        mult *= remaining / safe_remaining
    MULTIPLIERS[i] = round(mult * 0.97, 2)  # 3% house edge


class MinesView(View):
    """Interactive 5×5 minefield using a grid of Discord buttons."""

    def __init__(
        self,
        ctx: commands.Context,
        bet: int,
        starting_balance: int,
    ):
        super().__init__(timeout=180)  # 3-minute timeout
        self.ctx = ctx
        self.bet = bet
        self.starting = starting_balance
        self.game_over = False
        self.reveals = 0
        self.message: discord.Message | None = None

        # Generate mine positions
        all_positions = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
        self.mines = set(random.sample(all_positions, NUM_MINES))
        self.revealed: set[tuple[int, int]] = set()

        # Build the button grid
        self._build_grid()

    def _build_grid(self):
        """Create the initial 5×5 button grid + cash out button."""
        self.clear_items()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                btn = Button(
                    label="·",
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"mine_{r}_{c}",
                    row=r,
                )
                if (r, c) in self.revealed:
                    btn.label = "💎"
                    btn.style = discord.ButtonStyle.success
                    btn.disabled = True

                btn.callback = self._make_callback(r, c)
                self.add_item(btn)

    def _make_callback(self, r: int, c: int):
        """Create a callback for a specific tile button."""
        async def callback(interaction: discord.Interaction):
            await self._reveal_tile(interaction, r, c)
        return callback

    @property
    def current_multiplier(self) -> float:
        if self.reveals == 0:
            return 0.0
        return MULTIPLIERS.get(self.reveals, 1.0)

    @property
    def current_winnings(self) -> int:
        return int(self.bet * self.current_multiplier)

    @property
    def next_multiplier(self) -> float:
        return MULTIPLIERS.get(self.reveals + 1, 1.0)

    def build_embed(self) -> discord.Embed:
        """Build the game-state embed."""
        if self.game_over:
            return self._final_embed
        embed = discord.Embed(
            title="💣 Mines",
            description=(
                f"**Bet:** 🪙 **{self.bet:,}**\n"
                f"**Revealed:** {self.reveals} / {_SAFE_TILES}\n"
                f"**Current Multiplier:** `{self.current_multiplier:.2f}×`\n"
                f"**Current Winnings:** 🪙 **{self.current_winnings:,}**\n"
                f"**Next Reveal:** `{self.next_multiplier:.2f}×`\n\n"
                f"💎 = Safe  |  💣 = Mine  |  Click **Cash Out** to collect!"
            ),
            color=0x3498DB,
        )
        embed.set_footer(text=f"Mines: {NUM_MINES} hidden in the grid")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your game!", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        """Auto cash-out on timeout if the player has reveals."""
        if not self.game_over:
            if self.reveals > 0:
                await self._do_cashout(None)
            else:
                self.game_over = True
                self._final_embed = discord.Embed(
                    title="⏰ Timed Out!",
                    description="Game expired. Your bet has been returned.",
                    color=0xFFA500,
                )
                self._disable_all()
                if self.message:
                    try:
                        await self.message.edit(embed=self._final_embed, view=self)
                    except Exception:
                        pass

    async def _reveal_tile(self, interaction: discord.Interaction, r: int, c: int):
        """Handle a tile click."""
        if self.game_over or (r, c) in self.revealed:
            return

        if (r, c) in self.mines:
            # 💥 Hit a mine!
            self.game_over = True
            new_bal = add_balance(self.ctx.author.id, -self.bet, self.starting)
            self._show_all_mines()
            self._final_embed = discord.Embed(
                title="💥 BOOM! You Hit a Mine!",
                description=(
                    f"You lost 🪙 **{self.bet:,}** Coins!\n"
                    f"**Balance:** 🪙 **{new_bal:,}**"
                ),
                color=0xE74C3C,
            )
            self._final_embed.set_footer(text=f"You survived {self.reveals} reveals")
            self._disable_all()
            await interaction.response.edit_message(
                embed=self._final_embed, view=self
            )
            self.stop()
        else:
            # Safe tile
            self.reveals += 1
            self.revealed.add((r, c))

            # Check if all safe tiles are revealed (full clear!)
            if self.reveals >= _SAFE_TILES:
                await self._do_cashout(interaction)
                return

            # Rebuild the grid with the new revealed tile
            self._build_grid()
            # Add the cash-out button back
            self._add_cashout_button()

            await interaction.response.edit_message(
                embed=self.build_embed(), view=self
            )

    def _show_all_mines(self):
        """Reveal all mine positions in the button grid (for game-over display)."""
        self.clear_items()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if (r, c) in self.mines:
                    btn = Button(
                        label="💣",
                        style=discord.ButtonStyle.danger,
                        disabled=True,
                        row=r,
                    )
                elif (r, c) in self.revealed:
                    btn = Button(
                        label="💎",
                        style=discord.ButtonStyle.success,
                        disabled=True,
                        row=r,
                    )
                else:
                    btn = Button(
                        label="·",
                        style=discord.ButtonStyle.secondary,
                        disabled=True,
                        row=r,
                    )
                self.add_item(btn)

    def _add_cashout_button(self):
        """We can't add a 6th row, so we use a different approach:
        The cash-out is triggered by a command or we use the first row trick.
        Actually, Discord allows 5 rows × 5 buttons = 25, which is exactly our grid.
        So we'll use a separate message or a follow-up.
        
        Workaround: We'll make the grid 5×5 but sacrifice the bottom-right tile
        to place a Cash Out button. Actually, let's just keep it clean and 
        add a text instruction to use a reaction or a new command.
        
        Better solution: use 4 rows of 5 tiles + 1 row with 4 tiles + cash out.
        But that changes the grid shape.
        
        Cleanest solution: We'll just not add a cash-out button and instead
        tell the user to click 🏦 reaction. Actually, let's use a second message.
        
        Simplest correct solution: Make the grid 5x4 (20 tiles) with 4 mines
        and put cash-out on row 5. But user wants 5x5.
        
        Final approach: Discord supports up to 5 action rows, each with up to 5 
        buttons = 25 max. Our grid is exactly 25. So we CAN'T add more buttons.
        We'll handle cash-out via a text command: !cashout
        """
        # Can't add — grid fills all 25 button slots. Cash out handled via command.
        pass

    def _disable_all(self):
        """Disable all buttons."""
        for child in self.children:
            child.disabled = True  # type: ignore

    async def _do_cashout(self, interaction: discord.Interaction | None):
        """Cash out current winnings."""
        self.game_over = True
        winnings = self.current_winnings
        net = winnings - self.bet
        new_bal = add_balance(self.ctx.author.id, net, self.starting)

        self._show_all_mines()
        self._final_embed = discord.Embed(
            title="🏦 Cashed Out!",
            description=(
                f"**Reveals:** {self.reveals}\n"
                f"**Multiplier:** `{self.current_multiplier:.2f}×`\n"
                f"**Winnings:** 🪙 **{winnings:,}** (net +{net:,})\n"
                f"**Balance:** 🪙 **{new_bal:,}**"
            ),
            color=0x2ECC71,
        )
        self._disable_all()

        if interaction:
            await interaction.response.edit_message(
                embed=self._final_embed, view=self
            )
        elif self.message:
            try:
                await self.message.edit(embed=self._final_embed, view=self)
            except Exception:
                pass
        self.stop()


class Mines(commands.Cog, name="Mines"):
    """💣 Navigate a minefield for multiplied winnings!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.starting = bot.app_config.get("starting_balance", 500)
        # Track active games so !cashout works
        self.active_games: dict[int, MinesView] = {}

    @commands.command(name="mines", aliases=["mine", "minesweeper"])
    async def mines(self, ctx: commands.Context, amount: int = None):
        """
        Play Mines! Reveal tiles on a 5×5 grid.
        Each safe reveal increases your multiplier.
        Hit a mine and lose everything!
        Use !cashout to collect your winnings.
        """
        if amount is None:
            await ctx.send(
                embed=discord.Embed(
                    description=(
                        f"**Usage:** `{ctx.prefix}mines [amount]`\n"
                        f"Use `{ctx.prefix}cashout` during a game to collect winnings."
                    ),
                    color=0xFF4444,
                )
            )
            return

        if amount <= 0:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ Bet must be a positive number.",
                    color=0xFF4444,
                )
            )
            return

        bal = get_balance(ctx.author.id, self.starting)
        if amount > bal:
            await ctx.send(
                embed=discord.Embed(
                    description=f"❌ You only have 🪙 **{bal:,}** Coins.",
                    color=0xFF4444,
                )
            )
            return

        # Check for existing active game
        if ctx.author.id in self.active_games:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ You already have an active Mines game! Use `!cashout` to finish it.",
                    color=0xFF4444,
                )
            )
            return

        view = MinesView(ctx, amount, self.starting)
        msg = await ctx.send(
            embed=view.build_embed(),
            content=f"💡 **Tip:** Use `{ctx.prefix}cashout` at any time to collect your winnings!",
            view=view,
        )
        view.message = msg
        self.active_games[ctx.author.id] = view

        # Wait for the game to end, then clean up
        await view.wait()
        self.active_games.pop(ctx.author.id, None)

    @commands.command(name="cashout", aliases=["co"])
    async def cashout(self, ctx: commands.Context):
        """Cash out of your current Mines game."""
        view = self.active_games.get(ctx.author.id)
        if not view or view.game_over:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ You don't have an active Mines game.",
                    color=0xFF4444,
                )
            )
            return

        if view.reveals == 0:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ Reveal at least one tile before cashing out!",
                    color=0xFF4444,
                )
            )
            return

        await view._do_cashout(None)

    @mines.error
    async def mines_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=discord.Embed(
                    description="❌ Please enter a valid number for the bet amount.",
                    color=0xFF4444,
                )
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Mines(bot))
