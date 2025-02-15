import { NextResponse } from 'next/server';
import { generateText } from 'ai';
import { createOpenAI as createGroq } from '@ai-sdk/openai';

const groq = createGroq({
  baseURL: 'https://api.groq.com/openai/v1',
  apiKey: process.env.GROQ_API_KEY,
});

export async function POST(req: Request) {
  try {
    const { theme } = await req.json();

    const prompt = `Create a French-English vocabulary list for the theme "${theme}".
    Return ONLY a raw JSON array with NO markdown formatting, NO backticks, and NO explanatory text.

    IMPORTANT FORMATTING RULES:
    1. The "french" field must ONLY contain the base word WITHOUT any articles (no "le", "la", "les", "un", "une")
    2. The "english" field must ONLY contain the base word WITHOUT any articles (no "the", "a", "an")
    3. The "plural" field must contain the actual plural form of the French word (e.g., "pluies", "fruits") WITHOUT the article "les"

    Each object in the array must follow this exact structure:
    {
      "french": "word in French",
      "english": "word in English",
      "gender": "masculine or feminine",
      "parts": {
        "definite_article": "le or la",
        "indefinite_article": "un or une",
        "plural": "plural form of the word"
      }
    }
    
    Examples:
    CORRECT:
    {
    "french": "la pluie",
    "english": "the rain",
    "gender": "feminine",
    "parts": {
      "definite_article": "la",
      "indefinite_article": "une",
      "plural": "les"
      }
    }

    INCORRECT:
    {
    "french": "pluie",
    "english": "rain",
    "gender": "feminine",
    "parts": {
      "definite_article": "la",
      "indefinite_article": "une",
      "plural": "pluies"
      }
    }

    Generate exactly 5 vocabulary items. Return ONLY the JSON array with no additional text or formatting. Check 'Important formatting rules' again before answering.
    `;

    const { text } = await generateText({
      model: groq('gemma2-9b-it'),
      prompt,
    });

    const vocabularyList = JSON.parse(text);

    return NextResponse.json(vocabularyList);
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: 'Failed to generate vocabulary' },
      { status: 500 }
    );
  }
}
