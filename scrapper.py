import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlsplit
import os

USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}


def fetch_results(search_term, number_results, language_code):
    assert isinstance(search_term, str), 'Search term must be a string'
    assert isinstance(number_results, int), 'Number of results must be an integer'
    escaped_search_term = search_term.replace(' ', '+')

    google_url = 'https://www.google.com/search?q={}&num={}&hl={}'.format(escaped_search_term, number_results,
                                                                          language_code)
    print(google_url)
    response = requests.get(google_url, headers=USER_AGENT)
    response.raise_for_status()

    return search_term, response.text


def parse_results(html, keyword):
    print("Search Terms: " + keyword)
    soup = BeautifulSoup(html, 'html.parser')

    rank = 1
    result_block = soup.find_all('div', attrs={'class': 'g'})
    for result in result_block:

        link = result.find('a', href=True)
        title = result.find('h3', attrs={'class': 'r'})
        description = result.find('span', attrs={'class': 'st'})
        if link and title:
            link = link['href']
            title = title.get_text()
            if description:
                description = description.get_text()
            if link != '#':
                # Find any email addresses from the link
                emails, new_urls = scrape_link(link)

                result = {'keyword': keyword,
                          'rank': rank,
                          'link': link,
                          'title': title,
                          'description': description,
                          'emails': emails,
                          'new_urls': new_urls}

                # Write the results to the file
                append_file(result, keyword)

                rank += 1


def scrape_google(search_term, number_results, language_code):
    try:
        # Search google for the search terms
        keyword, html = fetch_results(search_term, number_results, language_code)

        # Parse the result from the search result
        parse_results(html, keyword)
    except AssertionError:
        print("Incorrect arguments parsed to function")
    except requests.HTTPError:
        print("You appear to have been blocked by Google")
    except requests.RequestException:
        print("Appears to be an issue with your connection")
    except Exception:
        print("Error scrapping google")


def scrape_link(url):
    print("Processing %s" % url)
    emails = []
    new_urls = []
    try:
        response = requests.get(url)
    except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
        # ignore pages with er
        return emails, new_urls
    except AssertionError:
        print("Incorrect arguments parsed to function: " + url)
        return emails, new_urls
    except requests.HTTPError:
        print("Bad Link" + url)
        return emails, new_urls
    except requests.RequestException:
        print("Appears to be an issue with your connection" + url)
        return emails, new_urls
    except Exception:
        print("Error checking URL: " + url)
        return emails, new_urls

    # extract base url to resolve relative links
    parts = urlsplit(url)
    base_url = "{0.scheme}://{0.netloc}".format(parts)
    path = url[:url.rfind('/') + 1] if '/' in parts.path else url

    response = requests.get(url, headers=USER_AGENT)
    response.raise_for_status()

    # extract all email addresses and add them into the resulting set
    emails.append(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))

    soup = BeautifulSoup(response.text, 'html.parser')

    # find and process all the anchors in the document
    for anchor in soup.find_all("a"):
        # extract link url from the anchor
        link = anchor.attrs["href"] if "href" in anchor.attrs else ''
        # resolve relative links
        if link.startswith('/'):
            link = base_url + link
        elif not link.startswith('http'):
            link = path + link
        # add the new url to the queue if it was not enqueued nor processed yet
        if not link in new_urls:
            new_urls.append(link)

    return emails, new_urls


def append_file(results, keywords):
    # Use the keyword for the file name
    file_name = keywords.replace(' ', '_')
    file_name += ".txt"
    file_name = os.path.join("results", file_name)

    # Write the data as JSON with print pretty
    with open(file_name, "a+") as f:
        f.write(json.dumps(results, indent=4, sort_keys=True))


if __name__ == '__main__':
    #search_terms = "adcp dvl"
    search_terms = "david.salazar@ucsb.edu adcp"
    scrape_google(search_terms, 100, "en")



