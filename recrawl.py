"""
Total reCrawl Regex Crawler

Crawls a website and extracts (US) phone numbers, links, and email addresses.

@author: Andy Hudock <ahudock@pm.me>

Usage:
    python recrawl.py <starting_url> [--depth <depth>] [--follow-external] [--delay <delay>]

Arguments:
    starting_url Starting URL for crawler

Options:
    --depth <depth>   Depth to crawl (default: 2)
    --follow-external Follow links to different domains if provided
    --delay <delay>   Delay between requests in seconds (default: 1)

TODO:
    - Support regex as arg?
    - Specify phone region?
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse, urljoin
import argparse

# Track visited URLs to avoid cycles
visited_urls = set()

def fetch_html(url):
    """
    Fetch HTML content from an URL

    :param str url: URL to fetch
    :return str: HTML content of the page, or an empty string if fetching failed
    """
    try:
        response = requests.get(url)
        response.raise_for_status() # Ensure we notice bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return ""

def find_strings(html, search_string):
    """
    Find specified strings in HTML content
    
    :param str html: HTML content to search for strings
    :param str search_string: String to search for in HTML content
    :return list: Instances of specified strings found in HTML content
    """
    # Find instances of the specified string
    instances = re.findall(search_string, html, re.IGNORECASE)
    return instances

def find_phone_numbers(html):
    """
    Find phone numbers in HTML content
    
    :param str html: HTML content to search for phone numbers
    :return list: Phone numbers found in HTML content
    """
    pattern = re.compile(r'''
        (\+?\d{1,3}[\s.-]?)?                # Optional country code
        (\(?\d{3}\)?[\s.-]?)?               # Optional area code with parentheses
        (\d{3}[\s.-]?\d{4}|\d{7}|\d{10,11}) # Main phone number
    ''', re.VERBOSE)

    # Find all potential phone numbers
    matches = pattern.findall(html)

    # Validate potential phone numbers and filter unique numbers
    valid_numbers = set()
    for match in matches:
        phone_number = "".join(match)
        if len(re.sub(r'\D', '', phone_number)) in (10, 11): # Include only 10 or 11-digit numbers
            valid_numbers.add(phone_number)

    return list(valid_numbers)

def find_email_addresses(html):
    """
    Find and validate email addresses in HTML content
    
    :param str html: HTML content to search for email addresses
    :return list: Valid email addresses found in HTML content
    """
    # Comprehensive email pattern matching regex
    pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    # Find potential email addresses
    matches = pattern.findall(html)

    # Validate potential email addresses
    valid_emails = set()
    for email in matches:
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            valid_emails.add(email)

    return list(valid_emails)

def get_links(html, base_url, follow_external):
    """
    Extract links from HTML content.

    :param str html: HTML content to search for links
    :param str base_url: Base URL of the page
    :param bool follow_external: Flag indicating whether to follow links to different domains
    :return set: Links found in HTML content
    """
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    base_domain = urlparse(base_url).netloc
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        link_domain = urlparse(full_url).netloc
        if follow_external or link_domain == base_domain:
            links.add(full_url)
    return links

def crawl(url, base_url, depth=2, follow_external=False, delay=1, phone=False, email=False, search_string=None):
    """
    Crawl a website and extract phone numbers and email addresses.
    
    :param str url: Starting URL for crawler
    :param str base_url: Base URL of website
    :param int depth: Depth of crawl
    :param bool follow_external: Flag indicating whether to follow links to different domains
    :param float delay: Delay between requests in seconds
    :param bool phone: Flag indicating whether to find phone numbers
    :param bool email: Flag indicating whether to find email addresses
    :param str search_string: String to search for in HTML content
    """
    if depth == 0 or url in visited_urls:
        return
    print(f"Crawling: {url}")
    visited_urls.add(url)

    html = fetch_html(url)
    if not html:
        return

    if phone:
        phone_numbers = find_phone_numbers(html)
        if phone_numbers:
            # Filter out phone numbers not 10, or 11 digits (US)
            phone_numbers = [number for number in phone_numbers if len(re.sub(r'\D', '', number)) in (10, 11)]
            if phone_numbers:
                print(f"Possible phone numbers found on {url}: {phone_numbers}")

    if email:
        email_addresses = find_email_addresses(html)
        if email_addresses:
            print(f"Possible email addresses found on {url}: {email_addresses}")

    if search_string:
        string_instances = find_strings(html, search_string)
        if string_instances:
            print(f"Specified strings found on {url}: {string_instances}")

    links = get_links(html, base_url, follow_external)
    for link in links:
        time.sleep(delay) # Wait for specified delay before next request
        crawl(link, base_url, depth - 1, follow_external, delay, phone, email)

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Crawl a website and extract phone numbers, email addresses, and specified strings.')
    parser.add_argument('starting_url', help='Starting URL for the crawler')
    parser.add_argument('search_string', nargs='?', default=None, help='The string to search for in the HTML content')
    parser.add_argument('--depth', type=int, default=2, help='Depth of crawl')
    parser.add_argument('--follow-external', action='store_true', help='Follow links to different domains?')
    parser.add_argument('--delay', type=float, default=1, help='Delay between requests in seconds')
    parser.add_argument('--phone', action='store_true', help='Find phone numbers?')
    parser.add_argument('--email', action='store_true', help='Find email addresses?')

    # Parse arguments
    args = parser.parse_args()

    # Start crawling with provided starting URL, depth, follow_external flag, delay, phone, email flags, and search_string
    crawl(args.starting_url, args.starting_url, args.depth, args.follow_external, args.delay, args.phone, args.email, args.search_string)
