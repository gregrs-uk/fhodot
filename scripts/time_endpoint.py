"""Function for timing an API endpoint"""

from time import perf_counter
from werkzeug.test import Client
from fhodot.app import app

URL = "http://127.0.0.1:5000/api/suggest?l=-0.14619956627642153&b=51.50793696905042&r=-0.11392722740923403&t=51.52129040029465"
REPEATS = 5

URL = URL.replace("http://127.0.0.1:5000", "")

client = Client(app)

def fetch_and_calculate_average_time(url, repeats=1):
    """Time how long it takes to get URL from API

    If repeats > 1, calculate the average time, excluding the first
    attempt since this often takes longer than subsequent attempts.
    """
    print(f"Timing {url} {repeats} times")

    timings = []
    for _ in range(0, repeats):
        tic = perf_counter()
        response = client.get(url)
        toc = perf_counter()

        string = list(response[0])[0]
        timings.append(toc - tic)
        print(f"{toc - tic:0.4f} seconds for JSON string " +
              f"of length {len(string)}")

    if repeats > 1:
        timings = timings[1:] # discard first
        average = sum(timings) / len(timings)
        print(f"Average time without first attempt: {average:0.4f}")

fetch_and_calculate_average_time(URL, REPEATS)
