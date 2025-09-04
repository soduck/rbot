import openai

openai.api_key = "sk-WsTCuES0rdDz9tjkDqMHKBI0jMghO6jl2bHW1mb0xqT3BlbkFJDP9KKBVnE-YqKs-HU8ek0VmZCr19QFJaiBMjf8EhUA"
try:
    print("送信中...")
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "こんにちは！"}],
        timeout=10
    )
    print("✅ 応答:", res["choices"][0]["message"]["content"])
except Exception as e:
    print("❌ エラー:", e)