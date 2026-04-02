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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@repeat(every(1).seconds)
def manage_db():
    engine = create_engine(
        f'postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}/{os.environ['DB_NAME']}')
    json_resp = json.loads(
        requests.get('https://api.dotgg.gg/cgfw/getcards?game=riftbound&mode=indexed').text)
    card_list = [dict(zip(json_resp['names'], items)) for items in json_resp['data']]
    with Session(engine) as session:
        logger.info('Atualização iniciada')
        for card in card_list:
            try:
                rarity__upper = card['rarity'].upper()
                is_token = False
                is_promo = False
                match rarity__upper:
                    case 'TOKEN':
                        is_token = True
                    case 'PROMO':
                        is_promo = True
                    case _:
                        rarity = RarityEnum[rarity__upper].value

                regex = re.compile(r':(rb_[a-z0-9_]+):')
                card_effect = card['effect']
                if card_effect is not None and regex.search(card_effect):
                    card_effect = re.sub(r":(rb_[a-z0-9_]+):",
                                         r'<img src="https://static.dotgg.gg/riftbound/text/\1.svg">', card_effect)

                card_cost_ = card['cost']
                card_supertype_ = card['supertype']
                card_might_ = card['might']
                stmt = insert(Card).values(name=card['name'], effect=card_effect,
                                           cost=int(
                                               card_cost_ if card_cost_ is not None and card_cost_ != '' and not card_cost_.isspace() else 0),
                                           type=card['type'],
                                           supertype=card_supertype_ if card_supertype_ is not None and card_supertype_ != '' else None,
                                           might=int(
                                               card_might_ if card_might_ is not None and card_might_ != '' and not card_might_.isspace() else 0),
                                           set_name=card['set_name'],
                                           rarity=rarity, is_token=is_token, is_promo=is_promo, image=card['image'],
                                           color=card['color'], tags=card['tags'],
                                           code=card['id'])

                stmt = stmt.on_conflict_do_update(constraint='cards_code_uk',
                                                  set_={c.name: getattr(insert(Card).excluded, c.name) for c in
                                                        Card.__table__.columns if c.name not in ("id", "code")})
                session.execute(stmt)
            except Exception as e:
                logger.error('-----------------------------------------')
                logger.error(f'Erro na carta {card['name']} - {card['id']}')
                logger.exception(e)
                logger.error('-----------------------------------------')
                continue
            session.commit()
        logger.info('Atualização finalizada')


while True:
    run_pending()
    time.sleep(1)
