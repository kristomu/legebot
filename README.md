legebot
=======
Monitoring script for GP/doctor vacancies in the Norwegian "fastlege" system.

Script for overvåkning av ledige plasser i fastlegeordningen

This system uses the new JSON-based helsenorge.no API, i.e. not the old HTML-
based one from NAV.

Functionality and usage
-----------------------

The script regularly checks for vacancies in the GP lists of selected doctors,
notifying the user when new spots are freed.

To configure, change lines 29-43 to taste. The comments should be fairly self-
explanatory. The kommune to kommune number mapping can be found at <https://no.wikipedia.org/wiki/Liste_over_norske_kommunenummer>.

Run using python, i.e. "python legebot.py". Tests can be run using "python parse_doc_2.py"; they should all return True.

Notes
-----

The script exhibits a ratchet effect, which means that if the number of 
vacancies for a particular GP increases and then decreases, the script won't
fire off a new mail unless the number later increases to a new high point. See
line 101 of legebot.py.

The script also doesn't list the current vacancy vector. In the worst case 
scenario, a glitch in helsenorge or on the client side (an undiscovered bug)
could cause the vacancy vector to resolve to all -1s irrespective of the real
number of vacancies. In that case, the script would silently fail to notice any
changes in the vacancy numbers for as long as the glitch persists.
