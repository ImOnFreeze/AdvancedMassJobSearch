class Dice:
    def __init__(self, debugMode, logging):
        self.debugMode = debugMode
        self.logging = logging
        self.logging.info("Creating Dice object...")
        self.engineName = "Dice"

    # The start of the job search process.
    # sample URL
    # https://www.dice.com/jobs/advancedResult.html?for_one=IT+Tech&for_all=Entry+Level&for_exact=&for_none=&for_jt=&for_com=&for_loc=Waltham%2C+MA&sort=relevance&radius=30&postedDate=3
    def jobSearch(self, chrome, lists, resultsList, positionLevel, keyword, location):
        self.logging.info("Starting job search for {0} {1} in {2}...".format(positionLevel, keyword, location))
        jobPageList = []

        # Using URL pattern for their search. Update some strings so they'll fit.
        searchPageURL = "https://www.dice.com/jobs/advancedResult.html"

        try:
            self.logging.debug("Updating strings for URL based search...")
            positionText = positionLevel.replace(" ", "+")
            keywordText = keyword.replace(" ", "+")
            locationText = location.replace(" ", "+")
            locationText = locationText.replace(",", "%2C")
            searchPageURL = searchPageURL + ("?for_one={0}&for_all={1}&for_exact=&for_none=&for_jt=&for_com=&for_loc={2}".format(keywordText, positionText, locationText))
            self.logging.debug("Strings updated!")
        except Exception as error:
            self.logging.error("Couldn't update strings for page URL. Without them the process cannot continue.")
            self.logging.error(error)
            return

        try:
            self.logging.debug("Setting sort to relevance and posted date to last three days...")
            searchPageURL = searchPageURL + "&sort=relevance&radius=30&postedDate=3"
            self.logging.debug("Sort set!")
        except Exception as error:
            self.logging.warning("Couldn't set sort to relevance.")
            self.logging.error(error)


        # Start going to the page with results on it. This is so we can get the correct URL for iterating through pages.
        try:
            self.logging.debug("Going to results page...")
            chrome.get(searchPageURL)
            self.logging.debug("Page reached!")
        except Exception as error:
            self.logging.error("Couldn't get to results page. Without it the process cannot continue.")
            self.logging.error(error)
            return

        try:
            self.logging.debug("Find the next page button...")
            element = chrome.find_element_by_xpath("//span[@class='icon-filled-arrow-66']")
            element.click()
            searchPageURL = chrome.current_url
            multiplePages = True
            self.logging.debug("Next page button found!")
        except Exception as error:
            multiplePages = False
            self.logging.debug("Next page button not found. This is probably because there are not enough results to warrant a second page.")
            self.logging.debug(error)

        # After 3 pages then this stuff is probably all irrelevant anyway
        for pageIndex in range(1, 4):
            try:
                # Go to the current page index's page using the URL pattern. If there was no next page button (or if we couldn't find it) then ignore this block.
                if multiplePages:
                    self.logging.debug("Attempting to reach page {0} of jobs...".format(pageIndex))
                    searchPageURL = (searchPageURL[:searchPageURL.index("startPage")] + "startPage-{0}-jobs".format(pageIndex))
                    chrome.get(searchPageURL)
                    self.logging.debug("Page reached!")
                elif not multiplePages and pageIndex > 1:
                    self.logging.debug("Attempting to reach the only page of jobs...")
                    break
            except Exception as error:
                self.logging.warning("Could not navigate to page {0} of jobs.".format(pageIndex))
                self.logging.warning(error)
                break

            # Dice does max 30 postings per page
            # Get a list of the hrefs that we wanna parse through.
            for jobIndex in range(0, 30):
                # Screen whatever is previewed on the search page. Not gonna visit full pages of things we know we don't want to check.
                try:
                    result = self.previewScreen(chrome, lists, jobIndex)
                    if result.startswith("Bad"):
                        if not multiplePages and result == "Bad Posting":
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

        # Iterate through the hrefs and parse through the pages.
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

        # If this element can't be found then we're not gonna be able to get to the page anyway.
        try:
            element = chrome.find_element_by_xpath("//*[@id=\"position{0}\"]".format(jobIndex))
        except:
            self.logging.debug("No element was found at jobIndex {0}".format(jobIndex))
            return "Bad Posting"

        try:
            url = element.get_attribute("href")
        except Exception as error:
            self.logging.warning("Issue screening for Job URL.")
            self.logging.debug(error)
            return "Bad URL"

        try:
            title = element.text
        except Exception as error:
            self.logging.warning("Issue screening for Job Title.")
            self.logging.debug(error)

        try:
            # Parse through titles we don't like
            for x in lists.avoidTitlesWith:
                if x.lower() in title.lower():
                    self.logging.info("Bad title keyword, {0}, found in posting index {1}. Disregarding this job posting.".format(x, jobIndex))
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
            self.logging.error(error)
            return "Low Priority: {0}, {1}: {2}".format(title, location, pageURL)

        try:
            # Job title
            try:
                element = chrome.find_element_by_id("jt")
                title = element.text
                self.logging.info("\tJob Title: {0}".format(title))
            except:
                furtherInvestigation = True
                self.logging.info("\tJob Title: {0}".format("Not found"))
            # Time Posted
            try:
                element = chrome.find_element_by_xpath("//ul[@class='list-inline details']/li[@class='posted hidden-xs']")
                timePostedAgo = element.text
                self.logging.info("\tTime Posted: {0}".format(timePostedAgo))
            except:
                self.logging.info("\tTime Posted: {0}".format("Not found"))
            # Job Location
            try:
                element = chrome.find_element_by_xpath("//ul[@class='list-inline details']/li[@class='location']/span[1]")
                location = str(element.text)
                self.logging.info("\tLocation: {0}".format(location))
            except:
                furtherInvestigation = True
                self.logging.info("\tLocation: {0}".format("Not found"))
            # Job Description
            try:
                element = chrome.find_element_by_id("jobdescSec")
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
                    if line.startswith(tuple(["*", "-", "·", "+", "~", ">", "●", "•"])):
                        qualificationsList.append(line[0:])
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
