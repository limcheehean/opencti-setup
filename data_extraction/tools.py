from agents import search_data
from clients import get_model

model_name = "deepseek-chat"
client = get_model(model_name)

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_data",
            "description": "",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term or keyword to lookup (e.g. 'Emotet', 'APT28', 'log4shell')."
                    },
                    "entity_type": {
                        "type": "array",
                        "description": "",
                        "items": {
                            "type": "string",
                            "enum": [
                              "Artifact",
                              "Attack-Pattern",
                              "Autonomous-System",
                              "Campaign",
                              "City",
                              "Country",
                              "Course-Of-Action",
                              "Cryptocurrency-Wallet",
                              "Data-Component",
                              "data-source",
                              "Data-Source",
                              "Domain-Name",
                              "Email-Addr",
                              "Email-Message",
                              "External-Reference",
                              "Hostname",
                              "Incident",
                              "Indicator",
                              "Infrastructure",
                              "Intrusion-Set",
                              "IPv4-Addr",
                              "IPv6-Addr",
                              "Kill-Chain-Phase",
                              "Malware",
                              "Marking-Definition",
                              "Mutex",
                              "Note",
                              "Organization",
                              "Region",
                              "Report",
                              "Sector",
                              "Software",
                              "StixFile",
                              "Text",
                              "Tool",
                              "Url",
                              "Vulnerability",
                              "Windows-Registry-Key",
                              "X509-Certificate"
                            ]
                        }
                    },
                    "start_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Filter results starting from this ISO date (e.g. '2025-01-01')"
                    },
                    "end_date": {
                        "type": "string",
                        "format": "date",
                        "description": "Filter results up to this ISO date (e.g. '2025-12-31)"
                    }
                },
                "required": ["query", "entity_type"]
            }
        }
    }
]

tools_map = {
    "search_data": lambda **kwargs: search_data(**kwargs)
}
