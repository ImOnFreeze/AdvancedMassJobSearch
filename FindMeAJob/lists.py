import sys

# Class that holds all important lists.
class Lists:
    def __init__(self, debugMode, logging):
        self.debugMode = debugMode
        self.logging = logging
        try:
            self.logging.debug("Creating Lists object...")
            self.searchEngines = self.populateSearchEngines()
            self.searchKeywords = self.populateSearchKeywords()
            self.searchExperienceLevels = self.populateSearchExperienceLevels()
            self.searchLocations = self.populateSearchLocations()
            self.avoidTitlesWith = self.populateAvoidTitlesWith()
            self.avoidLocationsWith = self.populateAvoidLocationsWith()
            self.avoidTimeframesWith = self.populateAvoidTimeframesWith()
            self.avoidQualificationsWith = self.populateAvoidQualificationsWith()
            self.possibleQualificationsKeywords = self.populatePossibleQualificationsKeywords()
            self.results = self.populateResults()
            self.logging.debug("Lists objects created!")
        except Exception as error:
            logging.critical("Lists failed to be correctly created.")
            logging.critical(error)
            sys.exit("Exiting Process due to critical error.")


    # Initial Population
    def populateSearchEngines(self):
        tempList = []
        return tempList


    # Initial Population
    def populateSearchKeywords(self):
        if not self.debugMode:
            tempList = ["Software", "Developer", "Web", "QA", "QE", "Quality Assurance", "Quality Engineer", "Engineer", "Automation", "Programmer", "IT", "Security", "Release Engineer", "Build Engineer", "DevOps"]
        else:
            tempList = ["Software"]
        return tempList


    # Initial Population
    def populateSearchExperienceLevels(self):
        if not self.debugMode:
            tempList = ["Intern", "Entry Level"]
        else:
            tempList = ["Entry Level"]
        return tempList


    # Initial Population
    def populateSearchLocations(self):
        tempList = ["Waltham, MA"]
        return tempList


    # Initial Population
    def populatePossibleQualificationsKeywords(self):
        tempList = ["Qualifications", "Requirements", "Required"]
        for x in range(0, len(tempList)):
            tempList.append("{0}:".format(tempList[x]))
            tempList.append("\n{0}:".format(tempList[x]))
            tempList.append(" {0}:".format(tempList[x]))
            tempList.append(" \n{0}:".format(tempList[x]))
        return tempList


    # Initial Population
    def populateAvoidTitlesWith(self):
        tempList = ["Senior", "Sr.", "Lead", "Summer", "Uber", "Accounting", "Electrical", "Sr", "Hardware", "Marketing", "Clerk", "Administrative", "Manager", "Automotive", "Procurement", "Power",
                    "Assistant", "Teller", "Cashier", "Geotechnical", "Recruiter", "Social Media", "Coordinator", "Director", "Head", "Data Entry", "Manufacturing", "Accountant", "Insurance"]
        return tempList


    # Initial Population
    def populateAvoidQualificationsWith(self):
        tempList = ["2+", "3+", "4+", "5+", "6+", "7+", "8+",
                    "2 years", "3 years", "4 years", "5 years", "6 years", "7 years", "8 years",
                    "enrolled", "CAD", "Studying"]
        return tempList


    # Initial Population
    def populateAvoidLocationsWith(self):
        tempList = ["Boston", "Ipswich", "NH", "Andover", "Pepperell", "Worcester", "RI", "Peabody", "Beverly", "Leominster", "ME", "Cambridge", "Quincy", "Dorchester", "Chelmsford", "Acton", "Topsfield",
                    "Milford", "MN", "TX", "Byfield", "Littleton", "Roxbury", "Devens", ]
        return tempList


    # Initial Population
    def populateAvoidTimeframesWith(self):
        tempList = ["4 days", "5 days", "6 days", "7 days", "8 days", "9 days", "10 days", "11 days", "12 days", "13 days", "14 days", "15 days", "16 days", "17 days", "18 days", "19 days", "20 days",
                    "21 days", "22 days", "23 days", "24 days", "25 days", "26 days", "27 days", "28 days", "29 days", "30 days", "30+ days",
                    "4d", "5d", "6d",
                    "week", "weeks",
                    "month", "months"]
        return tempList


    # Initial Population
    def populateResults(self):
        tempList = []
        return tempList

