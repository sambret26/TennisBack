from models.Player import Player
from models.PlayerCategories import PlayerCategories
from database import db
from logger.logger import log, BATCH
from sqlalchemy.exc import IntegrityError, PendingRollbackError

class PlayerRepository:

    #GETTERS
    @staticmethod
    def getAllPlayers():
        return Player.query.all()

    @staticmethod
    def getAllPlayerNames():
        results = Player.query.with_entities(Player.id, Player.firstName, Player.lastName).all()
        players = [Player(id=r[0], firstName=r[1], lastName=r[2]) for r in results]
        return players

    @staticmethod
    def getPlayerById(playerId):
        return Player.query.get(playerId)

    @staticmethod
    def getNumberPlayers():
        return Player.query.count()

    @staticmethod
    def getRankingIds():
        results = Player.query.with_entities(Player.rankingId).all()
        return [result[0] for result in results]

    @staticmethod
    def getRankingIdsByCategoryId(categoryId):
        results = db.session.query(Player.rankingId).select_from(Player)\
            .join(PlayerCategories, Player.id == PlayerCategories.playerId)\
            .filter(PlayerCategories.categoryId == categoryId).all()
        return [result[0] for result in results]

    @staticmethod
    def getPlayersIdMap():
        return {player.fftId: player.id for player in Player.query.all()}

    @staticmethod
    def getPlayersMap():
        return {player.fftId: player for player in Player.query.filter_by(toDelete=False).all()}

    @staticmethod
    def getPlayersNamesMap():
        return {player.lastName + '_' + player.firstName: player for player in Player.query.all()}

    @staticmethod
    def getPlayerCrmIdMap():
        return {player.crmId: player for player in Player.query.all()}
    
    #ADDERS
    @staticmethod
    def addPlayer(player):
        db.session.add(player)
        db.session.commit()
        return player

    @staticmethod
    def addPlayers(players):
        for player in players:
            player.categories = []
        db.session.add_all(players)
        db.session.commit()

    #SETTERS
    @staticmethod
    def updatePlayer(playerId, player):
        Player.query.filter_by(id=playerId).update(player.toDictForDB())
        db.session.commit()

    @staticmethod
    def updatePlayerFromBatch(player):
        Player.query.filter_by(fftId=player.fftId).update(player.toDictForInfos())
        db.session.commit()

    #DELETERS
    @staticmethod
    def deletePlayerById(playerId):
        Player.query.filter_by(id=playerId).delete()
        db.session.commit()

    @staticmethod
    def deletePlayer(player):
        try:
            db.session.delete(player)
            db.session.commit()
            return True
        except (IntegrityError, PendingRollbackError, Exception):
            db.session.rollback()
            log.error(BATCH, f"Error deleting player {player.id}")
            return False

    @staticmethod
    def deleteAllPlayers():
        Player.query.delete()
        db.session.commit()