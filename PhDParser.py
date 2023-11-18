import lxml
import requests
import json
from bs4 import BeautifulSoup
import disciplines
import warnings
from datetime import datetime
from collections import defaultdict

class Parser():
    def __init__(self):
        self.disciplines = disciplines.disciplines

    def parseURL(self, url) -> BeautifulSoup:
        """ Returns 'soup' object from a html page using requests and BeautifulSoup. 
            url (str) : valid findaPhD url to parse
            RETURNS BeautifulSoup : BeautifulSoup object used to parse data
        """
        return BeautifulSoup(requests.get(url).text, 'lxml')

    def saveAsJson(self, contents:(list[dict]), file_path:str="json"):
        """ Saves list of dictionaries as .json file. 
            contents (list[dict]) : contents to save in .json file
            file_path (str) : path to save, including filename. can be relative. defaults to json + the lowest integer unused by an existing 'json' file
        """
        if file_path == "json": 
            i = 1
            while True:
                try: open(f"str{i}.json")
                except FileNotFoundError: break
                else: i+=1
            file_path = f"str{i}.json"
            
        with open(file_path, 'w') as json_file:
            json.dump(contents, json_file, indent=2)

class DisciplineParser(Parser):
    """ Parses the 'disciplines' page on findaphd.com to return all discipline url codes. """

    def __init__(self):
        super().__init__()  # initialise parent class
        self.url = "https://www.findaphd.com/phds/discipline/"
        self.soup = self.parseURL(self.url)
    
    def scrapeDisciplines(self) -> dict:
        """ Scrapes discipline page and returns dictionary of disciplines. """
        discipline_containers = self.soup.find_all(class_="card-title text-dark h4 d-block")

        for discipline_container in discipline_containers:
            if discipline_container is None: continue
            title = discipline_container.get_text(strip=True).lower()
            link_suffix = discipline_container.get('href')
            if title not in self.disciplines:
                self.disciplines[title] = link_suffix
        return self.disciplines

class PhDParser(Parser):
    """ Class to handle all (previous and current) searches for PhDs. Each instance handles a single new search. 
        all_projects (defaultdict[dict]) : dict of search terms, storing a dict of project names, each with a dict of saved projects for that search term. 
    """
    all_projects = defaultdict(dict)

    def __init__(self):
        """ Initialises class with new_projects """
        super().__init__()  # initialise parent class
        self.current_projects = {}
        self.search_term = None  # assigned to in genProjects
        self.recent_hashstring = ""

    def genProjects(self, discipline:str="psychology", recent_only:bool=True, keywords:str="") -> list[dict]:
        """ Parent function. Generates a list of projects from input parameters. Returns and saves internally. 
            discipline (str) : discipline of study to search within. default is "psychology"
            recent_only (bool) : show only recent PhD opportunities. default is True
            keywords (str) : *comma separated* list of search terms. defaults to no terms
            RETURNS list[dict] : list of projects with all project info
        """
        url = self.genURL(discipline=discipline, recent_only=recent_only, keywords=keywords)
        all_soup = self.parseURL(url)
        self.current_projects = self.parsePhdSoup(all_soup)
        if self.current_projects == []:
            warnings.warn('There are currently no PhDs listed using your search terms:/ Feel free to try again.')
        return self.current_projects

    def saveRecentAsJson(self, file_path:str="recent.json"):
        """ Saves recent new projects as a .json file with given output path. 
            file_path (str) : path to save projects to. default is "recent.json" in current directory.
        """
        if self.current_projects == []: raise Exception('No recent projects to save!')
        self.saveAsJson(self.current_projects, file_path=file_path)

    # ~~~~~ INTERNAL FUNCTIONS - do not need to be called by user. ~~~~~
    # ~~~~~
    def genURL(self, discipline:str="", recent_only:bool=True, keywords:str="") -> str:
        """ Generates a valid findaPhD url using search keywords. 
            discipline (str) : discipline of study to search within. default is "psychology"
            recent_only (bool) : show only recent PhD opportunities. default is True
            keywords (str) : *comma separated* list of search terms. defaults to no terms
            RETURNS str : valid findaPhD url
        """
        if discipline not in self.disciplines: raise KeyError("not a valid subject!")

        url_parts = [f"https://www.findaphd.com{self.disciplines[discipline]}"]
        if recent_only: url_parts.append("Show=M")

        keywords_str = [item.strip() for item in keywords.split(',')]
        self.recent_hashstring = discipline + (",").join(sorted(keywords_str))  # save hashstring of search term
        print(self.recent_hashstring)

        keywords_str = f"keywords={("+").join(keywords_str)}"
        url_parts.append(keywords_str)
        url = '&'.join(url_parts)
        return url

    def parsePhdSoup(self, soup:BeautifulSoup) -> dict[dict]:
        """ Returns list of new PhD projecst using BeautifulSoup data. 
            soup (BeautifulSoup) : BeautifulSoup data for a findaPhD search page
            RETURNS dict[dict] of project traits, stored under project names
        """
        new_projects = {}
        phd_containers = soup.find_all(class_="w-100 card shadow-sm p-4")

        # Extra data from each project title individually.
        for container in phd_containers:
            # Get information from title
            title_container = container.find(class_="h4 text-dark mx-0 mb-3")
            link = f"https://www.findaphd.com{title_container['href']}"  # generate link to page
            title = title_container.text  # generate title

            # Process hashstring
            if title in hashstrings: continue  # don't reprocess if already in set
            hashstrings.add(title)  # add to existing hashstrings

            # Time accessed
            access_time = datetime.now()

            # Get information about PhD country from the 'flag' section
            country = container.find(class_="phd-result__dept-inst--country-icon")
            if country is not None:  country = country.get("title")

            # Get university name
            university = container.find(class_="phd-result__dept-inst--title")
            if university is not None: university = university.get_text(strip=True)
            
            # Get date of last update
            date_updated = container.find(class_="apply py-2 small")
            if date_updated is not None: date_updated = date_updated.get_text(strip=True)[8:]

            # Get deadline date
            deadline = container.find(class_="fa-calendar")
            if deadline is not None: deadline = deadline.parent.get_text(strip=True)

            # Get funding information
            funding = container.find(class_="fa-wallet")
            if funding is not None: funding = funding.parent.get_text(strip=True)

            # Append to list and return
            new_projects.append({
                "title": title,
                "date_updated": date_updated,
                "deadline": deadline,
                "access_time": access_time,
                "funding": funding,
                "link": link,
                "country": country,
                "university": university
            })
        return new_projects






