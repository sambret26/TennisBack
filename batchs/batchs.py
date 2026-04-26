
from models.Player import Player
from models.Team import Team
from models.Message import Message
from models.PlayerBalance import PlayerBalance
from models.PlayerCategories import PlayerCategories
from models.Convocation import Convocation
from repositories.CompetitionRepository import CompetitionRepository
from repositories.CategoryRepository import CategoryRepository
from repositories.PlayerRepository import PlayerRepository
from repositories.TeamRepository import TeamRepository
from repositories.RankingRepository import RankingRepository
from repositories.MessageRepository import MessageRepository
from repositories.PlayerBalanceRepository import PlayerBalanceRepository
from repositories.PlayerCategoriesRepository import PlayerCategoriesRepository
from repositories.ConvocationRepository import ConvocationRepository
from repositories.MatchRepository import MatchRepository
from moja import mojaService

playerRepository = PlayerRepository()
teamRepository = TeamRepository()
categoryRepository = CategoryRepository()
competitionRepository = CompetitionRepository()
rankingRepository = RankingRepository()
messageRepository = MessageRepository()
playerBalanceRepository = PlayerBalanceRepository()
playerCategoriesRepository = PlayerCategoriesRepository()
convocationRepository = ConvocationRepository()
matchRepository = MatchRepository()

def inscriptions(sendNotif):
    homologationId = competitionRepository.getHomologationId()
    players, playerCategories = getPlayers(homologationId)
    if players :
        updateDBPlayers(players, sendNotif)
    playersMap = playerRepository.getPlayersIdMap()
    teams = getTeams(homologationId, playersMap)
    if teams :
        updateDBTeams(teams)
    if not playerCategories :
        return False
    inscriptionsIds = PlayerCategoriesRepository.getInscriptionsId()
    playersCategoriesToAdd = []
    for playerCategory in playerCategories:
        playerId = playersMap.get(playerCategory.playerId)
        if playerId is None:
            #log.error(BATCH, f"Player {playerCategorie.playerId} not found")
            continue
        playerCategory.playerId = playerId
        if playerCategory.inscriptionId in inscriptionsIds:
            continue
        playersCategoriesToAdd.append(playerCategory)
    playerCategoriesRepository.addPlayerCategories(playersCategoriesToAdd)
    return True

def convocations():
    convacationsDB = convocationRepository.getConvocationsMap()
    categories = categoryRepository.getAllCategories()
    playersMap = playerRepository.getPlayerCrmIdMap()
    matchesMap = matchRepository.getMatchesMap()
    convocationsToCreate = []
    messages = []
    for categorie in categories:
        convocationsMoja = mojaService.getConvocations(categorie.fftId)
        for convocationMoja in convocationsMoja:
            convocationDB = convacationsDB.get(convocationMoja['conId'])
            if convocationDB is None:
                newConvo = Convocation.fromFFT(convocationMoja)
                if newConvo.crmId is not None:
                    convocationsToCreate.append(newConvo)
                if newConvo.state == "ACPT" and newConvo.crmId is not None:
                    addConvoMessage(messages, playersMap, matchesMap, newConvo)
                elif newConvo.state == "NCFR" and newConvo.crmId is not None:
                    addSendConvoMessage(messages, playersMap, matchesMap, newConvo)
            elif convocationDB.state != convocationMoja['statutConvocationCode']:
                convocationDB.state = convocationMoja['statutConvocationCode']
                if convocationMoja['statutConvocationCode'] == "ACPT" and convocationDB.crmId is not None:
                    addConvoMessage(messages, playersMap, matchesMap, convocationDB)
                if convocationMoja['statutConvocationCode'] == "NCFR" and convocationDB.crmId is not None:
                    addSendConvoMessage(messages, playersMap, matchesMap, convocationDB)
    convocationRepository.addConvocations(convocationsToCreate)
    messageRepository.addMessages(messages)
    return True

def updateMatch():
    mojaService.updateAllMatches()

def updateCalendar():
    return None #TODO : Implement calendar batch

def getPlayers(homologationId):
    ranksMapSimple = rankingRepository.getRankingMapSimple()
    categoriesMap = categoryRepository.getCategoriesMap()
    playerCategories = []
    players = []
    playersFromMoja = mojaService.getPlayersInfos(homologationId)
    if not playersFromMoja: 
        return None, None
    for player in playersFromMoja:
        addPlayerInPlayersList(players, playerCategories, player, categoriesMap, ranksMapSimple)
    return players, playerCategories

def getTeams(homologationId, playersMap):
    teams = []
    teamsFromMoja = mojaService.getTeamsInfos(homologationId)
    if not teamsFromMoja:
        return None
    for team in teamsFromMoja:
        addTeamsInLists(teams, team, playersMap)
    return teams

def addPlayerInPlayersList(players, playerCategories, player, categoriesMap, ranksMapSimple):
    newPlayer = Player.fromFFT(player)
    newPlayer.ranking = ranksMapSimple.get(player['echelonSimpleUpdated'])
    newPlayer.rankingId = newPlayer.ranking.id
    for category in player['epreuves']:
        if category['statutInscriptionCode'] != "PAR": 
            continue
        categoryInDB = categoriesMap.get(category['eprId'])
        categoryInsId = category['insId'] if 'insId' in category else category.get('jseId')
        newPlayerCategories = PlayerCategories(newPlayer.fftId, categoryInDB.id, categoryInsId)
        playerCategories.append(newPlayerCategories)
        #TODO : Amount
        newPlayer.categories.append(categoryInDB)
    addPlayer(players, newPlayer)

def addTeamsInLists(teams, team, playersMap):
    player1Id = playersMap[team['jouId1']]
    player2Id = playersMap[team['jouId2']]
    ranking = team["poidsInscription"]
    fftId = team["insId"]
    newTeam = Team(fftId, player1Id, player2Id, ranking)
    teams.append(newTeam)

def addPlayer(players, newPlayer):
    for player in players:
        if newPlayer.fftId == player.fftId:
            if player.rankingId != newPlayer.rankingId:
                player.rankingId = newPlayer.rankingId
            return
    players.append(newPlayer)

def updatePlayerBalance(player, amount):
    if not player.balance :
        player.balance = PlayerBalance.fromPlayer(player, amount)
        return
    if amount == 0 :
        return
    player.balance.remainingAmount += amount
    player.balance.finalAmount += amount
    player.balance.initialAmount += amount

def updateDBPlayers(players, sendNotif):
    playersMap = playerRepository.getPlayersMap()
    newPlayers = []
    messages = []
    newRankingsPlayers = []
    for player in players:
        playerInDB = playersMap.get(player.fftId)
        if playerInDB:
            checkCategories(player, playerInDB, sendNotif)
            if player.isDifferent(playerInDB):
                if playerInDB.rankingId != player.rankingId:
                    newRankingsPlayers.append((player, playerInDB.rankingId))
                player.id = playerInDB.id
                playerRepository.updatePlayer(playerInDB.id, player)
            playersMap.pop(player.fftId)
        else:
            newPlayers.append(player)
    for player in playersMap.values():
        deletePlayer(messages, player)
    if sendNotif:
        sendMessages(newPlayers, newRankingsPlayers)
    if newPlayers :
        playerRepository.addPlayers(newPlayers)
    if messages :
        messageRepository.addMessages(messages)

def createPlayer(player):
    return {
        'id' : player.id,
        'fullName' : player.getFullName(),
        'ranking' : player.ranking.simple if player.ranking else None,
        'club' : player.club,
        'categories' : player.categories
    }

def deletePlayer(messages, player):
    if(playerRepository.deletePlayer(player)):
        msg = f"Désinscription de {player.getFullName()} ({player.club})"
        if player.ranking :
            msg += f" classé(e) {player.ranking.simple}"
        messages.append(Message("G", msg))
        for category in player.categories:
            messages.append(Message(category.code, msg))
    else:
        player.toDelete = True
        playerRepository.updatePlayer(player.id, player)
        msg = f"Tentative de suppression de {player.getFullName()} ({player.club})"
        if player.ranking :
            msg += f" classé(e) {player.ranking.simple}"
        msg += " échouée"
        messages.append(Message("ERROR", msg))

def updateDBTeams(teams):
    teamsMap = teamRepository.getTeamsMap()
    newTeams = []
    for team in teams:
        teamInDB = teamsMap.get(team.fftId)
        if teamInDB:
            teamsMap.pop(teamInDB.fftId)
        else:
            newTeams.append(team)
    if newTeams:
        teamRepository.addTeams(newTeams)
    if teamsMap:
        teamRepository.deleteTeams([team.id for team in teamsMap.values()])

# def updateDBPlayerCategorie(playerCategories):
#     toAdd = []
#     inscriptionsId = playerCategoriesRepository.getInscriptionsId()
#     for playerCategorie in playerCategories:
#         if not playerCategorie.inscriptionId in inscriptionsId:
#             toAdd.append(playerCategorie)
#     playerCategoriesRepository.addPlayerCategories(toAdd)

def checkCategories(player, playerInDB, sendNotif):
    newCategories = player.categories
    oldCategories = playerInDB.categories
    messages = []
    handleNewCategories(player, newCategories, oldCategories, messages, sendNotif)
    handleOldCategories(player, newCategories, oldCategories, messages, sendNotif)
    if len(messages) > 0 :
        #playerBalanceRepository.updatePlayerBalanceByPlayerId(playerInDB.id, player.balance)
        if sendNotif:
            messageRepository.addMessages(messages)

def handleNewCategories(player, newCategories, oldCategories, messages, sendNotif):
    for category in newCategories:
        if category not in oldCategories:
            if sendNotif:
                msg = f"Nouvelle inscription : {player.getFullName()} ({player.club})"
                if player.ranking :
                    msg += f" classé(e) {player.ranking.simple}"
                messages.append(Message(category.code, msg))

def handleOldCategories(player, newCategories, oldCategories, messages, sendNotif):
    for category in oldCategories:
        if category not in newCategories:
            playerCategoriesRepository.deletePlayerCategoryByPlayerIdAndCategoryId(player.id, category.id)
            if sendNotif:
                msg = f"Désinscription de {player.getFullName()} ({player.club})"
                if player.ranking :
                    msg += f" classé(e) {player.ranking.simple}"
                messages.append(Message(category.code, msg))

def addConvoMessage(messages, playersMap, matchesMap, convo):
    playerName = playersMap.get(convo.crmId).getFullName()
    match = matchesMap.get(convo.matchId)
    if match:
        date = match.getFormattedDate()
        hour = match.getFormattedHour()
        message = Message("CONVO", f"{playerName} à accepté sa convocation pour le match {match.label} le {date} à {hour}")
    else:
        message = Message("CONVO", f"{playerName} à accepté sa convocation pour un match non identifié")
    messages.append(message)

def addSendConvoMessage(messages, playersMap, matchesMap, convo):
    playerName = playersMap.get(convo.crmId).getFullName()
    match = matchesMap.get(convo.matchId)
    if match:
        date = match.getFormattedDate()
        hour = match.getFormattedHour()
        message = Message("SEND_CONVO", f"{playerName} à été convoqué pour le match {match.label} le {date} à {hour}")
    else:
        message = Message("SEND_CONVO", f"{playerName} à été convoqué pour un match non identifié")
    messages.append(message)

def sendMessages(newPlayers, newRankingsPlayers):
    messages = []
    for player in newPlayers:
        msg = f"Nouvelle inscription : {player.getFullName()} ({player.club})"
        if player.ranking :
            msg += f" classé(e) {player.ranking.simple}"
        messages.append(Message("G", msg))
        for category in player.categories:
            messages.append(Message(category.code, msg))
    for player, rankingId in newRankingsPlayers:
        ranking = rankingRepository.getRankingById(rankingId)
        if ranking == player.ranking:
            continue
        msg = f"Reclassement de {player.getFullName()} ({ranking.simple} => {player.ranking.simple})"
        messages.append(Message("G", msg))
    messageRepository.addMessages(messages)