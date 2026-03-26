from my_site.integrations.dify_client import DifyClient

sample_resume_text = """
OMURBEK DZHAMALOV
South Korea
Bachelor of Science in Computer Science and Mathematics

EXPERIENCE
Yandex LLC
Data Analyst Intern

- Prioritized 100 optimal power bank deployment locations in Moscow.
- Optimized ATM deployment strategy using CatBoost classifier.
"""

if __name__ == "__main__":
    client = DifyClient()

    raw = client.analyze_resume(sample_resume_text)
    print("RAW RESPONSE:")
    print(raw)

    parsed = client.extract_result_json(raw)
    print("\nPARSED RESULT:")
    print(parsed)