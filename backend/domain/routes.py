from domain.airslots_api import router as airslots
from domain.battery_logs_api import router as battery_logs
from domain.reserves_api import router as reserves
from domain.switchcards_api import router as switchcards

routers = (airslots, battery_logs, reserves, switchcards,)
