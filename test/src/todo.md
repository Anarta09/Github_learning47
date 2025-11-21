1. Logging and Exception middlewares and configuration 
  + Also create a solid naming convention for better understandability.
  + Flow debugging for better understandability, and read the code.

2. Create a file for constants and perform the necessary steps.

3. `/create-client`: remove redirectUris and manage it in backend and make the `publicClient` true by default, remove both from payload.
"redirectUris": [
    "http://localhost:8000/*"
  ],
  "publicClient": True

4. realm roles are not needed.

5. In the exported `json`, replace the:
  "policies": 
  [
    {
      "name": "Admin Policy",
      "description": "",
      "type": "role",
      "logic": "POSITIVE",
      "decisionStrategy": "UNANIMOUS",
      "config": {
        "fetchRoles": "true",
        "roles": "[{\"id\":\"AnnovaHealthCare/Admin\",\"required\":true}]"
      }
    },
    {
      "name": "TeamLead Caller Policy",
      "description": "",
      "type": "role",
      "logic": "POSITIVE",
      "decisionStrategy": "UNANIMOUS",
      "config": {
        "fetchRoles": "true",
        "roles": "[{\"id\":\"AnnovaHealthCare/Team Lead Caller\",\"required\":false}]"
      }
    }
  ]
client name in roles (AnnovaHealthCare here) with the new client name/id that is created.

6. keycloak user and my DB user should be in sync, so create a syncronization script.

7. Differentiate users (in DB) using the client's name/id in the same realm.

8. Make the get_admin_token() function into a dependency injection.

9. Implement custom Logging and add the logging to all files.

10. Exceptions centralization.

11. Create a standarized name for input and output files of kc client json data.

12. Try to see if update API's can be created for the functionalities that we have.

13. Cache the admin token in `get_admin_token()` and error handle to call api if it expires.

14. If there's an error while fetching resources, policies and scopes, just take the original copy that we have of the json configuration and change the client name and import the configuration.

15. `user_payload_formatter.py`, (user route) make the attribute assignment dynamic rather than hardcoded formatter and assign the values from the first 5 payload.

16. User Attributes should be assigned automatically after user creation, and something in attribute that will uniquely identify it between the multiple client that are available to us.

17. Create the table defined by garvit sir, the schema and important columns are defined in the notebook.