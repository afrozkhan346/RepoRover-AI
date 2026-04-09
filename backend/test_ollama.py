from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

response = client.chat.completions.create(
    model="deepseek-coder:6.7b",
    messages=[
        {"role": "system", "content": "You are a code expert."},
        {"role": "user", "content": "Explain what this Python code does:\n\ndef add(a, b):\n    return a + b"}
    ]
)

print(response.choices[0].message.content)
