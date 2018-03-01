import string
import os
import sys
import re
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

### Incomplete work in progress. Has not been refactored like the other classes have.

class LinkedIn:
    def __init__(self, debugMode, logging):
        self.debugMode = debugMode
        self.logging = logging
        self.logging.info("[LINKEDIN] Creating LinkedIn object...")
        self.engineName = "LinkedIn"

    def jobSearch(self, chrome, lists, resultsList, positionLevel, keyword, location):
        # sample URL
        # https://www.linkedin.com/jobs/search?keywords=Entry%20Level%20Software&location=Waltham%2C%20Massachusetts
        self.logging.info("[LINKEDIN] Starting job search for {0}...".format(keyword))
        searchPageURL = "https://www.linkedIn.com/"

        nextButton = ""
        jobPageList = []

        try:
            self.logging.info("[LINKEDIN] Logging into LinkedIn")
            username = "linkedinUsername"
            password = "linkedinPassword"
            chrome.get(searchPageURL)
            element = chrome.find_element_by_id("login-email")
            element.send_keys(username)
            element = chrome.find_element_by_id("login-password")
            element.send_keys(password)
            element = chrome.find_element_by_id("login-submit")
            element.click()
        except Exception as error:
            self.logging.warning("[LINKEDIN] Could not login. Probably because it is already logged in.")
            if error is not None:
                self.logging.warning(error)

        try:
            # Much fast to through the search into LinkedIn's URL pattern
            positionText = positionLevel.replace(" ", "%20")
            keywordText = keyword.replace(" ", "%20")
            locationText = location.replace(" ", "%20")
            locationText = locationText.replace(",", "%2C")
            searchPageURL = searchPageURL + ("jobs/search/?keywords={0}+{1}&location={2}".format(positionText, keywordText, locationText))
        except Exception as error:
            self.logging.error("[LINKEDIN] Couldn't update strings for page URL.")
            if error is not None:
                self.logging.error(error)
            return

        try:
            self.logging.info("[LINKEDIN] Searching for {0} {1} Jobs...".format(positionLevel, keyword))
            chrome.get(searchPageURL)
        except:
            self.logging.error("[LINKEDIN] Couldn't get to results page.")
            return

        # We need to do this through tabbing throughout the page.
        try:
            self.logging.info("[LINKEDIN] Setting sort to relevance...")
            tabBig = ActionChains(chrome)
            tabBig.send_keys(Keys.TAB * 29)
            tabBig.perform()
            element = chrome.switch_to.active_element
            element.send_keys(Keys.ENTER)
            time.sleep(1)
            element = chrome.find_element_by_xpath("//*[@id=\"date-posted-facet-values\"]/li[2]/label/p/span[1]")
            element.click()
            tabBig = ActionChains(chrome)
            tabBig.send_keys(Keys.TAB * 6)
            tabBig.perform()
        except Exception as error:
            self.logging.warning("[LINKEDIN] Couldn't set sort to relevance.")
            if error is not None:
                self.logging.error(error)
            # Skip trying to sort for relevance and just go to the first job. That should be 36 Tabs. We are gonna subtract one though so the upcoming while loop works, though
            chrome.get(searchPageURL)
            tabBig = ActionChains(chrome)
            tabBig.send_keys(Keys.TAB * 35)
            tabBig.perform()

        self.logging.info("[LINKEDIN] Starting Job Parse...")

        pageIndex = 1
        # After 3 pages then this stuff is probably all irrelevant anyway
        while pageIndex <= 3:
            try:
                self.logging.info("[LINKEDIN] Navigating to page {0} of jobs.".format(pageIndex))
                if pageIndex != 1:
                    nextButton.click()
            except Exception as error:
                self.logging.info("[LINKEDIN] End of job pages.")
                if error is not None:
                    self.logging.warning("[LINKEDIN] Could not navigate to page {0} of jobs.".format(pageIndex))
                    self.logging.error(error)
                break

            # Job Listings in LinkedIn are labeled as Ember#### where #### is some posting number. It makes it difficult to find elements by an index. Therefore we will tab throughout the entire page and add the job links into a list and parse
            # that later.
            try:
                self.logging.info("[LINKEDIN] Getting the list of jobs...")
                # kill myself
                tabAction = ActionChains(chrome)
                tabAction.send_keys(Keys.TAB)
                for x in range(0, 250):
                    tabAction.perform()
                    element = chrome.switch_to.active_element
                    try:
                        # Check to see if we are at the end. If we hit the next button (or fail to find it after 250 tabs) then we are at the end
                        if element.text == "Next\nNext":
                            try:
                                nextButton = chrome.find_element_by_xpath("//*[starts-with(@id, \"ember\")]/li[3]/button")
                            except:
                                nextButton = chrome.find_element_by_xpath("//*[starts-with(@id, \"ember\")]/li[2]/button")
                            print("Next Button Set")
                            break
                        # Otherwise, add this element to the jobPageList for later parsing
                        elif element.get_attribute("href").startswith("https://www.linkedin.com/jobs/view/") and len(element.text) > 5:
                            jobPageList.append(element.get_attribute("href"))
                    except:
                        ""
            except Exception as error:
                self.logging.error("[LINKEDIN] Could not get list of jobs")
                if error is not None:
                    self.logging.error(error)

            jobIndex = 0
            # LinkedIn does max 25 postings per page
            while jobIndex < 1:
                # Screen job preview
                # Placeholder for when I make a method to screen some info on the job preview
                # result = self.linkedInPreviewScreen(chrome, lists, jobIndex, jobPageList)
                result = "Good"
                if result.startswith("Bad"):
                    self.logging.info("[LINKEDIN] Bad Posting. Not adding it to the list.\n")
                    jobIndex = jobIndex + 1
                    continue

                else:
                    try:
                        self.logging.info(("[LINKEDIN] Selecting the job page at index {0} for {1} {2}...".format(jobIndex, positionLevel, keyword)))
                        chrome.get(jobPageList[jobIndex])
                    except Exception as error:
                        self.logging.info("[LINKEDIN] End of job results.")
                        if error is not None:
                            self.logging.warning("[LINKEDIN] Error finding job posting page.")
                            self.logging.error(error)
                        break

                    # Parse page to get what I want
                    result = self.linkedInPageParse(chrome, lists)
                    if result.startswith("Bad"):
                        self.logging.info("[LINKEDIN] Bad Posting. Not adding it to the list.\n")
                        chrome.back()
                    elif result.startswith("Low"):
                        self.logging.info("[LINKEDIN] Mediocre Posting. Adding it to the list.\n")
                        resultsList.append(result)
                    else:
                        self.logging.info("[LINKEDIN] Good Enough Posting. Adding it to the list.\n")
                        resultsList.append(result)
                        chrome.back()
                jobIndex = jobIndex + 1
            pageIndex = pageIndex + 1
        return resultsList

    # This is broken right now. Heh.
    # Screen the preview to see if we even wanna parse this stuff.
    def linkedInPreviewScreen(self, chrome, lists, jobIndex, jobPageList):
        title = ""
        try:
            title = jobPageList[jobIndex].text
        except:
            self.logging.warning("[LINKEDIN] Issue screening for Job Title.")

        try:
            # Parse through titles we don't like
            for x in lists.getAvoidTitlesWith():
                if x in title:
                    self.logging.info("[LINKEDIN] Bad title keyword, {0}, found in posting index {1}. Disregarding this job posting...".format(x, jobIndex))
                    return "Bad Title"
        except Exception as error:
            self.logging.error("[LINKEDIN] Issue screening job posting.")
            if error is not None:
                self.logging.error(error)
            return "Good enough posting"
        return "Good enough posting"

    def linkedInPageParse(self, chrome, lists):
        furtherInvestigation = False

        pageURL = chrome.current_url
        timePostedAgo = ""
        title = ""
        location = ""
        description = ""
        qualifications = ""
        qualificationsList = []
        self.logging.info("[LINKEDIN] Parsing {0}".format(pageURL))
        self.logging.info("[LINKEDIN] ====================")

        # Check if a new tab was opened. If it was then honestly lets not deal with it. Throw it into a low priority list.
        try:
            if len(chrome.window_handles) > 1:
                self.logging.info("[LINKEDIN] Additional tab detected. Closing it and adding page to low priority manual searching..")
                chrome.switch_to_window(chrome.window_handles[1])
                pageURL = chrome.current_url
                chrome.close()
                chrome.switch_to_window(chrome.window_handles[0])
                return "Low Priority: {0}, {1}: {2}".format(title, location, pageURL)
        except Exception as error:
            self.logging.error("[LINKEDIN] Some error occurred closing tab.")
            if error is not None:
                self.logging.error(error)
                return "Low Priority: {0}, {1}: {2}".format(title, location, pageURL)

        try:
            # Job title
            try:
                element = chrome.find_element_by_xpath("//*[starts-with(@id, \"ember\")]/div[3]/h1")
                title = element.text
                self.logging.info("[LINKEDIN] \tJob Title: {0}".format(title))
            except:
                furtherInvestigation = True
                self.logging.info("[LINKEDIN] \tJob Title: {0}".format("Not found"))
            # Time Posted
            try:
                element = chrome.find_element_by_xpath("//*[starts-with(@id, \"ember\")]/div[3]/p/span[1]")
                try:
                    timePostedAgo = element[element.text.index("\n"):]
                except:
                    timePostedAgo = element.text
                self.logging.info("[LINKEDIN] \tTime Posted: {0}".format(timePostedAgo))
            except:
                self.logging.info("[LINKEDIN] \tTime Posted: {0}".format("Not found"))
            # Job Location
            try:
                element = chrome.find_element_by_xpath("//*[starts-with(@id, \"ember\")]/div[3]/h3/span[2]")
                try:
                    location = element[element.text.index("\n"):]
                except:
                    location = element.text
                location = re.sub("^\d+\s|\s\d+\s|\s\d+$", " ", location)
                self.logging.info("[LINKEDIN] \tLocation: {0}".format(location))
            except:
                furtherInvestigation = True
                self.logging.info("[LINKEDIN] \tLocation: {0}".format("Not found"))
            # Job Description
            try:
                element = chrome.find_element_by_id("job-details")
                description = element.text
                self.logging.info("[LINKEDIN] \tJob Description: {0}".format(description[:127] + "..."))
            except:
                furtherInvestigation = True
                self.logging.info("[LINKEDIN] \tJob Description: {0}".format("Not found"))

            # Qualifications
            # Find where the qualifications section is
            for word in lists.getPossibleQualificationsKeywords():
                if word.lower() in description.lower():
                    qualifications = description[(description.lower()).index(word.lower()):]
            if len(qualifications) >= 5:
                self.logging.info("[LINKEDIN] \tJob Qualifications:")
                for line in qualifications.splitlines():
                    if line.startswith(tuple(["*", "-", "·", "+", "~", ">", "●", "•"])):
                        qualificationsList.append(line[0:])
                        self.logging.debug("\t\t{0}".format(line))
                if len(qualificationsList) <= 2:
                    qualificationsList = qualifications
                    self.logging.info("[LINKEDIN] \t\t{0}".format(qualificationsList))
            else:
                furtherInvestigation = True
                self.logging.info("[LINKEDIN] \tJob Qualifications: {0}".format("Not found"))

            # Parse through titles we don't like
            for x in lists.getAvoidTitlesWith():
                if x in title:
                    self.logging.info("[LINKEDIN] Bad title keyword, {0}, found in {1}. Disregarding this job posting...".format(x, title))
                    self.logging.info("[LINKEDIN] ====================\n")
                    return "Bad Title"
            # Parse through locations we don't like
            for x in lists.getAvoidLocationsWith():
                if x in location:
                    self.logging.info("[LINKEDIN] Bad location keyword, {0}, found in {1}. Disregarding this job posting...".format(x, location))
                    self.logging.info("[LINKEDIN] ====================\n")
                    return "Bad Location"
            # Parse through dates posted we don't like
            for x in lists.getAvoidTimeframesWith():
                if x in timePostedAgo:
                    self.logging.info("[LINKEDIN] Time posted was too old. Disregarding this job posting...")
                    self.logging.info("[LINKEDIN] ====================\n")
                    return "Bad Time"
            # Parse through qualifications we don't like
            for x in lists.getAvoidQualificationsWith():
                for y in qualificationsList:
                    if x in y:
                        self.logging.info("[LINKEDIN] Bad qualification keyword, {0}, found in {1}. Disregarding this job posting...".format(x, "the job description"))
                        self.logging.info("[LINKEDIN] ====================\n")
                        return "Bad Qualifications"
        except Exception as error:
            self.logging.error(error)
            self.logging.info("[LINKEDIN] ====================\n")

        if furtherInvestigation:
            self.logging.info("[LINKEDIN] This page needs further investigation. Adding URL to the list for further investigation...")
            self.logging.info("[LINKEDIN] ====================\n")
            return "Further Investigation: {0}, {1}: {2}".format(title, location, pageURL)

        self.logging.info("[LINKEDIN] This page looks like a potential candidate. Adding URL to the list for further investigation...")
        self.logging.info("[LINKEDIN] ====================\n")
        return "Potential Candidate: {0}, {1}: {2}".format(title, location, pageURL)
