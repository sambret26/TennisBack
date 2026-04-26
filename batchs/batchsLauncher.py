from discord import discordBusiness, discordNotif
from batchs import batchs
from repositories.SettingRepository import SettingRepository

from logger.logger import log, BATCH

settingRepository = SettingRepository()

async def pgwLoop(bot):
    if settingRepository.getBatchsActive() is False:
        return
    log.info(BATCH, "Lancement du batch pgw")
    await discordBusiness.pgw(bot)
    log.info(BATCH, "Fin du batch pgw")

async def inscriptionsLoop():
    if settingRepository.getBatchsActive() is False:
        return
    log.info(BATCH, "Lancement du batch inscriptions")
    batchs.inscriptions(True)
    log.info(BATCH, "Fin du batch inscriptions")

async def convocationLoop():
    if settingRepository.getBatchsActive() is False:
        return
    log.info(BATCH, "Lancement du batch convocations")
    batchs.convocations()
    log.info(BATCH, "Fin du batch convocations")

async def sendNotifLoop(bot):
    if settingRepository.getBatchsActive() is False:
        return
    log.info(BATCH, "Lancement du batch sendNotif")
    await discordNotif.sendNotif(bot)
    log.info(BATCH, "Fin du batch sendNotif")

def updateMatchLoop():
    if settingRepository.getBatchsActive() is False:
        return
    log.info(BATCH, "Lancement du batch updateMatch")
    batchs.updateMatch()
    log.info(BATCH, "Fin du batch updateMatch")

async def updateCalLoop():
    if settingRepository.getBatchsActive() is False:
        return
    log.info(BATCH, "Lancement du batch updateCal")
    batchs.updateCalendar()
    log.info(BATCH, "Fin du batch updateCal")