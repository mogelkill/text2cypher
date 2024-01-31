import logging
import os
import os.path
import random
import sys
import traceback
import uuid
from collections import Counter

import yaml
from tqdm import tqdm

from .args import *
from .generate_graph import GraphGenerator
from .questions import question_forms
from .types import *

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    args = get_args()

    logging.basicConfig()
    logger.setLevel(args.log_level)
    logging.getLogger("gqa").setLevel(args.log_level)

    if args.name is not None:
        name = args.name
    else:
        name = uuid.uuid4()

    total_gqa = args.count * 1000
    if args.just_one:
        total_gqa = 1

    filename = f"./data/gqa-{name}.yaml"
    logger.info(f"Generating {total_gqa} (G,Q,A) tuples into {filename}")

    os.makedirs("./data", exist_ok=True)

    def type_matches(form):
        if args.group is not None:
            if form.group == args.group:
                return True
            else:
                return False

        if args.type_prefix is not None:
            for i in args.type_prefix:
                if form.type_string.startswith(i):
                    return True
            return False

        return True

    with open(filename, "w") as file:
        f_try = Counter()
        f_success = Counter()

        def forms():
            while True:
                for form in question_forms:
                    yield form

        def specs():
            form_gen = forms()
            i = 0
            fail = 0
            with tqdm(total=total_gqa) as pbar:
                while i < total_gqa:
                    try:
                        graph = GraphGenerator(args)
                        graph.generate()
                        g = graph.graph_spec
                        logger.debug("Generated graph")

                        if len(g.nodes) == 0 or len(g.edges) == 0:
                            raise ValueError("Empty graph was generated")

                        j = 0
                        attempt = 0
                        while j < args.questions_per_graph:
                            form = next(form_gen)
                            attempt += 1

                            if type_matches(form):
                                f_try[form.type_string] += 1

                                logger.debug(f"Generating question '{form.english}'")
                                q, a = form.generate(g, args)

                                f_success[form.type_string] += 1
                                i += 1
                                j += 1
                                pbar.update(1)

                                logger.debug(f"Question: '{q}', answer: '{a}'")

                                if args.draw:
                                    graph.draw(os.path.join("data", f"graph-{i}.png"))

                                if args.omit_graph:
                                    yield DocumentSpec(None, q, a).stripped()
                                else:
                                    yield DocumentSpec(g, q, a).stripped()

                            if attempt > len(question_forms) * 3:
                                raise Exception(f"Could not find form that matches {args.type_prefix}")

                    except Exception as ex:
                        logger.debug(f"Exception {ex} whilst trying to generate GQA")

                        # ValueError is deemed to mean "should not generate" and not a bug in the underlying code
                        if not isinstance(ex, ValueError):
                            fail += 1
                            if fail >= max(total_gqa / 3, len(question_forms)):
                                raise Exception(
                                    f"{ex} --- Too many exceptions whilst trying to generate GQA, stopping."
                                )

        yaml.dump_all(specs(), file, explicit_start=True)

        logger.info(f"GQA per question type: {f_success}")

        for i in f_try:
            if i in f_success:
                if f_success[i] < f_try[i]:
                    logger.warn(f"Question form {i} failed to generate {f_try[i] - f_success[i]}/{f_try[i]}")
            else:
                logger.warn(f"Question form {i} totally failed to generate")
