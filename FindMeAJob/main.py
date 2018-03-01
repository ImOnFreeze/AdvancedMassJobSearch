import logging
import smtplib
import SearchEngines
import lists
import os
import sys

from selenium import webdriver
from selenium.webdriver.remote.remote_connection import LOGGER

# It is main.
def main():
    # Set Debug Mode
    debugMode = False

    # Setup logging
    setUpLogging(debugMode)

    # Clear lastrun.txt file. This file holds the results from the last run. It also records the current run and uses that information to email the user with a list of job listings.
    clearTextFile(debugMode, "lastrun.txt")

    # Setup Selenium Chrome Webdriver
    Chrome = setUpChrome(debugMode)

    # Setup variables
    emailUsername = "GmailUsername"
    emailPassword = "GmailPassword"

    searchDice = True
    searchCareerBuilder = True
    searchGlassDoor = True
    searchLinkedIn = False  # Incomplete
    searchMonster = True
    searchSimplyHired = True

    # Create  Lists object. This is the object that holds all user defined keywords and lists that they wish to include or exclude into the search.
    Lists = lists.Lists(debugMode, logging)

    # Setup search engine objects and add them to a list.
    if searchDice:
        Lists.searchEngines.append(SearchEngines.Dice(debugMode, logging))
    if searchCareerBuilder:
        Lists.searchEngines.append(SearchEngines.CareerBuilder(debugMode, logging))
    if searchGlassDoor:
        Lists.searchEngines.append(SearchEngines.GlassDoor(debugMode, logging))
    if searchLinkedIn:
        Lists.searchEngines.append(SearchEngines.LinkedIn(debugMode, logging))
    if searchSimplyHired:
        Lists.searchEngines.append(SearchEngines.SimplyHired(debugMode, logging))
    if searchMonster:
        Lists.searchEngines.append(SearchEngines.Monster(debugMode, logging))

    # If anything breaks from here on out we need to close the Chrome driver.
    try:
        # Get each search engine. Search through it. Record the results. Clear the results list in prep for another search engine.
        logging.info("Starting Job Search Process...")
        for searchEngine in Lists.searchEngines:
            for experienceLevel in Lists.searchExperienceLevels:
                for searchKeywords in Lists.searchKeywords:
                    for searchLocation in Lists.searchLocations:
                        Lists.results = searchEngine.jobSearch(Chrome, Lists, Lists.results, experienceLevel, searchKeywords, searchLocation)
            writeResultsToTextFile("lastrun.txt", Lists.results, searchEngine.engineName)
            Lists.results.clear()
        logging.info("Job Search Process complete!")
    except Exception as error:
        logging.error("Error with Job Search Process.")
        logging.error(error)
        Chrome.quit()

    Chrome.quit()
    constructAndSendEmailFromTextFile("lastrun.txt", emailUsername, emailPassword)
    logging.info("Done!")
    logging.info("=====================================================================================================")

# Sets up logging module.
def setUpLogging(debugMode=False):
    if not debugMode:
        logging.basicConfig(handlers=[logging.FileHandler("logs.txt", 'w', 'utf-8')], format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]: %(message)s', level=logging.INFO)
    else:
        logging.basicConfig(handlers=[logging.FileHandler("logs.txt", 'w', 'utf-8')], format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]: %(message)s', level=logging.DEBUG)
    logging.info("=====================================================================================================")
    logging.info("Logging was set up!")


# Sets up Chrome Webdriver for Selenium
def setUpChrome(debugMode=False):
    logging.info("Setting up Selenium Chrome Webdriver...")
    try:
        chromeOptions = webdriver.ChromeOptions()
        if not debugMode:
            chromeOptions.add_argument('headless')
        else:
            chromeOptions.add_argument("--start-maximized")
            LOGGER.setLevel(logging.INFO)
        logging.info("Headless Chrome Web Driver was set up!")
        return webdriver.Chrome(chrome_options=chromeOptions)
    except Exception as error:
        logging.critical("Failed Starting Headless Chrome Web Driver.")
        logging.critical(error)
        sys.exit("Exiting Process due to critical error.")


# Clears a text file. Format should be <example.txt>.
def clearTextFile(debugMode, nameOfFile):
    try:
        logging.info("Clearing {0}...".format(nameOfFile))
        text_file = open("{0}".format(nameOfFile), "w", encoding="UTF-8")
        text_file.write("")
        text_file.close()
        logging.info("Cleared {0}!".format(nameOfFile))
    except Exception as error:
        logging.error("Could not clear the file: {0}.".format(nameOfFile))
        logging.error(error)

# Sorts list, removes duplicates, writes remaining results to file. Format should be <example.txt>.
def writeResultsToTextFile(nameOfFile, resultsList, searchSiteName):
    logging.info("Writing results to {0}".format(nameOfFile))
    try:
        logging.debug("Sorting Results List...")
        resultsList = set(resultsList)
        resultsList = list(resultsList)
        resultsList.sort()
        logging.debug("Results List sorted!")
    except Exception as error:
        logging.error("Couldn't sort list.")
        logging.error(error)

    try:
        logging.debug("Attempting to remove duplicate listings...")
        index = 9
        while index < (len(resultsList) - 1):
            if resultsList[index][:100] in resultsList[index + 1]:
                del resultsList[index + 1]
                index = index - 1
            else:
                index = index + 1
        logging.debug("Duplicate listings removed!")
    except Exception as error:
        logging.error("Error attempting to remove duplicate listings.")
        logging.error(error)

    try:
        logging.debug("Saving results from {0} to file...".format(searchSiteName))
        text_file = open("{0}".format(nameOfFile), "a", encoding="UTF-8")
        text_file.write("{0}:\n".format(searchSiteName))
        for line in resultsList:
            text_file.write(line + "\n")
        text_file.write("\n")
        text_file.close()
        logging.debug("Results saved!")
    except Exception as error:
        logging.error("Could not save results from {0}.".format(searchSiteName))
        logging.error(error)
        for result in resultsList:
            logging.error(result)


# Constructs and sends an email from the contents of a text file. Format should be <example.txt>.
# Emails should be gmail
def constructAndSendEmailFromTextFile(nameOfFile, username, password):
    logging.info("Constructing and saving email...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(username, password)
        sent_from = username
        to = [username]
        subject = 'Find Me A Job: I found these jobs for you!'
        body = ""
        text_file = open("{0}".format(nameOfFile), "r", encoding='UTF-8')
        import re
        for line in text_file.read():
            try:
                body = body + line
            except Exception as error:
                logging.error("There was an error writing the following line to body: {0}".format(line))
                logging.error(error)
        text_file.close()
        email_text = "Subject: {0}\n\n{1}".format(subject, body)
        email_text = email_text
        server.sendmail(sent_from, to, email_text.encode('utf-8'))
        server.close()
        logging.info("Email Sent!")

    except Exception as error:
        logging.error("There was an error sending the email.")
        logging.error(error)


# The start of it all.
if __name__ == "__main__":
    main()
