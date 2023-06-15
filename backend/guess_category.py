import openai
import os
from backend.database import get_papers, update_paper
from dotenv import load_dotenv
from tqdm import tqdm
from typing import Tuple

load_dotenv()


def guess_category(title: str) -> str:
    """Guess category with OpenAI."""

    openai.api_key = os.getenv("OPENAI_API_KEY")
    instruction = f"Given a journal article title, predict a subject category. Only provide one category, if you are not sure, just say 'uncertain'."
    prompt = f"Title: {title}"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


def _test_guesses() -> Tuple[dict, dict, dict]:
    """Test the guess_category function."""

    results = {}
    titles = {}
    real_categories = {}

    papers = get_papers(as_dict=True)
    test_papers = [paper for paper in papers if "category" in paper]
    for paper in tqdm(test_papers):
        try:
            real_categories[paper["id"]] = paper["category"]
            results[paper["id"]] = (
                guess_category(paper["title"])
                .removeprefix("Subject category: ")
                .removesuffix(".")
            )
            titles[paper["id"]] = paper["title"]
        except Exception as e:
            print(e)
            print(paper["title"])
            pass

    return results, titles, real_categories
