import random

from collections.abc import Mapping
from collections.abc import Sequence
from itertools import cycle
from typing import cast
from typing import Protocol

import numpy as np

from structlog.stdlib import get_logger
from typing_extensions import reveal_type

from ice.apis.openai import openai_complete
from ice.apis.openai import TooLongRequestError
from ice.paper import Paper
from ice.recipe import Recipe
from ice.recipe import recipe
from ice.recipes.best_completion import best_completion
from ice.recipes.consort_flow import baseline_elicit_answer
from ice.recipes.find_best_few_shot_prompt import best_few_shot
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard
from ice.recipes.program_search.nodes.prune.prune import prune
from ice.recipes.program_search.nodes.select.dynamic import SelectionExample
from ice.recipes.program_search.nodes.select.prompts import get_selections
from ice.recipes.program_search.nodes.select.prompts import make_selection_prompt
from ice.recipes.program_search.nodes.select.prompts import render_selection_example
from ice.recipes.program_search.nodes.select.prompts import RenderableSelectionExample
from ice.recipes.program_search.utils.find_examples import matches
from ice.utils import reduce_async
from ice.utils import window_dropping

log = get_logger()


# class Select(Protocol):
#     async def __call__(self, question: str, texts: list[str], examples: list[Example]) -> list[int]:
#         pass

random.seed(314)


def last_token_logprob(openai_response: dict) -> float:
    return openai_response["choices"][0]["logprobs"]["token_logprobs"][-1]


def last_token_top_logprobs(openai_response: dict) -> dict[str, float]:
    return openai_response["choices"][0]["logprobs"]["top_logprobs"][-1]


def logprobs_greater_than_none(
    selections: Mapping[int, float], none_logprob: float, texts: Sequence[str]
) -> Sequence[str]:
    return [text for idx, text in enumerate(texts) if selections[idx] > none_logprob]


async def select(
    question: str,
    texts: Sequence[str],
    existing: Sequence[str],
    examples: list[RenderableSelectionExample] | None = None,
) -> Sequence[str]:
    """Select additional texts by comparing logprobs of indices considered by the model.

    Args:
        question (str): The question to select texts for.
        texts (Sequence[str]): Texts to consider for selection.
        existing (Sequence[str]): Already-selected texts

    Returns:
        Sequence[str]: Newly selected texts (subset of texts)
    """
    if len(texts) > 5:
        log.warning(
            "The OpenAI API only returns the top 5 logprobs, so passing more than 5 candidates means that not all can be fully considered.",
            num_candidates=len(texts),
        )
    prompt = make_selection_prompt(
        question=question,
        existing=existing,
        texts=[t for t in texts if t],
        examples=examples,
    )
    try:
        response = await openai_complete(
            prompt=prompt, max_tokens=0, logprobs=100, echo=True
        )
    except TooLongRequestError:
        if examples and len(examples) >= 2:
            return await select(question, texts, existing, examples[:-1])
        else:
            raise
    choice_logprobs = get_selections(last_token_top_logprobs(response), len(texts))
    return logprobs_greater_than_none(
        choice_logprobs, last_token_logprob(response), texts
    )


async def maybe_binary_prune(question: str, existing: list[str], max_to_keep=8):
    try:
        return await prune(question, existing, max_to_keep=8)
    except TooLongRequestError:
        mid = len(existing) // 2
        h1 = await maybe_binary_prune(question, existing[:mid], max_to_keep=max_to_keep)
        h2 = await maybe_binary_prune(question, existing[mid:], max_to_keep=max_to_keep)
        return await maybe_binary_prune(question, h1 + h2, max_to_keep=max_to_keep)


async def select_reduce(
    question: str,
    texts: Sequence[Sequence[str]],
    do_prune: bool = False,
    examples: list[RenderableSelectionExample] | None = None,
) -> Sequence[str]:
    """Select texts that answer the question by reducing over `select`

    Args:
        question (str): The question to select texts for.
        texts (Sequence[Sequence[str]]): Texts to consider for selection, split into groups to consider at each step.

    Returns:
        Sequence[str]: Selected texts.
    """

    async def select_some(existing: list[str], new_texts: Sequence[str]):
        try:
            new_selections = await select(question, new_texts, existing, examples)
        except TooLongRequestError:
            if do_prune:
                existing = await maybe_binary_prune(
                    question, existing, max_to_keep=8
                )  # TODO: Be smarter about the limit here
                return await select_some(existing, new_texts)
            else:
                log.warning("Skipping because prompt full")
            return existing
        return existing + list(new_selections)

    return await reduce_async(select_some, texts, cast(list[str], []))


async def windowed_select(
    question: str,
    texts: Sequence[str],
    n: int,
    step: int,
    examples: list[RenderableSelectionExample] | None = None,
) -> Sequence[str]:
    """Select texts that answer the question via

    Args:
        question (str): The question to select texts for.
        texts (Sequence[str]): Texts to consider for selection.
        n (int): Number of texts to consider at each step.
        step (int): Overlap between windows. (if n == step, partition the document; if step < n, window with step size).

    Returns:
        Sequence[str]: Selected texts.
    """
    windowed_texts = window_dropping(texts, n, step)
    selections = set(
        await select_reduce(question, windowed_texts, do_prune=True, examples=examples)
    )
    return [t in selections for t in texts]


async def windowed_select_using_elicit_prompt(  # Best recall [use this]
    question: str,
    texts: Sequence[str],
    examples: list[RenderableSelectionExample] | None = None,
    perplexity_threshold: float = 3.0,
) -> Sequence[str]:
    """Select texts that answer the question via

    Args:
        question (str): The question to select texts for.
        texts (Sequence[str]): Texts to consider for selection.
        n (int): Number of texts to consider at each step.
        step (int): Overlap between windows. (if n == step, partition the document; if step < n, window with step size).

    Returns:
        Sequence[str]: Selected texts.
    """

    prompts = [
        baseline_elicit_answer._excerpt_prompt(
            qa_question=question,
            excerpt=text,
            answer_prefix=None,
        )
        for text in texts
    ]

    completion = " " + baseline_elicit_answer.NA_PHRASE

    prompt_perplexities = await best_completion(
        prompts=prompts,
        completion=completion,
    )

    return [
        t for t, p in zip(texts, prompt_perplexities) if p[1] > perplexity_threshold
    ]
    # Lower perplexity means more likely to be "not mentioned in excerpt"


def to_paragraphs(paper: Paper) -> Sequence[str]:
    return [str(p) for p in paper.paragraphs]


def _create_example_prompt(
    example: PaperQaGoldStandard,
    positive: bool,
):
    paragraphs = to_paragraphs(example.paper)
    relevant_paragraphs = example.gold_support
    irrelevant_paragraphs = [p for p in paragraphs if not p in relevant_paragraphs]
    relevant_paragraph, irrelevant_paragraph = random.choice(
        relevant_paragraphs
    ), random.choice(irrelevant_paragraphs)
    prompt = baseline_elicit_answer._excerpt_prompt(
        qa_question=example.question,
        excerpt=relevant_paragraph if positive else irrelevant_paragraph,
        answer_prefix=None,
    )
    completion = (
        example.gold_answer
        if isinstance(example.gold_answer, str)
        else example.gold_answer[0]
    )

    completion = completion.strip() if positive else baseline_elicit_answer.NA_PHRASE

    return prompt + " " + completion


def _create_example_prompts(
    example: PaperQaGoldStandard,
) -> Sequence[str]:
    paragraphs = to_paragraphs(example.paper)
    relevant_paragraphs = example.gold_support
    prompts = [
        baseline_elicit_answer._excerpt_prompt(
            qa_question=example.question,
            excerpt=paragraph,
            answer_prefix=None,
        )
        for paragraph in paragraphs
    ]
    completions = [
        example.gold_answer
        if isinstance(example.gold_answer, str)
        else example.gold_answer[0]
        if paragraph in relevant_paragraphs
        else baseline_elicit_answer.NA_PHRASE
        for paragraph in paragraphs
    ]
    completions = [" " + c.strip() for c in completions]

    return prompts, completions


async def windowed_select_using_elicit_prompt_few_shot(
    question: str,
    texts: Sequence[str],
    examples: list[RenderableSelectionExample] | None = None,
    perplexity_threshold: float = 3.0,
) -> Sequence[str]:
    random.shuffle(examples)

    prompts = sum([_create_example_prompts(e)[0] for e in examples], [])
    completions = sum([_create_example_prompts(e)[1] for e in examples], [])

    few_shot_prompts = await best_few_shot(
        examples_prompts=prompts,
        examples_completions=completions,
        n_shots=2,
        split_string="\n\n",
        prefix="Examples:\n\n",
        max_permutations=6,
        max_test_size=1,
    )

    few_shot_prompt = min(few_shot_prompts, key=lambda p: p[1])[0]

    # gold_support

    """Select texts that answer the question via

    Args:
        question (str): The question to select texts for.
        texts (Sequence[str]): Texts to consider for selection.
        n (int): Number of texts to consider at each step.
        step (int): Overlap between windows. (if n == step, partition the document; if step < n, window with step size).

    Returns:
        Sequence[str]: Selected texts.
    """

    prompts = [
        few_shot_prompt
        + "\n\n"
        + baseline_elicit_answer._excerpt_prompt(
            qa_question=question,
            excerpt=text,
            answer_prefix=None,
        )
        for text in texts
    ]

    completion = " " + baseline_elicit_answer.NA_PHRASE

    prompt_perplexities = await best_completion(
        prompts=prompts,
        completion=completion,
    )

    return [
        t for t, p in zip(texts, prompt_perplexities) if p[1] > perplexity_threshold
    ]
    # Lower perplexity means more likely to be "not mentioned in excerpt"


# Few-shot prompt

SELECTION_PROMPT = """"""


def as_strings(selections: Sequence[bool], texts: Sequence[str]) -> Sequence[str]:
    return [t for t, s in zip(texts, selections) if s]


# Meta-methods
# 1. autoregressive
# 2. tree
# 3. windowed

# Value functions
# Intrinsic (e.g., halter probability of answerable)
# Extrinsic (e.g., ROUGE-L of halter output with answer)


recipe.main(windowed_select)
