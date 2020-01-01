import asyncpg

from cogs.rpg.objects.account import Account


class AccountManager:

    def __init__(self, bot):
        self.bot = bot

    async def cache_accounts(self):

        self.bot.accounts.clear()

        accounts = await self.bot.db.fetch("SELECT * FROM accounts")
        for entry in accounts:
            items = await self.bot.db.fetch("SELECT * FROM inventory WHERE owner = $1", entry["id"])

            self.bot.accounts[entry["id"]] = Account(dict(entry), items)

        print(f"\n[RPG] Cached {len(self.bot.accounts)} out of {len(accounts)} accounts.")

    async def cache_account(self, account_id: int):

        account = await self.fetch_account(account_id)

        if account:
            self.bot.accounts[account_id] = account
        else:
            raise KeyError(f"Unable to cache account, No account found with id {account_id}")

    def get_account(self, account_id: int):

        try:
            return self.bot.accounts.get(account_id)
        except ValueError:
            return None

    async def fetch_account(self, account_id: int):

        account = await self.bot.db.fetchrow("SELECT * FROM accounts where id = $1", account_id)
        items = await self.bot.db.fetch("SELECT * FROM inventory where owner = $1", account_id)

        if not account:
            raise KeyError(f"Unable to fetch account, No account found with id {account_id}")

        return Account(dict(account), items)

    async def create_account(self, ctx, user_id: int):
        try:
            await self.bot.db.execute(f"INSERT INTO accounts VALUES ($1, 'bg_default', 1000, 1000)", user_id)

            query = 'INSERT INTO inventory (id, owner, count, name, power, slot) VALUES ($1, $2, $3, $4, $5, $6)'
            values =  [(1, user_id, 1, f"{ctx.author.name}'s Starter boots", 6, "boots"),
                       (101, user_id, 1, f"{ctx.author.name}'s Starter chestplate", 6, "chestplate"),
                       (201, user_id, 1, f"{ctx.author.name}'s Starter helmet", 6, "helmet")]
            await self.bot.db.executemany(query, values)

            await self.cache_account(user_id)
            return await ctx.send(f"Account created with ID `{user_id}`")

        except asyncpg.UniqueViolationError:
            return await ctx.send("You already have an account.")

    async def delete_account(self, ctx, user_id: int):

        account = ctx.account
        if not account:
            return await ctx.send("You don't have an account.")

        await self.bot.db.execute(f"DELETE FROM accounts WHERE id = $1", user_id)
        await self.bot.db.execute(f"DElETE FROM inventory WHERE owner = $1", user_id)
        self.bot.accounts.pop(user_id, None)

        return await ctx.send("Deleted your account.")
