import os
import asyncio
import logging
import time

from dotenv import load_dotenv
import telegram
import requests
from requests.exceptions import ConnectionError, ReadTimeout


def main():
    load_dotenv()
    tg_token = os.getenv('TG_BOT_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    dvmn_token = os.getenv('DVMN_TOKEN')
    if not tg_token:
        logging.error('Telegram token not found')
        exit()

    logging.basicConfig(level=logging.INFO)

    long_pulling_url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {dvmn_token}'}
    params = {'timestamp': None}

    bed_review_message_template = (
        'У Вас проверили работу «{new_attempt[lesson_title]}».\n\n'
        'К сожалению, в работе найдены ошибки.\n\n'
        'Cсылка на урок: {new_attempt[lesson_url]}.'
    )

    good_review_message_template = (
        'У Вас проверили работу «{new_attempt[lesson_title]}».\n\n'
        'Преподавателю всё понравилось, можете приступать к следующему уроку!\n\n'
        'Cсылка на урок: {new_attempt[lesson_url]}.'
    )

    fail_connection_count = 0

    bot = telegram.Bot(tg_token)
    while True:
        try:
            response = requests.get(long_pulling_url, params=params, headers=headers, timeout=100)
        except ReadTimeout:
            continue
        except ConnectionError:
            logging.warning('Connection failure')
            fail_connection_count += 1
            if fail_connection_count > 10:
                time.sleep(10)
            continue
        except:
            logging.error('Something wrong')
            time.sleep(10)
            continue

        fail_connection_count = 0
        if response.ok:
            works = response.json()
            if works['status'] == 'timeout':
                params = {'timestamp': works['timestamp_to_request']}
                logging.info('Server timeout received')
            elif works['status'] == 'found':
                params = {'timestamp': works['last_attempt_timestamp']}
                logging.info('Review found')
                for new_attempt in works['new_attempts']:

                    if new_attempt['is_negative']:
                        message = bed_review_message_template.format(new_attempt=new_attempt)
                    else:
                        message = good_review_message_template.format(new_attempt=new_attempt)

                    bot.send_message(text=message, chat_id=chat_id)
            else:
                logging.warning('Unrecognized response')
        else:
            logging.error('Bed request')


if __name__ == '__main__':
    main()
