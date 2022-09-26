# Interactive Composition Explorer 🧊

Decomposition of paper Q&A using humans and language models

## Table of contents

- [Design principles](#design-principles)
- [Running ICE locally](#running-ice-locally)
  - [Requirements](#requirements)
  - [Setup](#setup)
  - [Running ICE on the command line](#running-ice-on-the-command-line)
    - [Human data collection](#human-data-collection)
    - [GPT](#gpt)
  - [Streamlit](#streamlit)
  - [Evaluation](#evaluation)
  - [Evaluate in-app QA results](#evaluate-in-app-qa-results)
- [Development](#development)
  - [Adding new Python dependencies](#adding-new-python-dependencies)
  - [Contributions](#contributions)

## Design principles

- **Recipes** are decompositions of a task into subtasks.

  The meaning of a recipe is: If a human executed these steps and did a good job at each workspace in isolation, the overall answer would be good. This decomposition may be informed by what we think ML can do at this point, but the recipe itself (as an abstraction) doesn’t know about specific agents.

- **Agents** perform atomic subtasks of predefined shapes, like completion, scoring, or classification.

  Agents don't know which recipe is calling them. Agents don’t maintain state between subtasks. Agents generally try to complete all subtasks they're asked to complete (however badly), but some will not have implementations for certain task types.

- The **mode** in which a recipe runs is a global setting that can affect every agent call. For instance, whether to use humans or agents. Recipes can also run with certain `RecipeSettings`, which can map a task type to a specific `agent_name`, which can modify which agent is used for that specfic type of task.

## Running ICE locally

### Prerequisites

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Setup

1. Add required secrets to `.env`. See `.env.example` for a model.

1. Start ICE in its own terminal and leave it running:

   ```sh
   scripts/run-local.sh
   ```

1. Go through [the tutorial](https://primer.ought.org/).

### Advanced command line usage

#### Gold standards

```sh
scripts/run-recipe.sh --mode machine
```

You can run on the iteration gold standards of a specific recipe like this:

```sh
scripts/run-recipe.sh --mode machine -r placebotree -q placebo -g iterate
```

To run over multiple gold standard splits, just provide them separated by spaces:

```sh
scripts/run-recipe.sh --mode machine -r placebotree -q placebo -g iterate validation
```

### Streamlit

These require the streamlit variant of the Docker image:

```sh
STREAMLIT=1 scripts/run-local.sh
```

Run the streamlit apps like this:

```sh
scripts/run-streamlit.sh
```

This opens a multi-page app that lets you select specific scripts.

To add a page, simply create a script in the `streamlits/pages` folder.

### Evaluation

When you run a recipe, ICE will evaluate the results based on the gold standards in `gold_standards/`. You'll see the results on-screen, and they'll be saved as CSVs in `data/evaluation_csvs/`. You can then upload the CSVs to the "Performance dashboard" and "Individual paper eval" tables in the [ICE Airtable](https://airtable.com/app4Fo26j2vGYufCe/tblkFq839UrBrj9P9/viwDkUqYMQtDAl773?blocks=hide).

#### Evaluate in-app QA results

1. Set up both `ice` and `elicit-next` so that they can run on your computer
2. Switch to the `eval` branch of `elicit-next`, or a branch from the eval branch. This branch should contain the QA code and gold standards that you want to evaluate.
3. If the `ice` QA gold standards (`gold_standards/gold_standards.csv`) may not be up-to-date, download [this Airtable view](https://airtable.com/app4Fo26j2vGYufCe/tbl0JN0LFtDi5SrS5/viws799VwN4AXMNii?blocks=hide) (all rows, all fields) as a CSV and save it as `gold_standards/gold_standards.csv`
4. Duplicate the [All rows, all fields](https://airtable.com/app4Fo26j2vGYufCe/tbl0JN0LFtDi5SrS5/viws799VwN4AXMNii?blocks=hide) view in Airtable, then in your duplicated view, filter to exactly the gold standards you'd like to evaluate and download it as a CSV. Save that CSV as `api/eval/gold_standards/gold_standards.csv` in `elicit-next`
5. Make sure `api/eval/papers` in `elicit-next` contains all of the gold standard papers you want to evaluate
6. In `ice`, run `scripts/eval-in-app-qa.sh <path to elicit-next>`. If you have `elicit-next` cloned as a sibling of `ice`, this would be `scripts/eval-in-app-qa.sh $(pwd)/../elicit-next/`.

This will generate the same sort of eval as for ICE recipes.

### Using PyTorch

```sh
TORCH=1 scripts/run-local.sh
```

## Development

### Running tests

Cheap integration tests:

```sh
scripts/run-recipe.sh --mode test
```

Unit tests:

```sh
scripts/run-tests.sh
```

### Adding new Python dependencies

1. Manually add the dependency to `pyproject.toml`
2. Update the lock file and install the changes:

```sh
docker compose exec ice poetry lock --no-update
docker compose exec ice poetry install # if you're running a variant image, pass --extras streamlit or --extras torch
```

The lockfile update step will take about 15 minutes.

You **do not** need to stop, rebuild, and restart the docker containers.

### Upgrading poetry

To upgrade poetry to a new version:

1. In the Dockerfile, temporarily change `pip install -r poetry-requirements.txt` to `pip install poetry==DESIRED_VERSION`
2. Generate a new `poetry-requirements.txt`:
   ```sh
   docker compose -f docker-compose.yml -f docker-compose.build.yml up -d
   docker compose exec ice bash -c 'pip freeze > poetry-requirements.txt'
   ```
3. Revert the Dockerfile changes

### Contributions

Before making a PR, check linting, types, tests, etc:

```sh
scripts/checks.sh
```

## Sharing recipe traces

Reminder: Traces contain source code, so be sure you want to share all the code called by your recipe.

1. Publish the trace to https://github.com/oughtinc/static and wait for the github-pages workflow to finish.
2. Add the trace information to `ui/helpers/recipes.ts`.
