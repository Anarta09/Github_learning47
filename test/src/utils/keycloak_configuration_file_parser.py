import json


def extract_keycloak_data(json_string):
    """
    Parses the Keycloak client configuration JSON to extract resources, scopes, and policies.
    """
    try:
        config = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None, None, None

    # 1. Extract Resources and Scopes
    resources_data = {}
    all_scopes = set()

    if "resources" in config:
        for resource in config["resources"]:
            name = resource.get("name")
            uris = ", ".join(resource.get("uris", []))
            scopes = [
                s.get("name") for s in resource.get("scopes", []) if s.get("name")
            ]

            if name:
                resources_data[name] = {"URIs": uris, "Scopes": scopes}
                all_scopes.update(scopes)

    # 2. Extract Policies
    policies_data = []

    if "policies" in config:
        for policy in config["policies"]:
            policy_info = {
                "Name": policy.get("name"),
                "Type": policy.get("type"),
                "Decision Strategy": policy.get("decisionStrategy"),
            }

            config_str = policy.get("config", {})

            if policy_info["Type"] == "role":
                # Role policies have a 'roles' field that is a JSON string
                roles_str = config_str.get("roles")
                roles = []
                if roles_str:
                    try:
                        # Safely parse the nested JSON string
                        role_list = json.loads(roles_str)
                        roles = [r.get("id") for r in role_list if r.get("id")]
                    except json.JSONDecodeError:
                        roles = ["Error parsing roles config"]

                policy_info["Applies To Roles"] = ", ".join(roles)

            elif policy_info["Type"] == "scope":
                # Scope policies have 'resources', 'scopes', and 'applyPolicies' which are JSON strings
                policy_info["Resources Covered"] = ", ".join(
                    json.loads(config_str.get("resources", "[]"))
                )
                policy_info["Scopes Covered"] = ", ".join(
                    json.loads(config_str.get("scopes", "[]"))
                )
                policy_info["Applies To Policies"] = ", ".join(
                    json.loads(config_str.get("applyPolicies", "[]"))
                )

            policies_data.append(policy_info)

    return resources_data, list(sorted(all_scopes)), policies_data


def format_output(resources, scopes, policies):
    """
    Formats the extracted data for clear console output.
    """
    output = []

    # --- Resources and Scopes ---
    output.append("====================================================")
    output.append("                  KEYCLOAK RESOURCES                  ")
    output.append("====================================================")
    if resources:
        for name, data in resources.items():
            output.append(f"\nResource Name: **{name}**")
            output.append(f"  URIs: {data['URIs'] if data['URIs'] else 'N/A'}")
            output.append(f"  Scopes ({len(data['Scopes'])}):")
            for scope in data["Scopes"]:
                output.append(f"    - {scope}")
    else:
        output.append("No resources found.")

    output.append("\n" + "-" * 50)
    output.append("               ALL UNIQUE SCOPES                    ")
    output.append("-" * 50)
    if scopes:
        for scope in scopes:
            output.append(f"- {scope}")
    else:
        output.append("No unique scopes found.")

    # --- Policies ---
    output.append("\n====================================================")
    output.append("                  KEYCLOAK POLICIES                   ")
    output.append("====================================================")
    if policies:
        for policy in policies:
            output.append(f"\nPolicy Name: **{policy['Name']}**")
            output.append(f"  Type: {policy['Type']}")
            output.append(f"  Decision Strategy: {policy['Decision Strategy']}")
            if policy["Type"] == "role":
                output.append(
                    f"  Applies To Roles: {policy.get('Applies To Roles', 'N/A')}"
                )
            elif policy["Type"] == "scope":
                output.append(
                    f"  Resources Covered: {policy.get('Resources Covered', 'N/A')}"
                )
                output.append(
                    f"  Scopes Covered: {policy.get('Scopes Covered', 'N/A')}"
                )
                output.append(
                    f"  Applies To Policies: {policy.get('Applies To Policies', 'N/A')}"
                )
    else:
        output.append("No policies found.")

    return "\n".join(output)
