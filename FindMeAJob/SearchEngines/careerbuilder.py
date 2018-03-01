from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class CareerBuilder:
    def __init__(self, debugMode, logging):
        self.debugMode = debugMode
        self.logging = logging
        self.logging.info("Creating CareerBuilder object...")
        self.engineName = "CareerBuilder"

    # The start of the job search process.
    # Sample URL
    # https://www.careerbuilder.com/jobs-entry-it-in-waltham,ma?page_number=1&posted=3&sort=relevance_desc
    def jobSearch(self, chrome, lists, resultsList, positionLevel, keyword, location):
        self.logging.info("Starting job search for {0} {1} in {2}...".format(positionLevel, keyword, location))
        jobPageList = []
        jobElementList = []

        # Using URL pattern for their search. Update some strings so they'll fit.
        searchPageURL = "https://www.careerbuilder.com/"

        try:
            self.logging.debug("Updating strings for URL based search...")
            positionText = positionLevel.replace(" ", "-")
            keywordText = keyword.replace(" ", "-")
            locationText = location.replace(" ", "-")
            searchPageURL = searchPageURL + ("jobs-{0}-{1}-in-{2}?".format(positionText, keywordText, locationText))
            self.logging.debug("Strings updated!")
        except Exception as error:
            self.logging.error("Couldn't update strings for page URL. Without them the process cannot continue.")
            self.logging.error(error)
            return

        try:
            self.logging.debug("Setting sort to relevance...")
            searchPageURL = searchPageURL + "page_number=1&posted=3&sort=relevance_desc"
            self.logging.debug("Sort set!")
        except Exception as error:
            self.logging.warning("Couldn't set sort to relevance.")
            self.logging.error(error)

        # Start going to the page with results on it.
        try:
            self.logging.debug("Going to results page...")
            chrome.get(searchPageURL)
            self.logging.debug("Page reached!")
        except Exception as error:
            self.logging.error("Couldn't get to results page. Without it the process cannot continue.")
            self.logging.error(error)
            return

        # After 3 pages then this stuff is probably all irrelevant anyway
        for pageIndex in range(1, 4):
            try:
                self.logging.debug("Attempting to reach page {0} of jobs...".format(pageIndex))
                searchPageURL = chrome.current_url
                searchPageURL = (searchPageURL[:searchPageURL.index("page_number=")] + "page_number={0}&posted=3".format(pageIndex))
                chrome.get(searchPageURL)
                self.logging.debug("Page reached!")
            except Exception as error:
                self.logging.warning("Could not navigate to page {0} of jobs.".format(pageIndex))
                self.logging.warning(error)
                break

            # Job listings are difficult to find iteratively through xpath or id so we need to tab through the page. Tab 32 times to get to the first listing. We subtract one because we will be tabbing in each iteration of the next loop.
            try:
                self.logging.debug("Attempting to tab to first job...")
                tabBig = ActionChains(chrome)
                tabBig.send_keys(Keys.TAB * 31)
                tabBig.perform()
                self.logging.debug("Tabs complete!")
            except Exception as error:
                self.logging.error("Couldn't tab to the first job listing.")
                self.logging.error(error)
                break

            # Now, go through each remaining element. Determine if it is a link to a job page. Add it to a list.
            try:
                self.logging.debug("Tabbing through page and adding pages to list...")
                jobElementList.clear()
                tabAction = ActionChains(chrome)
                tabAction.send_keys(Keys.TAB)
                for x in range(0, 250):
                    tabAction.perform()
                    element = chrome.switch_to.active_element
                    try:
                        # Check to see if we are at the end. If we hit the Blog then we are at the end
                        if element.text == "Blog":
                            self.logging.debug("End of results page!")
                            break
                        # Otherwise, add this element to the jobPageList for later parsing
                        elif element.get_attribute("href").startswith("https://www.careerbuilder.com/job/") and len(element.text) > 5:
                            jobElementList.append(element)
                            self.logging.debug("Added {0} to parse list!".format(element.text))
                    except:
                        self.logging.debug("Couldn't add listing to parse list.")
            except:
                self.logging.debug("Something went wrong tabbing through the page and adding pages to list.")

            # CareerBuilder does max 25 postings per page
            # Get a list of the hrefs that we wanna parse through.
            for jobElement in jobElementList:
                # Screen whatever is previewed on the search page. Not gonna visit full pages of things we know we don't want to check.
                try:
                    result = self.previewScreen(chrome, lists, jobElement)
                    if result.startswith("Bad"):
                        if result == "Bad Posting":
                            self.logging.info("No more results found.")
                            break
                        else:
                            self.logging.info("Search Page {0} and Job Page {1} is a {2}. Not adding it to the list.\n".format(pageIndex, jobElement.text, result))
                            continue
                    else:
                        jobPageList.append(result)
                except Exception as error:
                    self.logging.error("Error finding job posting page {0}.".format(jobElement.text))
                    self.logging.error(error)
                    break

        # Iterate through the hrefs and parse through the pages.
        for jobPage in jobPageList:
            # Go to the jobs page.
            try:
                self.logging.debug("Attempting to reach page {0} of jobs...".format(jobPage))
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
                result = str(self.pageParse(chrome, lists))
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
    def previewScreen(self, chrome, lists, jobElement):
        self.logging.debug("Starting job preview screen...")
        url = ""
        title = ""

        try:
            url = jobElement.get_attribute("href")
        except Exception as error:
            self.logging.warning("Issue screening for Job URL.")
            self.logging.debug(error)
            return "Bad URL"

        try:
            title = jobElement.text
        except Exception as error:
            self.logging.warning("Issue screening for Job Title.")
            self.logging.debug(error)

        try:
            # Parse through titles we don't like
            for x in lists.avoidTitlesWith:
                if x.lower() in title.lower():
                    self.logging.info("Bad title keyword, {0}, found in posting {1}. Disregarding this job posting.".format(x, title))
                    return "Bad Title"
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
                element = chrome.find_element_by_xpath("//div[@class='card with-padding']/div[@class='small-12 item'][1]/h1")
                title = element.text
                self.logging.info(" \tJob Title: {0}".format(title))
            except:
                furtherInvestigation = True
                self.logging.info("\tJob Title: {0}".format("Not found"))
            # Time Posted
            try:
                element = chrome.find_element_by_id("job-begin-date")
                timePostedAgo = element.text
                self.logging.info("\tTime Posted: {0}".format(timePostedAgo))
            except:
                self.logging.info("\tTime Posted: {0}".format("Not found"))
            # Job Location
            try:
                element = chrome.find_element_by_id("job-company-name")
                location = str(element.text)
                location = location[location.index(" • ") + len(" . "):]
                self.logging.info("\tLocation: {0}".format(location))
            except:
                furtherInvestigation = True
                self.logging.info("\tLocation: {0}".format("Not found"))
            # Job Description
            try:
                element = chrome.find_element_by_xpath("/html[@class='wf-lato-n7-active wf-lato-n4-active wf-lato-n3-active wf-active']/body/div[@id='main-content']/div[@class='main']/div[@class='row'][3]/div[@class='small-12 large-6 large-push-3 columns']/div[@class='card with-padding']/div[@class='row'][2]/div[@class='small-12 columns item']")
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
                    if line.startswith(tuple(["*", "-", "·", "+", "~", ">", "●", "•", "–"])):
                        qualificationsList.append(line[0:])
                        self.logging.debug("\t\t{0}".format(line))
                if len(qualificationsList) <= 2:
                    qualificationsList = qualifications
                    self.logging.debug(" \t\t{0}".format(qualificationsList))
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
