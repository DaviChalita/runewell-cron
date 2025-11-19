import time

from schedule import every, repeat, run_pending


@repeat(every().day().at("24:00"))
def manage_db():
    print("teste")

while True:
    run_pending()
    time.sleep(1)
