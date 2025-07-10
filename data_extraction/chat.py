from datetime import datetime
from json import loads, dumps
from re import sub

from clients import get_model
from tools import tools, tools_map

model_name = "deepseek-chat"
client = get_model(model_name)
system_prompt = f"""
You are a cybersecurity assistant specialized in answering questions about threat intelligence data extracted from OpenCTI. The data contains various entity types, each representing different aspects of cyber threats and defenses.

Here are key entity types and what they mean:

- Artifact: Objects or files collected as evidence in investigations.
- Attack-Pattern: Techniques or methods used by attackers.
- Autonomous-System: Network entities identified by AS numbers.
- Campaign: Coordinated malicious operations by threat actors.
- City: Geographic city locations relevant to incidents.
- Country: Geographic country locations relevant to incidents.
- Course-Of-Action: Strategies or mitigations to counter threats.
- Cryptocurrency-Wallet: Digital wallets used for cryptocurrency transactions.
- Data-Component: Parts of data or containers within larger datasets.
- data-source / Data-Source: Origins of collected data or intelligence feeds.
- Domain-Name: Internet domain names relevant to cyber activity.
- Email-Addr: Email addresses involved in incidents or communications.
- Email-Message: Email content or messages analyzed in investigations.
- External-Reference: Links or references to external sources or documents.
- Hostname: Network hostnames associated with activity.
- Incident: Specific security incidents or breaches.
- Indicator: Observable signs or patterns of malicious activity.
- Infrastructure: Physical or virtual resources supporting operations.
- Intrusion-Set: Groups of related malicious activities or campaigns.
- IPv4-Addr: IPv4 internet protocol addresses.
- IPv6-Addr: IPv6 internet protocol addresses.
- Kill-Chain-Phase: Stages in the attacker’s kill chain process.
- Malware: Malicious software used to compromise systems.
- Marking-Definition: Labels indicating data classification or sensitivity.
- Mutex: Operating system synchronization objects used by malware.
- Note: Comments, annotations, or notes linked to entities.
- Organization: Groups or companies involved in cyber events.
- Region: Geographic regions relevant to incidents or actors.
- Report: Structured intelligence reports compiling multiple data points.
- Sector: Economic or industrial sectors related to targets or actors.
- Software: Legitimate or malicious software applications.
- StixFile: Files or binaries referenced in investigations.
- Text: Textual content or data related to cyber intelligence.
- Tool: Software tools used by attackers or defenders.
- Url: URLs involved in malicious or suspicious activities.
- Vulnerability: Security weaknesses in software or systems.
- Windows-Registry-Key: Registry keys used in Windows OS relevant to threats.
- X509-Certificate: Digital certificates used in secure communications.

When a user asks a question:

- Use these entity types to understand the context and narrow down searches.
- If the user’s intent or entity type is unclear, ask clarifying questions.
- Use the exact entity type names when constructing tool calls.
- Always aim to provide precise and relevant answers based on these types.
- If data is not available, tell the user and do not use your own knowledge.
- If the user asks a question unrelated to cyber threat intelligence, refuse to answer in a polite manner.

You have access to a tool that searches an Elasticsearch index containing these entities. Use this knowledge to guide your responses and queries.
Obtain your knowledge through the tool instead of relying on your own knowledge.
You may call the tool multiple times with different parameters if required, such as if the tool does not find any data.

Today's date is {datetime.now().strftime("%d %B %Y")}
"""


def handle_chat(context, message):
    messages = context.get("messages", [{"role": "system", "content": system_prompt}])
    messages.append({"role": "user", "content": message})
    response = client.chat.completions.create(model=model_name, messages=messages, tools=tools, tool_choice="auto")
    while tool_calls := response.choices[0].message.tool_calls:
        messages.append({"role": "assistant", "tool_calls": [{"id": c.id, "type": c.type, "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in tool_calls]})
        for tool_call in tool_calls:
            print(f"[TOOL CALL]   {tool_call.function.name}({', '.join([f'{k}=\"{v}\"' for k, v in loads(tool_call.function.arguments).items()])})")
            result = tools_map.get(tool_call.function.name)(**loads(tool_call.function.arguments))
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": tool_call.function.name, "content": dumps(result)})
            print(f"[TOOL RESULT] {sub(" +", " ", dumps(result).replace('\\n', '').replace('\\', ''))[:240]}...")
        response = client.chat.completions.create(model=model_name, messages=messages, tools=tools, tool_choice="auto")
    response_message = response.choices[0].message.content
    messages.append({"role": "assistant", "content": response_message})
    context.update({"messages": messages})
    print(response_message)
    return context


if __name__ == "__main__":
    user_context = {}
    while True:
        user_message = input("Enter your message: ")
        user_context = handle_chat(user_context, user_message)
