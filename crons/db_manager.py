import json
import logging
import os
import re
import time

import requests
from schedule import run_pending, repeat, every
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from enums.rarityenum import RarityEnum
from models.card import Card

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@repeat(every(1).minutes)
def manage_db():
    engine = create_engine(
        f'postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}/{os.environ['DB_NAME']}')
    json_resp = json.loads(
        requests.get('https://api.dotgg.gg/cgfw/getcards?game=riftbound&mode=indexed&cache=1157').text)
    card_list = [dict(zip(json_resp['names'], items)) for items in json_resp['data']]
    with Session(engine) as session:
        for card in card_list:
            try:
                rarity = RarityEnum[card['rarity'].upper()].value
                regex = re.compile(r':(rb_[a-z0-9_]+):')
                card_effect = card['effect']
                if card_effect is not None and regex.search(card_effect):
                    card_effect = re.sub(r":(rb_[a-z0-9_]+):", r'<img src="https://static.dotgg.gg/riftbound/text/\1.svg">', card_effect)

                stmt = insert(Card).values(name=card['name'], effect=card_effect,
                                           cost=int(card['cost'] if card['cost'] is not None and card['cost'] != '' and not card['cost'].isspace() else 0),
                                           type=card['type'],
                                           might=int(card['might'] if card['might'] is not None and card['might'] != '' and not card['might'].isspace() else 0),
                                           set_name=card['set_name'],
                                           rarity=rarity, image=card['image'], color=card['color'], tags=card['tags'],
                                           code=card['id'])

                stmt = stmt.on_conflict_do_update(constraint='cards_code_uk',
                                                  set_={c.name: getattr(insert(Card).excluded, c.name) for c in
                                                        Card.__table__.columns if c.name not in ("id", "code")})
                session.execute(stmt)
            except Exception as e:
                logger.error('-----------------------------------------')
                logger.error(f'Erro na carta {card['id']}')
                logger.exception(e)
                logger.error('-----------------------------------------')
                continue
            session.commit()
            logger.info('Atualização finalizada')


while True:
    run_pending()
    time.sleep(1)
