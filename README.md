# NASCAR_Web_Query
A module to query past and live NASCAR race results

This is my very first github experience, so bear with me.

The Web_Query module pulls race results from nascar.com JSON. 
3 main functions are intended to be used directly from the class: live_race, query, and update_driver_DB

Several complications exist within the JSON that explain the format of the code. Extracting names directly often contain extra characters to indicate a driver as ineligible, rookie, in the playoffs, etc. These characters can be removed using the clean_driver_list method, but it has been found that different JSON databases spell the same drivers name differently. Infuriating, I know. To correct these inconsistancies, the driver ID is used. The driver ID references a database which can be built and updated by the method update_driver_DB. If the user wants to change the spelling of a drivers name, it can be updated in the database and all subsequent times that driver ID appears the spelling in the database will be used.
