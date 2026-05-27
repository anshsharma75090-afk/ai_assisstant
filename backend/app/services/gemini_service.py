
from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)


class GeminiService:

    @staticmethod
    def generate_response(prompt: str):

        try:

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",

                messages=[
                    {
                        "role": "system",
                        "content": """
You are an advanced AI assistant.

Rules:
- Give detailed and professional answers
- Explain concepts clearly
- For coding questions:
  - provide proper code
  - explain the code
- For web search:
  - summarize results nicely
  - provide sources if requested
- Format answers beautifully
"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.5,
                max_tokens=1200
            )

            return response.choices[0].message.content

        except Exception as e:

            print("GROQ ERROR:", str(e))

            return f"Groq Error: {str(e)}"

    @staticmethod
    def analyze_image(prompt: str, image_data_url: str):
        try:
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "system",
                        "content": """
You are an expert coding and debugging assistant.

When the user sends an error screenshot or UI image:
- Read the visible error carefully
- Identify the likely cause
- Give clear fix steps
- Provide corrected code when useful
- If text is unclear, say what you can infer and ask for the missing detail
- Treat the latest uploaded image as the main image
- Use previous image analysis from chat context only when the user asks to compare, combine, or conclude multiple images
"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_url
                                }
                            }
                        ]
                    }
                ],
                temperature=0.3,
                max_tokens=1200
            )

            return response.choices[0].message.content

        except Exception as e:
            print("GROQ IMAGE ERROR:", str(e))
            return f"Image analysis error: {str(e)}"
