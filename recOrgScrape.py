import requests
import json
import bs4 as bs
import os
import sys
import time
import datetime


def get_permit_details(permit_name):
    """the permit_number and division_numbers are as follows"""
    perms = {
        'Middle': {
            'permit_number': '234623',
            'division_number': '377',
            'start_date': '2021-06-23',
            'end_date': '2021-07-31'
        },
        'test': {
            'permit_number': '234623',
            'division_number': '377',
            'start_date': '2021-04-23',
            'end_date': '2021-07-31'
        },
        'Main': {
            'permit_number': '234622',
            'division_number': '375',
            'start_date': '2021-06-1',
            'end_date': '2021-07-31'
        },
        'Selway': {
            'permit_number': '234624',
            'division_number': '378',
            'start_date': '2021-06-20',
            'end_date': '2021-07-15'
        },
        'HellsCanyon': {
            'permit_number': '234625',
            'division_number': '379',
            'start_date': '2021-06-1',
            'end_date': '2021-07-31'
        }
    }
    return [perms[permit_name][key] for key in ('permit_number', 'division_number', 'start_date', 'end_date')]


def get_session():
    return requests.session()


def get_access_token(session, username, password):
    headers = {
        'authority': 'www.recreation.gov',
        'accept': 'application/json, text/plain, */*',
        'pragma': 'no-cache',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'content-type': 'application/json;charset=UTF-8',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
        'origin': 'https://www.recreation.gov',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.recreation.gov/',
        'accept-language': 'en-US,en;q=0.9',
        'cookie': '_ga=GA1.2.1968320311.1613006065; _gid=GA1.2.111559654.1613248936; QSI_SI_0Ogo1301MUj7HeJ_intercept=true; _gat_UA-112750441-5=1; QSI_HistorySession=https%3A%2F%2Fwww.recreation.gov%2F~1613326654122',
    }
    data = {
        "username": username,
        "password": password,
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
    }
    data = json.dumps(data)
    response = session.post(
        'https://www.recreation.gov/api/accounts/login', headers=headers, data=data)
    access_key = response.json().get('access_token')
    access_token = 'Bearer ' + access_key
    return access_token


def get_recaptcha_value(session):
    headers = {
        'authority': 'www.google.com',
        'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'x-client-data': 'CKS1yQEIirbJAQimtskBCMS2yQEIqZ3KAQj4x8oBCKPNygEI3NXKAQjXm8sBCKecywEI5JzLAQipncsB',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'iframe',
        'referer': 'https://www.recreation.gov/',
        'accept-language': 'en-US,en;q=0.9',
    }
    params = (
        ('ar', '1'),
        ('k', '6Ld0BogUAAAAAGDL0sfz1wVdmuae18krNNQS6vW5'),
        ('co', 'aHR0cHM6Ly93d3cucmVjcmVhdGlvbi5nb3Y6NDQz'),
        ('hl', 'en'),
        ('v', '2Mfykwl2mlvyQZQ3PEgoH710'),
        ('size', 'invisible'),
        ('cb', '40wucb2yax90'),
    )
    response = session.get(
        'https://www.google.com/recaptcha/api2/anchor', headers=headers, params=params)
    soup = bs.BeautifulSoup(response.text, "html.parser")
    token = soup.find('input', attrs={"id": "recaptcha-token"})
    value_long = token.get('value')
    value = value_long[0:484]
    return value


def format_url(permit_number, division_number, start_date, end_date):
    url = f"https://www.recreation.gov/api/permits/{permit_number}/divisions/{division_number}/availability?start_date={start_date}T08:00:00.000Z&end_date={end_date}T00:00:00.000Z&commercial_acct=false&is_lottery=false"
    return url


def request_permit_availability(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
    response = requests.get(url, headers=headers)
    raw_data = json.loads(response.text)
    data = raw_data.get('payload')
    next_available_date = data.get('next_available_date')
    return next_available_date[0:10]


def next_date_is_available(next_date, end_date):
    return next_date != end_date


def check_loop(url, end_date):
    date_is_available = False
    next_available = None
    counter = 1
    while date_is_available == False:

        try:
            if counter % 500 == 0:
                print(counter)
                print(datetime.datetime.now().time())
            next_available = request_permit_availability(url)
            if next_date_is_available(next_available, end_date):
                date_is_available = True
            counter += 1
            time.sleep(.1)
        except Exception as e:
            print(f"error sleepy time: {e}")
            time.sleep(5)
    return next_available


def book_trip(session, access_token, recaptcha_token, day_to_book, permit_number, division_number):
    headers = {
        'authority': 'www.recreation.gov',
        'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
        'pragma': 'no-cache',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded',
        'accept': 'application/json, text/plain, */*',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'authorization':  access_token,
        'origin': 'https://www.recreation.gov',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.recreation.gov/permits/234623',
        'accept-language': 'en-US,en;q=0.9',
        'cookie': '_ga=GA1.2.1968320311.1613006065; _gid=GA1.2.111559654.1613248936; QSI_SI_0Ogo1301MUj7HeJ_intercept=true; _gat_UA-112750441-5=1; QSI_HistorySession=https%3A%2F%2Fwww.recreation.gov%2F~1613326654122',
    }

    data = {
        "gate_a": {
            "value": recaptcha_token,
            "description": "permitVenueBooking",
            "terminal": "east",
            "success": True
        },
        "issuance": {
            "permit_id": permit_number,
            "division_id": division_number,
            "user_id": "bsjuampvgdu0008sfth0",
            "start_date": day_to_book + "T00:00:00.000Z",
            "status": 0,
            "animals": [],
            "pets": [],
            "equipments": [],
            "guides": [],
            "itinerary": [
                {
                    "start_date": day_to_book + "T00:00:00.000Z",
                    "end_date": day_to_book + "T00:00:00.000Z",
                    "division_id": division_number
                }
            ],
            "sales_channel_type": 0
        }
    }
    data = json.dumps(data)
    response = session.post(
        f"https://www.recreation.gov/api/permits/{permit_number}/issuances", headers=headers, data=data)
    return response


def main():
    permit_number, division_number, start_date, end_date = get_permit_details(
        sys.argv[1])

    s = get_session()
    access_token = get_access_token(
        s, os.environ['REC_USER_NAME'], os.environ['REC_PASS'])
    recaptcha_token = get_recaptcha_value(s)
    url = format_url(permit_number, division_number, start_date, end_date)
    print('url:', url)

    next_available = check_loop(url, end_date)

    trip_book_response = book_trip(
        s, access_token, recaptcha_token, next_available, permit_number, division_number)
    print('trip_book_response:', trip_book_response)
    for x in range(2):
        os.system("say 'Wake Up'")


if __name__ == '__main__':
    main()
