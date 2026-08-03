"""Repeated-trial consistency scorer (flip-rate) for the LLM judge."""


def compute_flip_rate(judge_fn, case, n_trials: int = 10) -> float:
    raise NotImplementedError
