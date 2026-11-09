"""Giveaway posts and their participant registry."""

from sqlalchemy.engine import Connection

from db.giveaway_models import Giveaway, GiveawayParticipant

from .engine import Migration


def _migration_0109_giveaways(connection: Connection) -> None:
    Giveaway.__table__.create(connection, checkfirst=True)
    GiveawayParticipant.__table__.create(connection, checkfirst=True)


CHAIN_0109_GIVEAWAYS = [
    Migration(
        id="0109_giveaways",
        description="Giveaway posts published to the group plus participant tracking",
        upgrade=_migration_0109_giveaways,
    )
]
