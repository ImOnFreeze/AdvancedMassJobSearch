import re
from selenium.webdriver.common.keys import Keys

class GlassDoor:
    def __init__(self, debugMode, logging):
        self.debugMode = debugMode
        self.logging = logging
        self.logging.info("Creating GlassDoor object...")
        self.engineName = "GlassDoor"

    # The start of the job search process.
    # sample URL
    # https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword=Entry+Level+Software&sc.keyword=Entry+Level+Software&locT=C&locId=1154703&jobType=
    def jobSearch(self, chrome, lists, resultsList, positionLevel, keyword, location):
        self.logging.info("Starting job search for {0} {1} in {2}...".format(positionLevel, keyword, location))
        jobPageList = []

        # Using URL pattern for their search. Update some strings so they'll fit.
        searchPageURL = "https://www.glassdoor.com/"

        try:
            self.logging.debug("Filling in search bar...")
            # Glassdoor's URL pattern is weird so we gonna do some of this the old fashioned way. This is because location is determined by some abstract number.
            positionText = positionLevel
            keywordText = keyword
            locationText = location
            searchPageURL = "https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword=&sc.keyword=&locT=&locId=&jobType="
            chrome.get(searchPageURL)
            element = chrome.find_element_by_id("KeywordSearch")
            element.clear()
            element.send_keys("{0} {1}".format(positionText, keywordText))
            element = chrome.find_element_by_id("LocationSearch")
            element.clear()
            element.send_keys("{0}".format(locationText))
            chrome.find_element_by_id("HeroSearchButton").click()
            self.logging.debug("Filled in search bar!")
        except Exception as error:
            self.logging.error("Couldn't update search bar. Without them the process cannot continue.")
            self.logging.error(error)
            return

        try:
            self.logging.debug("Setting sort to relevance...")
            element = chrome.find_element_by_xpath("//*[@id=\"DKFilters\"]/div/div/div[2]")
            element.click()
            element = chrome.find_element_by_xpath("//*[@id=\"DKFilters\"]/div/div/div[2]/ul/li[2]")
            element.click()
            self.logging.debug("Sort set!")
        except Exception as error:
            self.logging.error("Couldn't set sort to relevance.")
            self.logging.error(error)

        self.logging.info("[GLASSDOOR] Starting Job Parse...")

        # After 3 pages then this stuff is probably all irrelevant anyway
        for pageIndex in range(1, 4):
            try:
                self.logging.debug("Attempting to reach page {0} of jobs...".format(pageIndex))
                if pageIndex != 1:
                    # We don't need to go to the next page on the first iteration.
                    element = chrome.find_element_by_xpath("//*[@id=\"FooterPageNav\"]/div/ul/li[7]/a/i")
                    element.click()
                self.logging.debug("Page reached!")
            except Exception as error:
                self.logging.warning("Could not navigate to page {0} of jobs.".format(pageIndex))
                self.logging.warning(error)
                break

            # GlassDoor does max 29 postings per page
            # Get a list of the hrefs that we wanna parse through.
            for jobIndex in range(0, 29):
                # Screen whatever is previewed on the search page. Not gonna visit full pages of things we know we don't want to check.
                try:
                    result = self.previewScreen(chrome, lists, jobIndex)
                    if result.startswith("Bad"):
                        if result == "Bad Posting":
                            self.logging.info("No more results found.")
                            break
                        else:
                            self.logging.info("Search Page {0} and Job Page {1} is a {2}. Not adding it to the list.\n".format(pageIndex, jobIndex, result))
                            continue
                    else:
                        jobPageList.append(result)
                except Exception as error:
                    self.logging.error("Error finding job posting page {0}.".format(jobIndex))
                    self.logging.error(error)
                    break

        for jobPage in jobPageList:
            # Go to the jobs page.
            try:
                self.logging.debug(("Selecting the job page {0}...".format(jobPage)))
                chrome.get(jobPage)
                self.logging.debug("Page reached!")
            except Exception as error:
                self.logging.error("Error getting to job posting page {0}. Skipping page.".format(jobPage))
                self.logging.error(error)
                continue

            try:
                # Parse page to get what we want and determine if this is a good candidate.
                self.logging.debug("Starting job page parse...")
                self.logging.info("====================")
                result = self.pageParse(chrome, lists)
                if result.startswith("Bad"):
                    self.logging.info("Bad Posting. Not adding it to the list!")
                elif result.startswith("Low"):
                    self.logging.info("Mediocre Posting. Adding it to the list!")
                    resultsList.append(result)
                else:
                    self.logging.info("Good Enough Posting. Adding it to the list!")
                    resultsList.append(result)
                self.logging.debug("Job page parse complete!")
                self.logging.info("====================\n")
            except Exception as error:
                self.logging.error("Error parsing job posting page {0}. Skipping page.".format(jobPage))
                self.logging.error(error)
                continue

        self.logging.info("Job search for {0} {1} in {2} complete!".format(positionLevel, keyword, location))
        return resultsList

    # Screen the preview to see if we even wanna parse this stuff.
    def previewScreen(self, chrome, lists, jobIndex):
        self.logging.debug("Starting job preview screen...")
        url = ""
        title = ""
        timePostedAgo = ""
        location = ""

        # If we can't find the URL to the job page then we can't parse it anyway.
        try:
            url = chrome.find_element_by_xpath("//*[@id=\"MainCol\"]/div[1]/ul/li[{0}]/div[2]/div[1]/div[1]/a".format(jobIndex)).get_attribute("href")
        except Exception as error:
            self.logging.warning("Issue screening for Job URL.")
            self.logging.debug(error)
            return "Bad URL"

        try:
            title = chrome.find_element_by_xpath("//*[@id=\"MainCol\"]/div[1]/ul/li[{0}]/div[2]/div[1]/div[1]/a".format(jobIndex)).text
        except Exception as error:
            self.logging.warning("Issue screening for Job Title.")
            self.logging.debug(error)

        try:
            location = chrome.find_element_by_xpath("//*[@id=\"MainCol\"]/div[1]/ul/li[{0}]/div[2]/div[2]/div".format(jobIndex)).text
        except Exception as error:
            self.logging.warning("Issue screening for Job Location.")
            self.logging.debug(error)

        try:
            timePostedAgo = chrome.find_element_by_xpath("//*[@id=\"MainCol\"]/div[1]/ul/li[{0}]/div[2]/div[3]/div[2]".format(jobIndex)).text
        except Exception as error:
            self.logging.warning("Issue screening for Time Posted.")
            self.logging.debug(error)

        try:
            # Parse through titles we don't like
            for x in lists.avoidTitlesWith:
                if x in title:
                    self.logging.info("Bad title keyword, {0}, found in posting index {1}. Disregarding this job posting...".format(x, jobIndex))
                    return "Bad Title"
            # Parse through locations we don't like
            for x in lists.avoidLocationsWith:
                if x in location:
                    self.logging.info("Bad location keyword, {0}, found in posting index {1}. Disregarding this job posting...".format(x, jobIndex))
                    return "Bad Location"
            # Parse through dates posted we don't like
            for x in lists.avoidTimeframesWith:
                if x in timePostedAgo:
                    self.logging.info("Time posted {0} was too old, found in posting index {1}. Disregarding this job posting...".format(x, jobIndex))
                    return "Bad Time"
        except Exception as error:
            self.logging.error("Issue screening job posting.")
            self.logging.error(error)
        self.logging.debug("Job preview screen complete!")
        return url

    def pageParse(self, chrome, lists):
        # Set up variables that will be used later on.
        furtherInvestigation = False

        pageURL = chrome.current_url
        timePostedAgo = ""
        title = ""
        location = ""
        description = ""
        qualifications = ""
        qualificationsList = []
        self.logging.info("Parsing {0}".format(pageURL))

        # Check if a new tab was opened. If it was then honestly lets not deal with it. Throw it into a low priority list.
        try:
            if len(chrome.window_handles) > 1:
                self.logging.info("Additional tab detected. Closing it and adding page to low priority manual searching..")
                chrome.switch_to_window(chrome.window_handles[1])
                pageURL = chrome.current_url
                chrome.close()
                chrome.switch_to_window(chrome.window_handles[0])
                return "Low Priority: {0}, {1}: {2}".format(title, location, pageURL)
        except Exception as error:
            self.logging.error("Some error occurred closing tab.")
            if error is not None:
                self.logging.error(error)
                return "Low Priority: {0}, {1}: {2}".format(title, location, pageURL)

        try:
            # Job title
            try:
                title = chrome.find_element_by_xpath("//*[@id=\"HeroHeaderModule\"]/div[3]/div[1]/div[2]/h2").text
                self.logging.info("\tJob Title: {0}".format(title))
            except:
                furtherInvestigation = True
                self.logging.info("\tJob Title: {0}".format("Not found"))
            # Time Posted
            try:
                timePostedAgo = chrome.find_element_by_xpath("//*[@id=\"HeroHeaderModule\"]/div[3]/div[2]/div[2]/span").text
                self.logging.info("\tTime Posted: {0}".format(timePostedAgo))
            except:
                self.logging.info("\tTime Posted: {0}".format("Not found"))
            # Job Location
            try:
                location = chrome.find_element_by_xpath("//*[@id=\"HeroHeaderModule\"]/div[3]/div[1]/div[2]/span[3]").text
                location = re.sub("^\d+\s|\s\d+\s|\s\d+$", " ", location)
                location = location[2:]
                self.logging.info("\tLocation: {0}".format(location))
            except:
                furtherInvestigation = True
                self.logging.info("\tLocation: {0}".format("Not found"))
            # Job Description
            try:
                element = chrome.find_element_by_xpath("//*[@id=\"JobDescriptionContainer\"]")
                description = element.text
                self.logging.info("\tJob Description: {0}".format(description[:127] + "..."))
            except:
                furtherInvestigation = True
                self.logging.info("\tJob Description: {0}".format("Not found"))

            # Qualifications
            # Find where the qualifications section is
            for word in lists.possibleQualificationsKeywords:
                if word.lower() in description.lower():
                    qualifications = description[(description.lower()).index(word.lower()):]
            if len(qualifications) >= 5:
                self.logging.debug("\tJob Qualifications:")
                for line in qualifications.splitlines():
                    # Take it all because GlassDoor is special
                    qualificationsList.append(line)
                    self.logging.debug("\t\t{0}".format(line))
                if len(qualificationsList) <= 2:
                    qualificationsList = qualifications
                    self.logging.debug("\t\t{0}".format(qualificationsList))
            else:
                furtherInvestigation = True
                self.logging.debug("\tJob Qualifications: {0}".format("Not found"))

            # Parse through titles we don't like
            for x in lists.avoidTitlesWith:
                if x.lower() in title.lower():
                    self.logging.info("Bad title keyword, {0}, found in {1}. Disregarding this job posting.".format(x, title))
                    return "Bad Title"
            # Parse through locations we don't like
            for x in lists.avoidLocationsWith:
                if x in location:
                    self.logging.info("Bad location keyword, {0}, found in {1}. Disregarding this job posting.".format(x, location))
                    return "Bad Location"
            # Parse through dates posted we don't like
            for x in lists.avoidTimeframesWith:
                if x.lower() in timePostedAgo.lower():
                    self.logging.info("Time posted was too old. Disregarding this job posting.")
                    return "Bad Time"
            # Parse through qualifications we don't like
            for x in lists.avoidQualificationsWith:
                for y in qualificationsList:
                    if x in y:
                        self.logging.info("Bad qualification keyword, {0}, found in {1}. Disregarding this job posting.".format(x, "the job description"))
                        return "Bad Qualifications"
        except Exception as error:
            self.logging.error(error)

        if furtherInvestigation:
            self.logging.info("This page needs further investigation. Adding URL to the list for further investigation.")
            return "Further Investigation: {0}, {1}: {2}".format(title, location, pageURL)

        self.logging.info("This page looks like a potential candidate. Adding URL to the list for further investigation.")
        return "Potential Candidate: {0}, {1}: {2}".format(title, location, pageURL)
